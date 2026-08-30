# powera-xinput

Einen kabelgebundenen PowerA-Switch-Controller unter Windows als Xbox-Controller
benutzen.

*[English version](README.md)*

---

Windows erkennt die meisten PowerA-Switch-Pads als gewöhnliches DirectInput-HID-Gerät.
Viele Spiele hören aber nur auf XInput: Der Controller steht in den Systemeinstellungen,
im Testdialog bewegen sich die Sticks — und im Spiel passiert nichts. Dieses Skript
liest die rohen HID-Reports des Pads und gibt sie auf einem virtuellen
Xbox-360-Controller wieder, den diese Spiele akzeptieren.

**Nicht geeignet für den Nintendo Switch Pro Controller oder Joy-Cons.** Das ist
Nintendo-Hardware (Vendor-ID `0x057E`) mit einem anderen Protokoll — dafür gibt es
[BetterJoy](https://github.com/Davidobot/BetterJoy). Dieses Skript ist für die
PowerA-Pads von Drittanbietern (Vendor-ID `0x20D6`), die kabelgebundenen, offiziell
lizenzierten Switch-Zubehörteile.

### Warum das hier steht

An der Switch tut das Pad, was es soll. Am PC sah Windows es, im Testdialog bewegten
sich die Sticks — und die Spiele interessierte es nicht. Die Lösung waren am Ende rund
hundert Zeilen, und die Frage kommt oft genug auf, dass sie es wert sind.

Es läuft auf meinem Rechner mit meinem Controller, und mehr ist nicht getestet. PowerA
vergibt jedem Modell eine eigene Product-ID, deins kann also abweichen. `read_hid.py`
und [docs/hid-report.de.md](docs/hid-report.de.md) gibt es genau deshalb: damit das
Anpassen ein paar Minuten dauert statt von vorn zu beginnen.

## Was hier drin ist

Keine Oberfläche, kein Hintergrunddienst, keine Konfigurationsdatei:

| Pfad | Zweck |
| --- | --- |
| `powera_to_xbox.py` | der Mapper, der beim Spielen läuft |
| `read_hid.py` | Diagnose-Ausgabe der rohen HID-Reports, zum Anpassen der Belegung |
| [docs/hid-report.de.md](docs/hid-report.de.md) | was das Pad Byte für Byte sendet |
| `smoketest/smoketest.py` | prüft die Mapping-Logik ohne angeschlossenen Controller |

## Voraussetzungen

- Windows 10 oder 11
- Python 3.9 oder neuer ([python.org](https://www.python.org/downloads/))
- [ViGEmBus](https://github.com/nefarius/ViGEmBus/releases) — der Treiber, der das
  virtuelle Xbox-Pad bereitstellt
- ein kabelgebundener PowerA-Switch-Controller (Vendor-ID `0x20D6`)

## Installation

1. ViGEmBus über den Link oben installieren. Es ist ein Treiber, der Installer fragt
   deshalb nach Administratorrechten. Einmalig.
2. Die Python-Abhängigkeiten installieren:

   ```
   pip install -r requirements.txt
   ```

## Benutzung

Controller anstecken, dann:

```
python powera_to_xbox.py
```

Das Fenster während des Spielens offen lassen. `Strg+C` beendet und gibt alle Tasten
frei.

Optionen:

```
--vid 0x20D6      USB-Vendor-ID (Standard: PowerA)
--pid 0xA711      USB-Product-ID (Standard: jedes Gerät dieses Herstellers)
--deadzone 8      Stick-Totzone in rohen HID-Einheiten, 0-126 (Standard: 8)
--list            alle HID-Geräte mit ihren IDs auflisten und beenden
--debug           jeden rohen HID-Report während des Mappings ausgeben
```

## Wenn der Controller nicht gefunden wird

PowerA vergibt jedem Modell eine eigene Product-ID, deine kann also von der abweichen,
gegen die das hier geschrieben wurde (`0xA711`). So findest du sie:

```
python powera_to_xbox.py --list
```

Suche den Eintrag, der beim Abziehen des Pads verschwindet, und übergib seine IDs:

```
python powera_to_xbox.py --vid 0x20D6 --pid 0xA712
```

Standardmäßig wird jedes Gerät mit der PowerA-Vendor-ID akzeptiert, die meisten Modelle
sollten also ganz ohne `--pid` laufen.

## Tastenbelegung

Die vier Aktionstasten sind **nach Position belegt, nicht nach Beschriftung**. Die
Switch vertauscht A/B und X/Y gegenüber Xbox — so bleibt die untere Taste die untere
Taste, und die Einblendungen im Spiel passen zu dem, was dein Daumen tut.

| Switch | Xbox / XInput |
| --- | --- |
| B (unten) | A |
| A (rechts) | B |
| Y (links) | X |
| X (oben) | Y |
| L / R | LB / RB |
| ZL / ZR | LT / RT (digital: aus oder voll) |
| Minus / Plus | Back / Start |
| L3 / R3 | Linker / rechter Stick-Klick |
| Steuerkreuz | D-Pad (auch die Diagonalen) |
| Sticks | Linker / rechter Stick |

Home und Capture sind nicht belegt. Für Capture gibt es in XInput überhaupt keine
Entsprechung. Home könnte den Guide-Button auslösen (`XUSB_GAMEPAD_GUIDE`), aber welches
Bit ihn meldet, unterscheidet sich je nach Modell: mit `read_hid.py` herausfinden und in
`BUTTON_MAP_HIGH` eintragen. Beachte, dass das einfache `XInputGetState` den
Guide-Button ausblendet — nicht jedes Spiel sieht ihn.

## Sticks und Totzone

Rohe Sticks ruhen ein bis zwei Einheiten neben der Mitte, im Spiel wirkt das als
langsames Driften. Alles innerhalb von `--deadzone` Einheiten um die Mitte wird als
neutral gemeldet, der Bereich darüber wird wieder auf den vollen Weg gestreckt — der
Stick erreicht also weiterhin den Vollausschlag. Höher setzen, wenn es noch driftet,
niedriger für feineres Zielen:

```
python powera_to_xbox.py --deadzone 12
```

## Fehlersuche

**`VIGEM_ERROR_BUS_NOT_FOUND` / „ViGEmBus driver was not found"** — ViGEmBus
installieren und neu starten, falls der Installer danach fragt.

**Das Spiel reagiert doppelt auf einen Tastendruck** — Windows sieht das ursprüngliche
DirectInput-Pad weiterhin neben dem neuen virtuellen, und manche Spiele lesen beide. In
Steam die Controller-Einstellungen öffnen und Steam Input für das PowerA-Gerät
abschalten.

**Tasten landen an der falschen Stelle** — dein Modell hat ein anderes Report-Layout.
`python read_hid.py` starten, einzeln Tasten drücken und notieren, welches Byte sich
ändert und welches Bit kippt; [docs/hid-report.de.md](docs/hid-report.de.md) sagt, welches
Byte wofür steht. Danach `BUTTON_MAP_LOW`, `BUTTON_MAP_HIGH` und `HAT_MAP` in
`powera_to_xbox.py` anpassen. Ein Pull Request mit deinem Modell und seinen IDs ist
willkommen.

**In einem bestimmten Spiel passiert nichts** — prüfen, ob das Spiel Eingaben nur im
Vordergrund liest, und den Mapper vor dem Spiel starten.

**Anti-Cheat** — ein virtuelles Gamepad ist ein Gerät auf Treiberebene, manche
Anti-Cheat-Systeme werten das als Manipulation. Nicht ohne vorherige Prüfung der Regeln
in kompetitiven Online-Spielen einsetzen.

## Wie es funktioniert

`pywinusb` öffnet den Controller als rohes HID-Gerät und ruft für jeden Report des Pads
eine Handler-Funktion auf. Der Handler dekodiert die Tasten-Bitmasken, den HAT-Schalter
und die vier Stick-Achsen und schreibt sie auf ein virtuelles Xbox-360-Pad, das über
`vgamepad` erzeugt wird und mit dem ViGEmBus-Treiber spricht. Rund hundert Zeilen, zum
Lesen und Anpassen gedacht, nicht zum Konfigurieren. Das Layout Byte für Byte steht in
[docs/hid-report.de.md](docs/hid-report.de.md).

ViGEmBus emuliert entweder ein Xbox-360-Pad oder ein DualShock 4, und das 360er ist
das, was Windows als XInput-Gerät registriert — genau die Schnittstelle, die den
Spielen fehlt. Neuere Xbox-Controller erreichen Spiele über dieselbe XInput-API, das
ältere Modell zu emulieren kostet also nichts: Der Tastensatz ist seit 2005 unverändert.
Nur der Share-Button der Series X|S und die Impulse-Trigger liegen außerhalb von XInput
— beides gibt es an einem Switch-Pad ohnehin nicht.

## Eine Änderung prüfen

`smoketest/smoketest.py` lässt die Achsen-Rechnung und den Report-Handler gegen ein
Ersatz-Gamepad laufen, die Belegung lässt sich also ohne angestecktes Gerät prüfen:

```
python smoketest/smoketest.py
```

`vgamepad` wird trotzdem importiert, weil die Button-Konstanten von dort kommen.

## Lizenz

MIT — siehe [LICENSE](LICENSE). Fremdkomponenten und ihre Lizenzen stehen in
[THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).

Keine Verbindung zu Nintendo, PowerA oder Microsoft, weder Zusammenarbeit noch
Billigung. „Nintendo Switch", „PowerA" und „Xbox" sind Marken ihrer jeweiligen
Inhaber und werden hier nur genannt, um die Hardware zu beschreiben, mit der dieses
Skript spricht.
