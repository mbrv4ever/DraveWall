# -*- coding: utf-8 -*-
"""DraveWall - hosts-bestand-motor.

Lezen en (met beheerdersrechten) schrijven van het Windows hosts-bestand
(%SystemRoot%\\System32\\drivers\\etc\\hosts). Plus: een domein blokkeren door
het naar 0.0.0.0 te wijzen, en de DNS-cache legen. Puur functioneel, los testbaar
(het pad is voor tests te overschrijven met zet_pad).
"""
import os
import shutil
import datetime

MERK = "# DraveWall"
_OVERRIDE_PAD = None


def standaard_pad():
    if os.name == "nt":
        return os.path.join(os.environ.get("SystemRoot", r"C:\Windows"),
                            "System32", "drivers", "etc", "hosts")
    return "/etc/hosts"


def zet_pad(pad):
    """Alleen voor tests: overschrijf het hosts-pad."""
    global _OVERRIDE_PAD
    _OVERRIDE_PAD = pad


def pad():
    return _OVERRIDE_PAD or standaard_pad()


def lees():
    try:
        with open(pad(), "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def schrijf(tekst, backup_map=None):
    """Schrijf het hosts-bestand. Maakt eerst (optioneel) een back-up. Vereist
    beheerdersrechten; bij gebrek daaraan komt er een PermissionError omhoog."""
    doel = pad()
    if backup_map:
        try:
            os.makedirs(backup_map, exist_ok=True)
            naam = "hosts-backup-%s.txt" % datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            shutil.copyfile(doel, os.path.join(backup_map, naam))
        except OSError:
            pass
    # Windows hosts gebruikt CRLF; normaliseer
    if os.name == "nt":
        tekst = tekst.replace("\r\n", "\n").replace("\n", "\r\n")
    map_ = os.path.dirname(doel) or "."
    tmp = os.path.join(map_, "hosts.dravewall.tmp")
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(tekst)
    os.replace(tmp, doel)


def _bestaande_hosts(tekst):
    namen = set()
    for regel in tekst.splitlines():
        s = regel.strip()
        if not s or s.startswith("#"):
            continue
        delen = s.split()
        for h in delen[1:]:
            namen.add(h.lower())
    return namen


def _schoon_domein(domein):
    d = (domein or "").strip().lower()
    for pre in ("https://", "http://"):
        if d.startswith(pre):
            d = d[len(pre):]
    d = d.split("/")[0].strip()
    return d


def blokkeer_domein(tekst, domein, ip="0.0.0.0"):
    """Voeg blokkeerregels toe voor domein en www.domein (als ze ontbreken).
    Geeft de nieuwe tekst terug."""
    domein = _schoon_domein(domein)
    if not domein:
        return tekst
    bestaand = _bestaande_hosts(tekst)
    toe = []
    for host in (domein, "www." + domein):
        if host not in bestaand:
            toe.append("%s %s %s" % (ip, host, MERK))
    if toe:
        if tekst and not tekst.endswith("\n"):
            tekst += "\n"
        tekst += "\n".join(toe) + "\n"
    return tekst


def deblokkeer_domein(tekst, domein):
    """Verwijder regels die dit domein (of www.domein) blokkeren."""
    domein = _schoon_domein(domein)
    doelen = {domein, "www." + domein}
    nieuw = []
    for regel in tekst.splitlines():
        s = regel.strip()
        if s and not s.startswith("#"):
            delen = s.split()
            if len(delen) >= 2 and any(h.lower() in doelen for h in delen[1:]):
                continue
        nieuw.append(regel)
    return "\n".join(nieuw) + ("\n" if tekst.endswith("\n") else "")


def flush_dns():
    if os.name == "nt":
        import subprocess
        try:
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True,
                           creationflags=0x08000000)
        except Exception:
            pass
