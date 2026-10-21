DraveWall - voorkant voor de Windows-firewall
==============================================

Dravenlock - lokaal, geen cloud.

WAT HET IS
----------
DraveWall maakt zelf geen firewall; het beheert de ingebouwde Windows Defender
Firewall met een eenvoudige interface. Blokkeer of sta programma's toe, beheer
regels en zet de firewall per profiel aan of uit.

BEHEERDERSRECHTEN
-----------------
Regels BEKIJKEN kan altijd. Regels WIJZIGEN (blokkeren/toestaan/aan-uit/verwijderen,
profiel schakelen, herstellen) vereist beheerdersrechten. De losse .exe vraagt daar
automatisch om (UAC). Start je via run.bat, gebruik dan de knop "Herstart als
beheerder" op het tabblad Status.

STARTEN
-------
Dubbelklik run.bat (Python 3.10 t/m 3.13 nodig). Werkt iets niet, gebruik
start-debug.bat: die toont de fouten.

VEILIGHEID
----------
- Elke regel die DraveWall maakt heet "DraveWall - ...". Met de knop "Verwijder alle
  DraveWall-regels" (tabblad Regels) draai je in een klik alles terug wat je met
  DraveWall hebt toegevoegd. Systeemregels blijven ongemoeid.
- Maak vooraf een BACK-UP (tabblad Status) van je firewall-instellingen; met
  "Herstellen" zet je die terug als er iets misgaat.
- Een foute regel kan internet blokkeren. Twijfel je? Maak eerst een back-up.

WAAR STAAN MIJN INSTELLINGEN
----------------------------
In de map DraveWall-data naast de app (taal, voorkeuren, fout-log.txt).

LOSSE .EXE MAKEN (optioneel)
----------------------------
Dubbelklik bouw-exe.bat. De .exe komt in de map dist (onefile, vraagt om beheerder).

SNELGIDS: druk op F1.
DONATIE (vrijwillig): https://paypal.me/roger076
CONTACT: service@dravenlock.nl
