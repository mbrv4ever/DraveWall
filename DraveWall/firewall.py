# -*- coding: utf-8 -*-
"""DraveWall - firewall-motor.

Beheert de ingebouwde Windows Defender Firewall via de officiele COM-API
(HNetCfg.FwPolicy2) - taal-onafhankelijk, geen netsh-tekst parsen. Aan/uit van
profielen en back-up/herstel gaan via 'netsh advfirewall' (commando's zonder
uitvoer-parsing, dus ook taal-onafhankelijk).

Alles wat met COM/Windows te maken heeft wordt 'lui' geimporteerd, zodat dit
bestand op elk systeem importeerbaar blijft (handig om de interface te testen).

Belangrijk: elke regel die DraveWall aanmaakt krijgt de naam 'DraveWall - ...' en
de groep 'DraveWall', zodat we onze eigen regels altijd kunnen terugvinden en in
een keer kunnen verwijderen, zonder systeemregels aan te raken.
"""
import os
import sys
import subprocess

VOORVOEGSEL = "DraveWall - "
GROEP = "DraveWall"

# COM-constanten (NET_FW_*)
PROF_DOMEIN = 1
PROF_PRIVE = 2
PROF_OPENBAAR = 4
PROF_ALLE = 0x7FFFFFFF

RICHTING_IN = 1
RICHTING_UIT = 2

ACTIE_BLOKKEREN = 0
ACTIE_TOESTAAN = 1

PROTO_TCP = 6
PROTO_UDP = 17
PROTO_ALLE = 256


class FirewallFout(Exception):
    pass


def op_windows():
    return os.name == "nt"


def _policy():
    """Geef het INetFwPolicy2-COM-object (of werp FirewallFout)."""
    if not op_windows():
        raise FirewallFout("alleen-windows")
    try:
        import win32com.client
        return win32com.client.Dispatch("HNetCfg.FwPolicy2")
    except Exception as e:
        raise FirewallFout("COM niet beschikbaar: %s" % e)


def beschikbaar():
    """True als we de firewall echt kunnen aansturen (Windows + COM werkt)."""
    try:
        _policy()
        return True
    except Exception:
        return False


def is_beheerder():
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _no_window():
    if op_windows():
        return 0x08000000  # CREATE_NO_WINDOW
    return 0


def _netsh(args):
    cmd = ["netsh", "advfirewall"] + args
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           creationflags=_no_window())
    except FileNotFoundError:
        raise FirewallFout("netsh niet gevonden")
    if r.returncode != 0:
        raise FirewallFout((r.stderr or r.stdout or "netsh-fout").strip())
    return r.stdout


# ---------------------------------------------------------------------------
# Status & profielen
# ---------------------------------------------------------------------------
def profiel_status():
    """Geef {'domein': bool, 'prive': bool, 'openbaar': bool} - firewall aan?"""
    p = _policy()
    return {
        "domein": bool(p.FirewallEnabled(PROF_DOMEIN)),
        "prive": bool(p.FirewallEnabled(PROF_PRIVE)),
        "openbaar": bool(p.FirewallEnabled(PROF_OPENBAAR)),
    }


def zet_profiel(profiel, aan):
    """profiel in {'domein','prive','openbaar'}; aan=True/False (via netsh)."""
    sleutel = {"domein": "domainprofile", "prive": "privateprofile",
               "openbaar": "publicprofile"}.get(profiel)
    if not sleutel:
        raise FirewallFout("onbekend profiel: %s" % profiel)
    _netsh(["set", sleutel, "state", "on" if aan else "off"])


# ---------------------------------------------------------------------------
# Regels lezen
# ---------------------------------------------------------------------------
def _regel_naar_dict(r):
    def veilig(fn, standaard=None):
        try:
            return fn()
        except Exception:
            return standaard
    return {
        "naam": veilig(lambda: r.Name, "") or "",
        "programma": veilig(lambda: r.ApplicationName, "") or "",
        "richting": "in" if veilig(lambda: r.Direction, RICHTING_IN) == RICHTING_IN else "uit",
        "actie": "toestaan" if veilig(lambda: r.Action, ACTIE_TOESTAAN) == ACTIE_TOESTAAN else "blokkeren",
        "aan": bool(veilig(lambda: r.Enabled, False)),
        "protocol": veilig(lambda: int(r.Protocol), PROTO_ALLE),
        "lokale_poorten": veilig(lambda: r.LocalPorts, "") or "",
        "externe_poorten": veilig(lambda: r.RemotePorts, "") or "",
        "profielen": veilig(lambda: int(r.Profiles), PROF_ALLE),
        "groep": veilig(lambda: r.Grouping, "") or "",
        "van_drave": (veilig(lambda: r.Grouping, "") == GROEP) or
                     str(veilig(lambda: r.Name, "") or "").startswith(VOORVOEGSEL),
    }


def lijst_regels(zoek="", alleen_drave=False):
    p = _policy()
    uit = []
    for r in p.Rules:
        d = _regel_naar_dict(r)
        if alleen_drave and not d["van_drave"]:
            continue
        if zoek:
            z = zoek.lower()
            if z not in d["naam"].lower() and z not in d["programma"].lower():
                continue
        uit.append(d)
    uit.sort(key=lambda d: (not d["van_drave"], d["naam"].lower()))
    return uit


# ---------------------------------------------------------------------------
# Regels maken / wijzigen / verwijderen
# ---------------------------------------------------------------------------
def _maak_regel_object(naam, programma, actie, richting, profielen,
                       protocol=PROTO_ALLE, lokale_poorten="", externe_poorten="",
                       beschrijving=""):
    import win32com.client
    r = win32com.client.Dispatch("HNetCfg.FWRule")
    r.Name = naam
    if programma:
        r.ApplicationName = programma
    r.Action = actie
    r.Direction = richting
    r.Enabled = True
    r.Profiles = profielen
    r.Grouping = GROEP
    if beschrijving:
        r.Description = beschrijving
    # Poorten kunnen alleen bij TCP/UDP
    if protocol in (PROTO_TCP, PROTO_UDP):
        r.Protocol = protocol
        if lokale_poorten:
            r.LocalPorts = lokale_poorten
        if externe_poorten:
            r.RemotePorts = externe_poorten
    else:
        r.Protocol = PROTO_ALLE
    return r


def maak_regel(naam, programma="", actie=ACTIE_BLOKKEREN, richting=RICHTING_UIT,
               profielen=PROF_ALLE, protocol=PROTO_ALLE, lokale_poorten="",
               externe_poorten="", beschrijving=""):
    """Maak een regel. De naam krijgt automatisch het DraveWall-voorvoegsel."""
    p = _policy()
    if not naam.startswith(VOORVOEGSEL):
        naam = VOORVOEGSEL + naam
    r = _maak_regel_object(naam, programma, actie, richting, profielen,
                           protocol, lokale_poorten, externe_poorten,
                           beschrijving or "Aangemaakt door DraveWall")
    p.Rules.Add(r)
    return naam


def blokkeer_programma(programma, label="", richtingen=("uit",), profielen=PROF_ALLE):
    """Blokkeer een .exe. richtingen: subset van ('uit','in')."""
    return _programma_regels(programma, label, richtingen, profielen, ACTIE_BLOKKEREN)


def sta_programma_toe(programma, label="", richtingen=("uit",), profielen=PROF_ALLE):
    return _programma_regels(programma, label, richtingen, profielen, ACTIE_TOESTAAN)


def _programma_regels(programma, label, richtingen, profielen, actie):
    naam_basis = label or os.path.splitext(os.path.basename(programma))[0]
    woord = "blokkeren" if actie == ACTIE_BLOKKEREN else "toestaan"
    gemaakt = []
    for r in richtingen:
        richting = RICHTING_IN if r == "in" else RICHTING_UIT
        naam = "%s%s (%s, %s)" % (VOORVOEGSEL, naam_basis, woord,
                                  "inkomend" if r == "in" else "uitgaand")
        maak_regel(naam, programma=programma, actie=actie, richting=richting,
                   profielen=profielen)
        gemaakt.append(naam)
    return gemaakt


def zet_regel_aan(naam, aan):
    p = _policy()
    try:
        regel = p.Rules.Item(naam)
    except Exception:
        raise FirewallFout("regel niet gevonden: %s" % naam)
    regel.Enabled = bool(aan)


def verwijder_regel(naam):
    p = _policy()
    p.Rules.Remove(naam)


def verwijder_drave_regels():
    """Verwijder alle regels die DraveWall heeft gemaakt. Geeft het aantal terug."""
    p = _policy()
    namen = []
    for r in p.Rules:
        d = _regel_naar_dict(r)
        if d["van_drave"] and d["naam"] not in namen:
            namen.append(d["naam"])
    for naam in namen:
        try:
            p.Rules.Remove(naam)
        except Exception:
            pass
    return len(namen)


# ---------------------------------------------------------------------------
# Back-up / herstel (via netsh; geen uitvoer-parsing)
# ---------------------------------------------------------------------------
def exporteer(pad):
    _netsh(["export", pad])


def importeer(pad):
    _netsh(["import", pad])


# ---------------------------------------------------------------------------
def herstart_als_beheerder(script_pad=None):
    """Herstart de app met UAC-verhoging. Geeft True als de poging is gestart."""
    if not op_windows():
        return False
    try:
        import ctypes
        if getattr(sys, "frozen", False):
            doel = sys.executable
            params = subprocess.list2cmdline(sys.argv[1:])
        else:
            doel = sys.executable
            params = subprocess.list2cmdline([script_pad or sys.argv[0]] + sys.argv[1:])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", doel, params, None, 1)
        return True
    except Exception:
        return False
