# -*- coding: utf-8 -*-
"""DraveWall - vriendelijke voorkant voor de Windows Defender Firewall (Dravenlock).

Aan/uit per profiel, programma's blokkeren/toestaan, regels bekijken/beheren,
handmatige regels, en back-up/herstel. Wijzigen vereist beheerdersrechten (UAC).
"""
import os
import sys
import json
import traceback

import firewall as FW
import hostsbestand as HB

APP_NAAM = "DraveWall"
APP_VERSIE = "0.2.2"
DONATIE_URL = "https://paypal.me/roger076"
CONTACT = "service@dravenlock.nl"

if getattr(sys, "frozen", False):
    BASIS = os.path.dirname(sys.executable)
else:
    BASIS = os.path.dirname(os.path.abspath(__file__))
FOUT_BESTAND = os.path.join(BASIS, "app-fout.txt")
DATA_MAP = os.path.join(BASIS, "DraveWall-data")
CONFIG_BESTAND = os.path.join(DATA_MAP, "instellingen.json")

BG = "#0e0e11"; PANEL = "#16161b"; PANEL2 = "#1c1c22"; TEXT = "#d4d4d4"
MUTED = "#8a8a94"; ACCENT = "#6fa3d6"; LINE = "#23232b"; WARN = "#d68a6f"
GOED = "#7fb069"


def zorg_voor_mappen():
    try:
        os.makedirs(DATA_MAP, exist_ok=True)
    except OSError:
        pass


def _excepthook(soort, waarde, tb):
    try:
        with open(FOUT_BESTAND, "w", encoding="utf-8") as f:
            f.write("DraveWall startfout\n\n")
            f.write("".join(traceback.format_exception(soort, waarde, tb)))
    except Exception:
        pass
    sys.__excepthook__(soort, waarde, tb)


sys.excepthook = _excepthook

STANDAARD_CONFIG = {"taal": "auto", "toon_welkom": True, "laatste_map": "",
                    "backup_map": ""}


def laad_config():
    cfg = dict(STANDAARD_CONFIG)
    try:
        with open(CONFIG_BESTAND, encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict):
            cfg.update(d)
    except Exception:
        pass
    return cfg


def bewaar_config(cfg):
    try:
        tmp = CONFIG_BESTAND + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        os.replace(tmp, CONFIG_BESTAND)
    except Exception:
        pass


def log_fout(actie, fout):
    try:
        zorg_voor_mappen()
        import datetime
        with open(os.path.join(DATA_MAP, "fout-log.txt"), "a", encoding="utf-8") as f:
            f.write("\n=== %s | %s ===\n" %
                    (datetime.datetime.now().isoformat(timespec="seconds"), actie))
            f.write("".join(traceback.format_exception(type(fout), fout, fout.__traceback__)))
    except Exception:
        pass


# ---------------------------------------------------------------------------
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QMessageBox, QDialog, QFormLayout, QLineEdit, QComboBox,
    QStatusBar, QFileDialog, QTabWidget, QTextBrowser, QCheckBox, QTableWidget,
    QTableWidgetItem, QAbstractItemView, QHeaderView, QFrame, QPlainTextEdit,
    QInputDialog,
)
from PyQt6.QtGui import QAction, QIcon, QDesktopServices, QGuiApplication, QPixmap
from PyQt6.QtCore import Qt, QUrl, QTimer


def _bundel(naam):
    return os.path.join(getattr(sys, "_MEIPASS", BASIS), naam)


def app_icoon():
    for naam in ("app.ico", "logo.png"):
        p = _bundel(naam)
        if os.path.isfile(p):
            ic = QIcon(p)
            if not ic.isNull():
                return ic
    return QIcon()


def STIJL():
    return """
    QWidget { background: %(bg)s; color: %(text)s; font-size: 15px; }
    QLabel#titel { font-size: 24px; font-weight: bold; }
    QLabel#sub { color: %(muted)s; }
    QLabel#waarschuwing { color: %(warn)s; }
    QLabel#ok { color: %(goed)s; }
    QLineEdit, QComboBox {
        background: %(panel2)s; color: %(text)s; border: 1px solid %(line)s;
        border-radius: 8px; padding: 7px; }
    QLineEdit:focus, QComboBox:focus { border: 1px solid %(accent)s; }
    QTableWidget { background: %(panel)s; color: %(text)s; border: 1px solid %(line)s;
        border-radius: 8px; gridline-color: %(line)s; }
    QTableWidget::item:selected { background: %(accent)s; color: #0b0b0e; }
    QHeaderView::section { background: %(panel2)s; color: %(text)s; border: none;
        border-bottom: 1px solid %(line)s; padding: 6px; }
    QPushButton { background: %(panel2)s; color: %(text)s; border: 1px solid %(line)s;
        border-radius: 9px; padding: 8px 12px; }
    QPushButton:hover { border: 1px solid %(accent)s; }
    QPushButton#primair { background: %(accent)s; color: #0b0b0e; border: none; font-weight: bold; }
    QPushButton#primair:hover { background: #84b4e0; }
    QPushButton#gevaar { border: 1px solid %(warn)s; color: %(warn)s; }
    QPushButton#gevaar:hover { background: %(warn)s; color: #0b0b0e; }
    QTabWidget::pane { border: 1px solid %(line)s; border-radius: 8px; }
    QTabBar::tab { background: %(panel)s; color: %(muted)s; padding: 9px 16px;
        border: 1px solid %(line)s; border-bottom: none;
        border-top-left-radius: 8px; border-top-right-radius: 8px; }
    QTabBar::tab:selected { background: %(panel2)s; color: %(text)s; }
    QMenuBar { background: %(bg)s; color: %(text)s; }
    QMenuBar::item:selected { background: %(panel2)s; }
    QMenu { background: %(panel)s; color: %(text)s; border: 1px solid %(line)s; }
    QMenu::item:selected { background: %(accent)s; color: #0b0b0e; }
    QStatusBar { background: %(bg)s; color: %(muted)s; }
    QCheckBox { color: %(text)s; }
    QFrame#banner { background: %(panel2)s; border: 1px solid %(warn)s; border-radius: 8px; }
    """ % {"bg": BG, "panel": PANEL, "panel2": PANEL2, "text": TEXT, "muted": MUTED,
           "accent": ACCENT, "line": LINE, "warn": WARN, "goed": GOED}


def centreer(d, ouder=None):
    try:
        s = (ouder.screen() if ouder else None) or QGuiApplication.primaryScreen()
        g = s.availableGeometry()
        d.move(g.center().x() - d.width() // 2, g.center().y() - d.height() // 2)
    except Exception:
        pass


def taal_detecteren():
    try:
        from PyQt6.QtCore import QLocale
        return "nl" if QLocale.system().name().lower().startswith("nl") else "en"
    except Exception:
        return "en"


TEKST = {
    "nl": {
        "ondertitel": "Voorkant voor de Windows-firewall + hosts-bestand - blokkeer programma's en domeinen",
        "menu_bestand": "Bestand", "menu_help": "Help", "instellingen": "Instellingen",
        "afsluiten": "Afsluiten", "snelgids": "Snelgids", "over": "Over DraveWall",
        "donatie": "Donatie", "sluiten": "Sluiten", "opslaan": "Opslaan",
        "annuleren": "Annuleren", "bladeren": "Bladeren...",
        "tab_welkom": "Welkom", "tab_status": "Status", "tab_prog": "Programma's",
        "tab_regels": "Regels",
        "tab_hosts": "Hosts",
        "welkom_intro": "DraveWall is een vriendelijke voorkant voor de Windows-firewall. "
                        "Blokkeer of sta programma's toe, beheer regels en zet de firewall "
                        "per profiel aan of uit. Wijzigen vereist beheerdersrechten.",
        "welkom_prog": "Programma blokkeren/toestaan", "welkom_regels": "Regels bekijken",
        "welkom_toon": "Dit welkomscherm tonen bij opstarten",
        # status
        "beheerder_ok": "Je draait als beheerder - wijzigen kan.",
        "beheerder_niet": "Let op: niet als beheerder gestart. Bekijken kan, maar wijzigen "
                          "lukt pas als beheerder.",
        "herstart_admin": "Herstart als beheerder",
        "welkom_admin_vraag": "Je draait niet als beheerder. Firewall-regels en het "
                              "hosts-bestand wijzigen lukt alleen als beheerder.",
        "firewall_profielen": "Firewall per profiel",
        "prof_domein": "Domein", "prof_prive": "Prive", "prof_openbaar": "Openbaar",
        "aan": "Aan", "uit": "Uit", "vernieuwen": "Vernieuwen",
        "veiligheid": "Veiligheid", "backup": "Back-up maken...",
        "herstel": "Herstellen...", "backup_klaar": "Back-up opgeslagen.",
        "herstel_vraag": "Hiermee wordt de hele firewall-configuratie teruggezet uit het "
                         "bestand. Doorgaan?", "herstel_klaar": "Firewall hersteld.",
        "fw_uit_vraag": "De firewall uitzetten kan je pc minder veilig maken. Toch doen?",
        # programma's
        "prog_kies": "Programma (.exe)", "prog_label": "Naam (optioneel)",
        "prog_richting": "Richting", "r_uit": "Uitgaand", "r_in": "Inkomend",
        "r_beide": "Beide", "prog_prof": "Voor profielen",
        "p_alle": "Alle", "blokkeer": "Blokkeren", "toestaan": "Toestaan",
        "prog_geen": "Kies eerst een programma (.exe).",
        "blok_klaar": "Geblokkeerd: {naam}", "toe_klaar": "Toegestaan: {naam}",
        "blok_vraag": "Het programma '{naam}' blokkeren voor internet?",
        "toe_vraag": "Het programma '{naam}' toestaan?",
        # regels
        "zoek": "Zoeken...", "alleen_drave": "Alleen DraveWall-regels",
        "k_aan": "Aan", "k_naam": "Naam", "k_prog": "Programma", "k_richting": "Richting",
        "k_actie": "Actie", "k_prof": "Profielen",
        "in_uit": "In-/uitschakelen", "verwijder": "Verwijderen",
        "nieuwe": "Nieuwe regel...", "verwijder_drave": "Verwijder alle DraveWall-regels",
        "kies_regel": "Selecteer eerst een regel.",
        "verwijder_vraag": "Regel '{naam}' verwijderen?",
        "verwijder_drave_vraag": "Alle regels die DraveWall heeft gemaakt verwijderen? "
                                 "Systeemregels blijven ongemoeid.",
        "verwijder_drave_klaar": "{n} DraveWall-regels verwijderd.",
        "regels_n": "{n} regels", "richting_in": "inkomend", "richting_uit": "uitgaand",
        "actie_toestaan": "toestaan", "actie_blokkeren": "blokkeren",
        # nieuwe-regel-dialoog
        "nr_titel": "Nieuwe regel", "nr_naam": "Naam", "nr_prog": "Programma (optioneel)",
        "nr_actie": "Actie", "nr_richting": "Richting", "nr_proto": "Protocol",
        "nr_lokaal": "Lokale poorten", "nr_extern": "Externe poorten",
        "nr_prof": "Profielen", "nr_naam_leeg": "Geef de regel een naam.",
        "proto_alle": "Alle", "maken": "Maken",
        # algemeen
        "niet_windows": "DraveWall werkt alleen op Windows (firewall-functies zijn daar "
                        "beschikbaar).", "geen_com": "Kon de Windows-firewall niet "
                        "benaderen. Start opnieuw, eventueel als beheerder.",
        "fout": "Er ging iets mis: {fout}",
        "fout_log": "Details staan in DraveWall-data\\fout-log.txt.",
        "rechten_fout": "Dit lukt alleen als beheerder. Klik 'Herstart als beheerder'.",
        "inst_taal": "Taal", "inst_taal_auto": "Automatisch (computertaal)",
        "herstart_taal": "Herstart de app om de taal volledig toe te passen.",
        "hosts_uitleg": "Bewerk het Windows hosts-bestand. Blokkeer een domein door het "
                        "naar 0.0.0.0 te wijzen. Opslaan vereist beheerdersrechten; er wordt "
                        "automatisch een back-up gemaakt in DraveWall-data en de DNS-cache "
                        "geleegd.",
        "hosts_herladen": "Herladen", "hosts_blokkeer": "Domein blokkeren...",
        "hosts_deblok": "Domein deblokkeren...", "hosts_opslaan": "Opslaan",
        "hosts_blokkeer_vraag": "Welk domein? (bijv. voorbeeld.nl)",
        "hosts_blok_toegevoegd": "Toegevoegd: {domein}. Klik Opslaan om door te voeren.",
        "hosts_deblok_klaar": "Verwijderd: {domein}. Klik Opslaan om door te voeren.",
        "hosts_opslaan_vraag": "Het hosts-bestand opslaan? Er wordt eerst een back-up gemaakt.",
        "hosts_opgeslagen": "Hosts-bestand opgeslagen en DNS-cache geleegd.",
        "hosts_lees_fout": "Kon het hosts-bestand niet lezen.",
        "hosts_admin_nodig": "Opslaan van het hosts-bestand kan alleen als beheerder. Klik "
                             "'Herstart als beheerder' op het tabblad Status.",
        "over_tekst": "DraveWall v{versie}\n\nVoorkant voor de Windows Defender Firewall. "
                      "Lokaal, geen cloud.\n\nContact: {contact}\nDonatie: {donatie}",
    },
    "en": {
        "ondertitel": "Front-end for the Windows firewall + hosts file - block programs and domains",
        "menu_bestand": "File", "menu_help": "Help", "instellingen": "Settings",
        "afsluiten": "Quit", "snelgids": "Quick guide", "over": "About DraveWall",
        "donatie": "Donate", "sluiten": "Close", "opslaan": "Save",
        "annuleren": "Cancel", "bladeren": "Browse...",
        "tab_welkom": "Welcome", "tab_status": "Status", "tab_prog": "Programs",
        "tab_regels": "Rules",
        "tab_hosts": "Hosts",
        "welkom_intro": "DraveWall is a friendly front-end for the Windows firewall. Block "
                        "or allow programs, manage rules and turn the firewall on or off per "
                        "profile. Changing requires administrator rights.",
        "welkom_prog": "Block/allow a program", "welkom_regels": "View rules",
        "welkom_toon": "Show this welcome screen at startup",
        "beheerder_ok": "Running as administrator - you can make changes.",
        "beheerder_niet": "Note: not started as administrator. Viewing works, but changing "
                          "needs administrator rights.",
        "herstart_admin": "Restart as administrator",
        "welkom_admin_vraag": "You are not running as administrator. Changing firewall "
                              "rules and the hosts file only works as administrator.",
        "firewall_profielen": "Firewall per profile",
        "prof_domein": "Domain", "prof_prive": "Private", "prof_openbaar": "Public",
        "aan": "On", "uit": "Off", "vernieuwen": "Refresh",
        "veiligheid": "Safety", "backup": "Make backup...",
        "herstel": "Restore...", "backup_klaar": "Backup saved.",
        "herstel_vraag": "This restores the entire firewall configuration from the file. "
                         "Continue?", "herstel_klaar": "Firewall restored.",
        "fw_uit_vraag": "Turning off the firewall can make your pc less safe. Do it anyway?",
        "prog_kies": "Program (.exe)", "prog_label": "Name (optional)",
        "prog_richting": "Direction", "r_uit": "Outbound", "r_in": "Inbound",
        "r_beide": "Both", "prog_prof": "For profiles",
        "p_alle": "All", "blokkeer": "Block", "toestaan": "Allow",
        "prog_geen": "Choose a program (.exe) first.",
        "blok_klaar": "Blocked: {naam}", "toe_klaar": "Allowed: {naam}",
        "blok_vraag": "Block program '{naam}' from the internet?",
        "toe_vraag": "Allow program '{naam}'?",
        "zoek": "Search...", "alleen_drave": "DraveWall rules only",
        "k_aan": "On", "k_naam": "Name", "k_prog": "Program", "k_richting": "Direction",
        "k_actie": "Action", "k_prof": "Profiles",
        "in_uit": "Enable/disable", "verwijder": "Delete",
        "nieuwe": "New rule...", "verwijder_drave": "Delete all DraveWall rules",
        "kies_regel": "Select a rule first.",
        "verwijder_vraag": "Delete rule '{naam}'?",
        "verwijder_drave_vraag": "Delete all rules created by DraveWall? System rules are "
                                 "left untouched.",
        "verwijder_drave_klaar": "{n} DraveWall rules deleted.",
        "regels_n": "{n} rules", "richting_in": "inbound", "richting_uit": "outbound",
        "actie_toestaan": "allow", "actie_blokkeren": "block",
        "nr_titel": "New rule", "nr_naam": "Name", "nr_prog": "Program (optional)",
        "nr_actie": "Action", "nr_richting": "Direction", "nr_proto": "Protocol",
        "nr_lokaal": "Local ports", "nr_extern": "Remote ports",
        "nr_prof": "Profiles", "nr_naam_leeg": "Give the rule a name.",
        "proto_alle": "All", "maken": "Create",
        "niet_windows": "DraveWall only works on Windows (firewall features live there).",
        "geen_com": "Could not access the Windows firewall. Restart, possibly as admin.",
        "fout": "Something went wrong: {fout}",
        "fout_log": "Details are in DraveWall-data\\fout-log.txt.",
        "rechten_fout": "This only works as administrator. Click 'Restart as administrator'.",
        "inst_taal": "Language", "inst_taal_auto": "Automatic (system language)",
        "herstart_taal": "Restart the app to fully apply the language.",
        "hosts_uitleg": "Edit the Windows hosts file. Block a domain by pointing it to "
                        "0.0.0.0. Saving requires administrator rights; a backup is made "
                        "automatically in DraveWall-data and the DNS cache is flushed.",
        "hosts_herladen": "Reload", "hosts_blokkeer": "Block domain...",
        "hosts_deblok": "Unblock domain...", "hosts_opslaan": "Save",
        "hosts_blokkeer_vraag": "Which domain? (e.g. example.com)",
        "hosts_blok_toegevoegd": "Added: {domein}. Click Save to apply.",
        "hosts_deblok_klaar": "Removed: {domein}. Click Save to apply.",
        "hosts_opslaan_vraag": "Save the hosts file? A backup is made first.",
        "hosts_opgeslagen": "Hosts file saved and DNS cache flushed.",
        "hosts_lees_fout": "Could not read the hosts file.",
        "hosts_admin_nodig": "Saving the hosts file only works as administrator. Click "
                             "'Restart as administrator' on the Status tab.",
        "over_tekst": "DraveWall v{versie}\n\nFront-end for the Windows Defender Firewall. "
                      "Local, no cloud.\n\nContact: {contact}\nDonate: {donatie}",
    },
}
_TAAL = "nl"


def T(s):
    return TEKST.get(_TAAL, TEKST["nl"]).get(s, s)


def _toon_fout(ouder, e, actie="actie"):
    log_fout(actie, e)
    low = str(e).lower()
    if isinstance(e, FW.FirewallFout) and "alleen-windows" in low:
        QMessageBox.warning(ouder, APP_NAAM, T("niet_windows"))
    elif "denied" in low or "geweigerd" in low or "0x80070005" in low or "toegang" in low:
        QMessageBox.warning(ouder, APP_NAAM, T("rechten_fout"))
    elif "com niet beschikbaar" in low:
        QMessageBox.warning(ouder, APP_NAAM, T("geen_com"))
    else:
        QMessageBox.warning(ouder, APP_NAAM,
                            T("fout").format(fout=e) + "\n\n" + T("fout_log"))


# ---------------------------------------------------------------------------
class InstellingenDialoog(QDialog):
    def __init__(self, ouder, cfg):
        super().__init__(ouder)
        self.cfg = cfg
        self.setWindowTitle(T("instellingen")); self.setWindowIcon(app_icoon())
        self.resize(460, 150); self.setStyleSheet(STIJL())
        lay = QVBoxLayout(self); form = QFormLayout()
        self.taal = QComboBox()
        self.taal.addItem(T("inst_taal_auto"), "auto")
        self.taal.addItem("Nederlands", "nl"); self.taal.addItem("English", "en")
        self.taal.setCurrentIndex(max(0, self.taal.findData(cfg.get("taal", "auto"))))
        form.addRow(T("inst_taal"), self.taal)
        lay.addLayout(form); lay.addStretch(1)
        knr = QHBoxLayout(); knr.addStretch(1)
        ann = QPushButton(T("annuleren")); ann.clicked.connect(self.reject); knr.addWidget(ann)
        ok = QPushButton(T("opslaan")); ok.setObjectName("primair")
        ok.clicked.connect(self._ok); knr.addWidget(ok)
        lay.addLayout(knr)
        QTimer.singleShot(0, lambda: centreer(self, ouder))

    def _ok(self):
        self.cfg["taal"] = self.taal.currentData()
        self.accept()


SNELGIDS_NL = """
<h2>DraveWall - Snelgids</h2>
<p>DraveWall is een voorkant voor de <b>Windows Defender Firewall</b>. Het maakt geen
eigen firewall, maar beheert die van Windows. <b>Wijzigen vereist beheerdersrechten</b>
(de knop 'Herstart als beheerder' staat op het tabblad Status).</p>
<h3>Status</h3>
<p>Zet de firewall <b>per profiel</b> (Domein/Prive/Openbaar) aan of uit. Maak hier ook
een <b>back-up</b> van de firewall-instellingen, of <b>herstel</b> die.</p>
<h3>Programma's</h3>
<p>Kies een <b>.exe</b>, kies de richting (uitgaand/inkomend/beide) en klik
<b>Blokkeren</b> of <b>Toestaan</b>. Zo houd je bijvoorbeeld een programma van internet af.</p>
<h3>Regels</h3>
<p>Bekijk en doorzoek alle firewall-regels. Selecteer een regel om die <b>in/uit te
schakelen</b> of te <b>verwijderen</b>, of maak een <b>nieuwe regel</b>. Elke regel die
DraveWall maakt heet 'DraveWall - ...'; met <b>Verwijder alle DraveWall-regels</b> draai
je in een klik alles terug wat je met DraveWall hebt toegevoegd.</p>
<h3>Hosts</h3>
<p>Bewerk het Windows <b>hosts-bestand</b>. Met <b>Domein blokkeren</b> wijs je een domein naar 0.0.0.0, zodat het niet meer geladen wordt. Klik daarna <b>Opslaan</b> (vereist beheerder); DraveWall maakt eerst een back-up in DraveWall-data en leegt de DNS-cache.</p>
<p>Donatie (vrijwillig): <b>paypal.me/roger076</b> &middot; service@dravenlock.nl</p>
"""
SNELGIDS_EN = """
<h2>DraveWall - Quick guide</h2>
<p>DraveWall is a front-end for the <b>Windows Defender Firewall</b>. It manages Windows'
firewall rather than making its own. <b>Changing requires administrator rights</b> (the
'Restart as administrator' button is on the Status tab).</p>
<h3>Status</h3>
<p>Turn the firewall on or off <b>per profile</b> (Domain/Private/Public). Also make a
<b>backup</b> of the firewall settings here, or <b>restore</b> one.</p>
<h3>Programs</h3>
<p>Pick an <b>.exe</b>, choose the direction (outbound/inbound/both) and click <b>Block</b>
or <b>Allow</b>. This is how you keep a program off the internet, for example.</p>
<h3>Rules</h3>
<p>View and search all firewall rules. Select a rule to <b>enable/disable</b> or
<b>delete</b> it, or create a <b>new rule</b>. Every rule DraveWall makes is named
'DraveWall - ...'; <b>Delete all DraveWall rules</b> reverts everything you added with
DraveWall in one click.</p>
<h3>Hosts</h3>
<p>Edit the Windows <b>hosts file</b>. With <b>Block domain</b> you point a domain to 0.0.0.0 so it no longer loads. Then click <b>Save</b> (requires administrator); DraveWall makes a backup in DraveWall-data first and flushes the DNS cache.</p>
<p>Donate (voluntary): <b>paypal.me/roger076</b> &middot; service@dravenlock.nl</p>
"""


class SnelgidsDialoog(QDialog):
    def __init__(self, ouder):
        super().__init__(ouder)
        self.setWindowTitle(T("snelgids")); self.setWindowIcon(app_icoon())
        self.resize(700, 580); self.setStyleSheet(STIJL())
        lay = QVBoxLayout(self)
        b = QTextBrowser(); b.setOpenExternalLinks(True)
        b.setHtml(SNELGIDS_NL if _TAAL == "nl" else SNELGIDS_EN)
        lay.addWidget(b)
        k = QPushButton(T("sluiten")); k.clicked.connect(self.accept); lay.addWidget(k)
        QTimer.singleShot(0, lambda: centreer(self, ouder))


class NieuweRegelDialoog(QDialog):
    def __init__(self, ouder):
        super().__init__(ouder)
        self.setWindowTitle(T("nr_titel")); self.setWindowIcon(app_icoon())
        self.resize(560, 420); self.setStyleSheet(STIJL())
        self.resultaat = None
        lay = QVBoxLayout(self); form = QFormLayout()
        self.naam = QLineEdit(); form.addRow(T("nr_naam"), self.naam)
        prij = QHBoxLayout()
        self.prog = QLineEdit(); prij.addWidget(self.prog, 1)
        bb = QPushButton(T("bladeren")); bb.clicked.connect(self._kies_prog); prij.addWidget(bb)
        form.addRow(T("nr_prog"), self._wrap(prij))
        self.actie = QComboBox()
        self.actie.addItem(T("blokkeer"), FW.ACTIE_BLOKKEREN)
        self.actie.addItem(T("toestaan"), FW.ACTIE_TOESTAAN)
        form.addRow(T("nr_actie"), self.actie)
        self.richting = QComboBox()
        self.richting.addItem(T("r_uit"), FW.RICHTING_UIT)
        self.richting.addItem(T("r_in"), FW.RICHTING_IN)
        form.addRow(T("nr_richting"), self.richting)
        self.proto = QComboBox()
        self.proto.addItem(T("proto_alle"), FW.PROTO_ALLE)
        self.proto.addItem("TCP", FW.PROTO_TCP)
        self.proto.addItem("UDP", FW.PROTO_UDP)
        form.addRow(T("nr_proto"), self.proto)
        self.lokaal = QLineEdit(); self.lokaal.setPlaceholderText("80, 443")
        form.addRow(T("nr_lokaal"), self.lokaal)
        self.extern = QLineEdit(); self.extern.setPlaceholderText("80, 443")
        form.addRow(T("nr_extern"), self.extern)
        # profielen
        prof = QHBoxLayout()
        self.cb_dom = QCheckBox(T("prof_domein")); self.cb_dom.setChecked(True)
        self.cb_priv = QCheckBox(T("prof_prive")); self.cb_priv.setChecked(True)
        self.cb_pub = QCheckBox(T("prof_openbaar")); self.cb_pub.setChecked(True)
        for c in (self.cb_dom, self.cb_priv, self.cb_pub):
            prof.addWidget(c)
        prof.addStretch(1)
        form.addRow(T("nr_prof"), self._wrap(prof))
        lay.addLayout(form); lay.addStretch(1)
        knr = QHBoxLayout(); knr.addStretch(1)
        ann = QPushButton(T("annuleren")); ann.clicked.connect(self.reject); knr.addWidget(ann)
        ok = QPushButton(T("maken")); ok.setObjectName("primair")
        ok.clicked.connect(self._ok); knr.addWidget(ok)
        lay.addLayout(knr)
        QTimer.singleShot(0, lambda: centreer(self, ouder))

    def _wrap(self, layout):
        w = QWidget(); w.setLayout(layout); return w

    def _kies_prog(self):
        p, _ = QFileDialog.getOpenFileName(self, T("nr_prog"), "", "Programma's (*.exe);;Alle (*.*)")
        if p:
            self.prog.setText(p)
            if not self.naam.text().strip():
                self.naam.setText(os.path.splitext(os.path.basename(p))[0])

    def _profielen(self):
        b = 0
        if self.cb_dom.isChecked():
            b |= FW.PROF_DOMEIN
        if self.cb_priv.isChecked():
            b |= FW.PROF_PRIVE
        if self.cb_pub.isChecked():
            b |= FW.PROF_OPENBAAR
        return b or FW.PROF_ALLE

    def _ok(self):
        if not self.naam.text().strip():
            QMessageBox.information(self, APP_NAAM, T("nr_naam_leeg")); return
        self.resultaat = {
            "naam": self.naam.text().strip(), "programma": self.prog.text().strip(),
            "actie": self.actie.currentData(), "richting": self.richting.currentData(),
            "protocol": self.proto.currentData(),
            "lokale_poorten": self.lokaal.text().strip(),
            "externe_poorten": self.extern.text().strip(),
            "profielen": self._profielen(),
        }
        self.accept()


# ---------------------------------------------------------------------------
class Hoofdvenster(QMainWindow):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self._alle_regels = []
        self.setWindowTitle("%s  v%s" % (APP_NAAM, APP_VERSIE))
        self.setWindowIcon(app_icoon())
        self.resize(1080, 740); self.setStyleSheet(STIJL())
        self._menu()
        self._bouw()
        sb = QStatusBar(); self.setStatusBar(sb)
        b = QPushButton(" \u2665 " + T("donatie")); b.setObjectName("primair")
        b.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(DONATIE_URL)))
        sb.addPermanentWidget(b)
        if FW.beschikbaar():
            QTimer.singleShot(0, self._ververs_alles)
        QTimer.singleShot(0, self._laad_hosts)

    def _menu(self):
        balk = self.menuBar()
        m = balk.addMenu(T("menu_bestand"))
        a = QAction(T("instellingen"), self); a.triggered.connect(self._instellingen); m.addAction(a)
        m.addSeparator()
        a = QAction(T("afsluiten"), self); a.setShortcut("Ctrl+Q")
        a.triggered.connect(self.close); m.addAction(a)
        h = balk.addMenu(T("menu_help"))
        a = QAction(T("snelgids"), self); a.setShortcut("F1")
        a.triggered.connect(lambda: SnelgidsDialoog(self).exec()); h.addAction(a)
        a = QAction(T("over"), self); a.triggered.connect(self._over); h.addAction(a)
        a = QAction(T("donatie"), self)
        a.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(DONATIE_URL))); h.addAction(a)

    def _bouw(self):
        centraal = QWidget(); self.setCentralWidget(centraal)
        lay = QVBoxLayout(centraal)
        kop = QLabel(APP_NAAM); kop.setObjectName("titel"); lay.addWidget(kop)
        sub = QLabel(T("ondertitel")); sub.setObjectName("sub"); lay.addWidget(sub)
        if not FW.op_windows():
            band = QLabel(T("niet_windows")); band.setObjectName("waarschuwing")
            band.setWordWrap(True); lay.addWidget(band)
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_welkom(), T("tab_welkom"))   # 0
        self.tabs.addTab(self._tab_status(), T("tab_status"))   # 1
        self.tabs.addTab(self._tab_prog(), T("tab_prog"))       # 2
        self.tabs.addTab(self._tab_regels(), T("tab_regels"))   # 3
        self.tabs.addTab(self._tab_hosts(), T("tab_hosts"))     # 4
        lay.addWidget(self.tabs, 1)
        self.tabs.setCurrentIndex(0 if self.cfg.get("toon_welkom", True) else 1)

    # ---- welkom ----
    def _tab_welkom(self):
        w = QWidget(); buiten = QVBoxLayout(w); buiten.addStretch(1)
        m = QVBoxLayout(); m.setSpacing(14); m.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        logo = QLabel(); logo.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        p = _bundel("logo.png")
        if os.path.isfile(p):
            pix = QPixmap(p)
            if not pix.isNull():
                logo.setPixmap(pix.scaledToHeight(150, Qt.TransformationMode.SmoothTransformation))
        m.addWidget(logo)
        titel = QLabel("%s  v%s" % (APP_NAAM, APP_VERSIE)); titel.setObjectName("titel")
        titel.setAlignment(Qt.AlignmentFlag.AlignHCenter); m.addWidget(titel)
        intro = QLabel(T("welkom_intro")); intro.setObjectName("sub")
        intro.setWordWrap(True); intro.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        intro.setMaximumWidth(660); m.addWidget(intro, 0, Qt.AlignmentFlag.AlignHCenter)
        # admin-banner: meteen zien of je beheerder bent + direct kunnen verhogen
        self.welkom_admin = QFrame(); self.welkom_admin.setObjectName("banner")
        self.welkom_admin.setFixedWidth(660)
        wal = QHBoxLayout(self.welkom_admin)
        self.welkom_admin_tekst = QLabel(""); self.welkom_admin_tekst.setWordWrap(True)
        wal.addWidget(self.welkom_admin_tekst, 1)
        self.welkom_admin_knop = QPushButton(T("herstart_admin"))
        self.welkom_admin_knop.clicked.connect(self._herstart_admin)
        wal.addWidget(self.welkom_admin_knop)
        m.addWidget(self.welkom_admin, 0, Qt.AlignmentFlag.AlignHCenter)
        knr = QHBoxLayout(); knr.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        b1 = QPushButton(T("welkom_prog")); b1.setObjectName("primair")
        b1.setMinimumWidth(250); b1.setMinimumHeight(56)
        b1.clicked.connect(lambda: self.tabs.setCurrentIndex(2))
        b2 = QPushButton(T("welkom_regels")); b2.setObjectName("primair")
        b2.setMinimumWidth(250); b2.setMinimumHeight(56)
        b2.clicked.connect(lambda: self.tabs.setCurrentIndex(3))
        knr.addWidget(b1); knr.addWidget(b2); m.addLayout(knr)
        gids = QPushButton(T("snelgids")); gids.clicked.connect(lambda: SnelgidsDialoog(self).exec())
        m.addWidget(gids, 0, Qt.AlignmentFlag.AlignHCenter)
        self.chk_welkom = QCheckBox(T("welkom_toon"))
        self.chk_welkom.setChecked(self.cfg.get("toon_welkom", True))
        self.chk_welkom.toggled.connect(self._welkom_toggle)
        m.addWidget(self.chk_welkom, 0, Qt.AlignmentFlag.AlignHCenter)
        buiten.addLayout(m); buiten.addStretch(1)
        self._ververs_welkom_admin()
        return w

    def _ververs_welkom_admin(self):
        if not FW.op_windows():
            self.welkom_admin.setVisible(False)
            return
        self.welkom_admin.setVisible(True)
        beheerder = FW.is_beheerder()
        if beheerder:
            self.welkom_admin_tekst.setText(T("beheerder_ok"))
            self.welkom_admin_tekst.setStyleSheet("color:%s; background:transparent;" % GOED)
            self.welkom_admin.setStyleSheet(
                "QFrame#banner{background:%s;border:1px solid %s;border-radius:8px;}" % (PANEL2, GOED))
            self.welkom_admin_knop.setVisible(False)
        else:
            self.welkom_admin_tekst.setText(T("welkom_admin_vraag"))
            self.welkom_admin_tekst.setStyleSheet("color:%s; background:transparent;" % WARN)
            self.welkom_admin.setStyleSheet(
                "QFrame#banner{background:%s;border:1px solid %s;border-radius:8px;}" % (PANEL2, WARN))
            self.welkom_admin_knop.setVisible(True)

    def _welkom_toggle(self, aan):
        self.cfg["toon_welkom"] = bool(aan); bewaar_config(self.cfg)

    # ---- status ----
    def _tab_status(self):
        w = QWidget(); lay = QVBoxLayout(w)
        self.banner = QFrame(); self.banner.setObjectName("banner")
        bl = QHBoxLayout(self.banner)
        self.banner_tekst = QLabel(""); self.banner_tekst.setWordWrap(True)
        bl.addWidget(self.banner_tekst, 1)
        self.knop_admin = QPushButton(T("herstart_admin"))
        self.knop_admin.clicked.connect(self._herstart_admin)
        bl.addWidget(self.knop_admin)
        lay.addWidget(self.banner)

        lay.addWidget(QLabel(T("firewall_profielen")))
        grid = QGridLayout()
        self.prof_labels = {}
        self.prof_knoppen = {}
        rij = 0
        for sleutel, lbl in (("domein", "prof_domein"), ("prive", "prof_prive"),
                             ("openbaar", "prof_openbaar")):
            grid.addWidget(QLabel(T(lbl)), rij, 0)
            stat = QLabel("-"); self.prof_labels[sleutel] = stat
            grid.addWidget(stat, rij, 1)
            knop = QPushButton(T("uit")); 
            knop.clicked.connect(lambda _=False, s=sleutel: self._toggle_profiel(s))
            self.prof_knoppen[sleutel] = knop
            grid.addWidget(knop, rij, 2)
            rij += 1
        grid.setColumnStretch(3, 1)
        lay.addLayout(grid)
        vrij = QHBoxLayout()
        bv = QPushButton(T("vernieuwen")); bv.clicked.connect(self._ververs_status)
        vrij.addWidget(bv); vrij.addStretch(1)
        lay.addLayout(vrij)

        lijn = QFrame(); lijn.setFrameShape(QFrame.Shape.HLine)
        lijn.setStyleSheet("color:%s;" % LINE); lay.addWidget(lijn)
        lay.addWidget(QLabel(T("veiligheid")))
        srij = QHBoxLayout()
        bb = QPushButton(T("backup")); bb.clicked.connect(self._backup)
        bh = QPushButton(T("herstel")); bh.clicked.connect(self._herstel)
        srij.addWidget(bb); srij.addWidget(bh); srij.addStretch(1)
        lay.addLayout(srij)
        lay.addStretch(1)
        self.status_status = QLabel(""); self.status_status.setObjectName("sub")
        lay.addWidget(self.status_status)
        return w

    def _ververs_status(self):
        beheerder = FW.is_beheerder()
        self.banner_tekst.setText(T("beheerder_ok") if beheerder else T("beheerder_niet"))
        self.banner_tekst.setObjectName("ok" if beheerder else "waarschuwing")
        self.banner_tekst.setStyleSheet("color:%s; background:transparent;" % (GOED if beheerder else WARN))
        self.knop_admin.setVisible(not beheerder and FW.op_windows())
        if not FW.beschikbaar():
            for s in self.prof_labels:
                self.prof_labels[s].setText("-")
            return
        try:
            st = FW.profiel_status()
            for s, aan in st.items():
                self.prof_labels[s].setText(T("aan") if aan else T("uit"))
                self.prof_labels[s].setStyleSheet("color:%s;" % (GOED if aan else WARN))
                self.prof_knoppen[s].setText(T("uit") if aan else T("aan"))
        except Exception as e:
            _toon_fout(self, e, "status lezen")

    def _toggle_profiel(self, sleutel):
        try:
            st = FW.profiel_status()
            nu_aan = st.get(sleutel, True)
            if nu_aan:  # we gaan uitzetten
                if QMessageBox.question(self, APP_NAAM, T("fw_uit_vraag")) != \
                        QMessageBox.StandardButton.Yes:
                    return
            FW.zet_profiel(sleutel, not nu_aan)
            self._ververs_status()
        except Exception as e:
            _toon_fout(self, e, "profiel schakelen")

    def _backup(self):
        p, _ = QFileDialog.getSaveFileName(self, T("backup"),
                                           os.path.join(self.cfg.get("backup_map", BASIS),
                                                        "firewall-backup.wfw"),
                                           "*.wfw")
        if not p:
            return
        if not p.lower().endswith(".wfw"):
            p += ".wfw"
        try:
            FW.exporteer(p)
            self.cfg["backup_map"] = os.path.dirname(p); bewaar_config(self.cfg)
            self.status_status.setText(T("backup_klaar"))
            self.status_status.setStyleSheet("color:%s;" % GOED)
        except Exception as e:
            _toon_fout(self, e, "back-up")

    def _herstel(self):
        p, _ = QFileDialog.getOpenFileName(self, T("herstel"),
                                           self.cfg.get("backup_map", BASIS), "*.wfw")
        if not p:
            return
        if QMessageBox.question(self, APP_NAAM, T("herstel_vraag")) != \
                QMessageBox.StandardButton.Yes:
            return
        try:
            FW.importeer(p)
            self.status_status.setText(T("herstel_klaar"))
            self.status_status.setStyleSheet("color:%s;" % GOED)
            self._ververs_status()
        except Exception as e:
            _toon_fout(self, e, "herstel")

    # ---- programma's ----
    def _tab_prog(self):
        w = QWidget(); lay = QVBoxLayout(w)
        form = QFormLayout()
        prij = QHBoxLayout()
        self.prog_pad = QLineEdit(); prij.addWidget(self.prog_pad, 1)
        bb = QPushButton(T("bladeren")); bb.clicked.connect(self._kies_prog); prij.addWidget(bb)
        wrap = QWidget(); wrap.setLayout(prij)
        form.addRow(T("prog_kies"), wrap)
        self.prog_label = QLineEdit(); form.addRow(T("prog_label"), self.prog_label)
        self.prog_richting = QComboBox()
        self.prog_richting.addItem(T("r_uit"), ("uit",))
        self.prog_richting.addItem(T("r_in"), ("in",))
        self.prog_richting.addItem(T("r_beide"), ("uit", "in"))
        form.addRow(T("prog_richting"), self.prog_richting)
        prof = QHBoxLayout()
        self.pcb_dom = QCheckBox(T("prof_domein")); self.pcb_dom.setChecked(True)
        self.pcb_priv = QCheckBox(T("prof_prive")); self.pcb_priv.setChecked(True)
        self.pcb_pub = QCheckBox(T("prof_openbaar")); self.pcb_pub.setChecked(True)
        for c in (self.pcb_dom, self.pcb_priv, self.pcb_pub):
            prof.addWidget(c)
        prof.addStretch(1)
        wrap2 = QWidget(); wrap2.setLayout(prof)
        form.addRow(T("prog_prof"), wrap2)
        lay.addLayout(form)
        knr = QHBoxLayout()
        bblok = QPushButton(T("blokkeer")); bblok.setObjectName("gevaar")
        bblok.setMinimumHeight(48); bblok.clicked.connect(lambda: self._prog_actie(True))
        btoe = QPushButton(T("toestaan")); btoe.setObjectName("primair")
        btoe.setMinimumHeight(48); btoe.clicked.connect(lambda: self._prog_actie(False))
        knr.addWidget(bblok); knr.addWidget(btoe)
        lay.addLayout(knr)
        lay.addStretch(1)
        self.status_prog = QLabel(""); self.status_prog.setObjectName("sub")
        lay.addWidget(self.status_prog)
        return w

    def _kies_prog(self):
        p, _ = QFileDialog.getOpenFileName(self, T("prog_kies"),
                                           self.cfg.get("laatste_map", BASIS),
                                           "Programma's (*.exe);;Alle (*.*)")
        if p:
            self.prog_pad.setText(p)
            self.cfg["laatste_map"] = os.path.dirname(p)
            if not self.prog_label.text().strip():
                self.prog_label.setText(os.path.splitext(os.path.basename(p))[0])

    def _prog_profielen(self):
        b = 0
        if self.pcb_dom.isChecked():
            b |= FW.PROF_DOMEIN
        if self.pcb_priv.isChecked():
            b |= FW.PROF_PRIVE
        if self.pcb_pub.isChecked():
            b |= FW.PROF_OPENBAAR
        return b or FW.PROF_ALLE

    def _prog_actie(self, blokkeren):
        pad = self.prog_pad.text().strip()
        if not pad:
            QMessageBox.information(self, APP_NAAM, T("prog_geen")); return
        naam = self.prog_label.text().strip() or os.path.splitext(os.path.basename(pad))[0]
        vraag = T("blok_vraag") if blokkeren else T("toe_vraag")
        if QMessageBox.question(self, APP_NAAM, vraag.format(naam=naam)) != \
                QMessageBox.StandardButton.Yes:
            return
        richtingen = self.prog_richting.currentData()
        prof = self._prog_profielen()
        try:
            if blokkeren:
                FW.blokkeer_programma(pad, naam, richtingen, prof)
                self.status_prog.setText(T("blok_klaar").format(naam=naam))
            else:
                FW.sta_programma_toe(pad, naam, richtingen, prof)
                self.status_prog.setText(T("toe_klaar").format(naam=naam))
            self.status_prog.setStyleSheet("color:%s;" % GOED)
            self._laad_regels()
        except Exception as e:
            self.status_prog.setStyleSheet("color:%s;" % WARN)
            self.status_prog.setText(T("fout").format(fout=e))
            _toon_fout(self, e, "programma-regel")

    # ---- regels ----
    def _tab_regels(self):
        w = QWidget(); lay = QVBoxLayout(w)
        brij = QHBoxLayout()
        self.zoek = QLineEdit(); self.zoek.setPlaceholderText(T("zoek"))
        self.zoek.textChanged.connect(self._toon_regels)
        brij.addWidget(self.zoek, 1)
        self.cb_alleen = QCheckBox(T("alleen_drave"))
        self.cb_alleen.toggled.connect(self._toon_regels)
        brij.addWidget(self.cb_alleen)
        bv = QPushButton(T("vernieuwen")); bv.clicked.connect(self._laad_regels)
        brij.addWidget(bv)
        lay.addLayout(brij)

        self.tabel = QTableWidget(0, 6)
        self.tabel.setHorizontalHeaderLabels([T("k_aan"), T("k_naam"), T("k_prog"),
                                              T("k_richting"), T("k_actie"), T("k_prof")])
        self.tabel.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabel.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabel.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabel.verticalHeader().setVisible(False)
        kop = self.tabel.horizontalHeader()
        kop.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        kop.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        lay.addWidget(self.tabel, 1)

        self.regels_info = QLabel(""); self.regels_info.setObjectName("sub")
        lay.addWidget(self.regels_info)
        krij = QHBoxLayout()
        b1 = QPushButton(T("in_uit")); b1.clicked.connect(self._toggle_regel)
        b2 = QPushButton(T("verwijder")); b2.setObjectName("gevaar"); b2.clicked.connect(self._verwijder_regel)
        b3 = QPushButton(T("nieuwe")); b3.clicked.connect(self._nieuwe_regel)
        krij.addWidget(b1); krij.addWidget(b2); krij.addWidget(b3); krij.addStretch(1)
        b4 = QPushButton(T("verwijder_drave")); b4.setObjectName("gevaar")
        b4.clicked.connect(self._verwijder_drave)
        krij.addWidget(b4)
        lay.addLayout(krij)
        return w

    def _laad_regels(self):
        if not FW.beschikbaar():
            self._alle_regels = []; self._toon_regels(); return
        try:
            self._alle_regels = FW.lijst_regels("", False)
        except Exception as e:
            self._alle_regels = []
            _toon_fout(self, e, "regels lezen")
        self._toon_regels()

    def _toon_regels(self):
        zoek = self.zoek.text().strip().lower()
        alleen = self.cb_alleen.isChecked()
        vorige = None
        d0 = self._gekozen_regel()
        if d0:
            vorige = d0["naam"]
        regels = []
        for d in self._alle_regels:
            if alleen and not d.get("van_drave"):
                continue
            if zoek and zoek not in d["naam"].lower() and zoek not in d["programma"].lower():
                continue
            regels.append(d)
        self.tabel.setRowCount(0)
        herstel_rij = -1
        for d in regels:
            r = self.tabel.rowCount(); self.tabel.insertRow(r)
            rich = T("richting_in") if d["richting"] == "in" else T("richting_uit")
            actie = T("actie_toestaan") if d["actie"] == "toestaan" else T("actie_blokkeren")
            waarden = [T("aan") if d["aan"] else T("uit"), d["naam"], d["programma"],
                       rich, actie, _prof_tekst(d["profielen"])]
            for k, v in enumerate(waarden):
                it = QTableWidgetItem(v)
                if k == 0:
                    it.setData(Qt.ItemDataRole.UserRole, d)
                if d.get("van_drave"):
                    it.setForeground(Qt.GlobalColor.cyan)
                self.tabel.setItem(r, k, it)
            if vorige and d["naam"] == vorige:
                herstel_rij = r
        if herstel_rij >= 0:
            self.tabel.selectRow(herstel_rij)
        self.regels_info.setText(T("regels_n").format(n=len(regels)))

    def _gekozen_regel(self):
        rij = self.tabel.currentRow()
        if rij < 0:
            return None
        it = self.tabel.item(rij, 0)
        return it.data(Qt.ItemDataRole.UserRole) if it else None

    def _toggle_regel(self):
        d = self._gekozen_regel()
        if not d:
            QMessageBox.information(self, APP_NAAM, T("kies_regel")); return
        try:
            FW.zet_regel_aan(d["naam"], not d["aan"])
            self._laad_regels()
        except Exception as e:
            _toon_fout(self, e, "regel schakelen")

    def _verwijder_regel(self):
        d = self._gekozen_regel()
        if not d:
            QMessageBox.information(self, APP_NAAM, T("kies_regel")); return
        if QMessageBox.question(self, APP_NAAM, T("verwijder_vraag").format(naam=d["naam"])) != \
                QMessageBox.StandardButton.Yes:
            return
        try:
            FW.verwijder_regel(d["naam"]); self._laad_regels()
        except Exception as e:
            _toon_fout(self, e, "regel verwijderen")

    def _nieuwe_regel(self):
        d = NieuweRegelDialoog(self)
        if not d.exec() or not d.resultaat:
            return
        r = d.resultaat
        try:
            FW.maak_regel(r["naam"], programma=r["programma"], actie=r["actie"],
                          richting=r["richting"], profielen=r["profielen"],
                          protocol=r["protocol"], lokale_poorten=r["lokale_poorten"],
                          externe_poorten=r["externe_poorten"])
            self._laad_regels()
        except Exception as e:
            _toon_fout(self, e, "regel maken")

    def _verwijder_drave(self):
        if QMessageBox.question(self, APP_NAAM, T("verwijder_drave_vraag")) != \
                QMessageBox.StandardButton.Yes:
            return
        try:
            n = FW.verwijder_drave_regels()
            QMessageBox.information(self, APP_NAAM, T("verwijder_drave_klaar").format(n=n))
            self._laad_regels()
        except Exception as e:
            _toon_fout(self, e, "DraveWall-regels verwijderen")

    # ---- hosts ----
    def _tab_hosts(self):
        w = QWidget(); lay = QVBoxLayout(w)
        uit = QLabel(T("hosts_uitleg")); uit.setObjectName("sub"); uit.setWordWrap(True)
        lay.addWidget(uit)
        self.hosts_pad_label = QLabel(HB.standaard_pad()); self.hosts_pad_label.setObjectName("sub")
        lay.addWidget(self.hosts_pad_label)
        self.hosts_edit = QPlainTextEdit()
        self.hosts_edit.setStyleSheet(
            "font-family: Consolas, 'Courier New', monospace; font-size: 14px;")
        lay.addWidget(self.hosts_edit, 1)
        self.hosts_status = QLabel(""); self.hosts_status.setObjectName("sub")
        lay.addWidget(self.hosts_status)
        krij = QHBoxLayout()
        bh = QPushButton(T("hosts_herladen")); bh.clicked.connect(self._laad_hosts)
        bb = QPushButton(T("hosts_blokkeer")); bb.clicked.connect(self._hosts_blokkeer)
        bd = QPushButton(T("hosts_deblok")); bd.clicked.connect(self._hosts_deblok)
        bo = QPushButton(T("hosts_opslaan")); bo.setObjectName("primair")
        bo.clicked.connect(self._hosts_opslaan)
        krij.addWidget(bh); krij.addWidget(bb); krij.addWidget(bd)
        krij.addStretch(1); krij.addWidget(bo)
        lay.addLayout(krij)
        return w

    def _laad_hosts(self):
        try:
            self.hosts_edit.setPlainText(HB.lees())
            self.hosts_status.setStyleSheet("color:%s;" % MUTED)
            self.hosts_status.setText("")
        except Exception as e:
            self.hosts_status.setStyleSheet("color:%s;" % WARN)
            self.hosts_status.setText(T("hosts_lees_fout"))
            _toon_fout(self, e, "hosts lezen")

    def _hosts_blokkeer(self):
        domein, ok = QInputDialog.getText(self, T("hosts_blokkeer"), T("hosts_blokkeer_vraag"))
        if not ok or not domein.strip():
            return
        nieuw = HB.blokkeer_domein(self.hosts_edit.toPlainText(), domein)
        self.hosts_edit.setPlainText(nieuw)
        self.hosts_status.setStyleSheet("color:%s;" % MUTED)
        self.hosts_status.setText(T("hosts_blok_toegevoegd").format(domein=domein.strip()))

    def _hosts_deblok(self):
        domein, ok = QInputDialog.getText(self, T("hosts_deblok"), T("hosts_blokkeer_vraag"))
        if not ok or not domein.strip():
            return
        nieuw = HB.deblokkeer_domein(self.hosts_edit.toPlainText(), domein)
        self.hosts_edit.setPlainText(nieuw)
        self.hosts_status.setText(T("hosts_deblok_klaar").format(domein=domein.strip()))

    def _hosts_opslaan(self):
        if not FW.is_beheerder():
            QMessageBox.warning(self, APP_NAAM, T("hosts_admin_nodig"))
            return
        if QMessageBox.question(self, APP_NAAM, T("hosts_opslaan_vraag")) != \
                QMessageBox.StandardButton.Yes:
            return
        try:
            HB.schrijf(self.hosts_edit.toPlainText(), backup_map=DATA_MAP)
            HB.flush_dns()
            self.hosts_status.setStyleSheet("color:%s;" % GOED)
            self.hosts_status.setText(T("hosts_opgeslagen"))
        except PermissionError as e:
            _toon_fout(self, e, "hosts opslaan")
        except Exception as e:
            self.hosts_status.setStyleSheet("color:%s;" % WARN)
            self.hosts_status.setText(T("fout").format(fout=e))
            _toon_fout(self, e, "hosts opslaan")

    # ---- gedeeld ----
    def _ververs_alles(self):
        self._ververs_status()
        self._laad_regels()

    def _herstart_admin(self):
        FW.herstart_als_beheerder(os.path.abspath(__file__) if not getattr(sys, "frozen", False) else None)
        self.close()

    def _instellingen(self):
        global _TAAL
        d = InstellingenDialoog(self, self.cfg)
        if d.exec():
            bewaar_config(self.cfg)
            nieuw = self.cfg.get("taal", "auto")
            _TAAL = taal_detecteren() if nieuw == "auto" else nieuw
            QMessageBox.information(self, APP_NAAM, T("herstart_taal"))

    def _over(self):
        QMessageBox.information(self, T("over"), T("over_tekst").format(
            versie=APP_VERSIE, contact=CONTACT, donatie=DONATIE_URL))


def _prof_tekst(bitmask):
    if bitmask == FW.PROF_ALLE or bitmask == 0:
        return T("p_alle")
    delen = []
    if bitmask & FW.PROF_DOMEIN:
        delen.append(T("prof_domein"))
    if bitmask & FW.PROF_PRIVE:
        delen.append(T("prof_prive"))
    if bitmask & FW.PROF_OPENBAAR:
        delen.append(T("prof_openbaar"))
    return ", ".join(delen) if delen else T("p_alle")


def main():
    global _TAAL
    zorg_voor_mappen()
    cfg = laad_config()
    taal = cfg.get("taal", "auto")
    _TAAL = taal_detecteren() if taal == "auto" else (taal if taal in ("nl", "en")
                                                      else taal_detecteren())
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Dravenlock.DraveWall")
        except Exception:
            pass
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAAM)
    app.setWindowIcon(app_icoon())
    app.setStyleSheet(STIJL())
    venster = Hoofdvenster(cfg)
    venster.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
