# HID-Report-Referenz

*[English version](hid-report.md)*

Was ein kabelgebundenes PowerA-Switch-Pad sendet und wie `powera_to_xbox.py` es liest.
Mit *gemessen* markierte Angaben wurden an echter Hardware überprüft: ein
kabelgebundener PowerA-Controller, Vendor-ID `0x20D6`, Product-ID `0xA711`, über USB
unter Windows 11.

---

## Das Gerät

| | |
|---|---|
| Vendor-ID | `0x20D6` — Bensussen Deutsch & Associates, die Firma hinter der Marke PowerA |
| Product-ID | `0xA711` *(gemessen — andere PowerA-Modelle haben andere IDs)* |
| Anschluss | USB, kabelgebunden |
| Klasse | USB-HID, generisches Gamepad |
| Was Windows daraus macht | bindet es an DirectInput. Es erscheint in `joy.cpl` und bewegt sich im Testdialog, aber es entsteht kein XInput-Gerät — deshalb sehen Spiele, die nur XInput sprechen, gar nichts. |

Das Pad sendet bei jeder Zustandsänderung einen Input-Report. `pywinusb` übergibt ihn
als Liste von Bytewerten an eine Callback-Funktion.

## Aufbau des Reports

Byte 0 ist die Report-ID, das erste Nutzbyte ist also Byte 1. Dieses Skript liest die
Bytes 1 bis 7 und ignoriert alles danach; der vollständige Report ist länger, seine
übrigen Bytes wurden nicht untersucht.

| Byte | Inhalt |
|---|---|
| 0 | Report-ID |
| 1 | Aktions- und Schultertasten, Bitmaske *(gemessen)* |
| 2 | Menü- und Stick-Tasten, Bitmaske *(gemessen)* |
| 3 | Steuerkreuz als HAT-Schalter *(gemessen)* |
| 4 | linker Stick X *(gemessen)* |
| 5 | linker Stick Y *(gemessen)* |
| 6 | rechter Stick X *(gemessen)* |
| 7 | rechter Stick Y *(gemessen)* |

### Byte 1 — Aktions- und Schultertasten

| Maske | Switch-Taste | Abgebildet auf |
|---|---|---|
| `0x01` | Y (links) | `XUSB_GAMEPAD_X` |
| `0x02` | B (unten) | `XUSB_GAMEPAD_A` |
| `0x04` | A (rechts) | `XUSB_GAMEPAD_B` |
| `0x08` | X (oben) | `XUSB_GAMEPAD_Y` |
| `0x10` | L | `XUSB_GAMEPAD_LEFT_SHOULDER` |
| `0x20` | R | `XUSB_GAMEPAD_RIGHT_SHOULDER` |
| `0x40` | ZL | linker Trigger, 0 oder 255 |
| `0x80` | ZR | rechter Trigger, 0 oder 255 |

Die vier Aktionstasten sind bewusst **nicht** nach Beschriftung abgebildet. Nintendo
setzt B nach unten und A nach rechts, Microsoft umgekehrt — die Abbildung nach Position
hält Bildschirmeinblendung und Daumen deckungsgleich.

ZL und ZR sind an diesem Pad einfache Schalter, nicht analog. Die Trigger melden
deshalb immer nur 0 oder 255 — in einem Spiel mit feinfühligem Gas fühlt sich das wie
ein Ein-Aus-Pedal an. Das liegt an der Hardware, nicht an der Abbildung.

### Byte 2 — Menü- und Stick-Tasten

| Maske | Switch-Taste | Abgebildet auf |
|---|---|---|
| `0x01` | Minus | `XUSB_GAMEPAD_BACK` |
| `0x02` | Plus | `XUSB_GAMEPAD_START` |
| `0x04` | L3 (linker Stick-Klick) | `XUSB_GAMEPAD_LEFT_THUMB` |
| `0x08` | R3 (rechter Stick-Klick) | `XUSB_GAMEPAD_RIGHT_THUMB` |
| `0x10` – `0x80` | **nicht untersucht** | — |

Home und Capture wurden nicht verfolgt. Sie sind die naheliegenden Kandidaten für die
vier ungenutzten oberen Bits dieses Bytes — das ist aber eine Vermutung, keine Messung.
Wer sie findet: Home lässt sich auf `XUSB_GAMEPAD_GUIDE` legen, für Capture gibt es in
XInput keine Entsprechung.

### Byte 3 — Steuerkreuz

Ein gewöhnlicher HAT-Schalter mit acht Richtungen, im Uhrzeigersinn von oben in
45°-Schritten:

| Wert | Richtung | Wert | Richtung |
|---|---|---|---|
| `0x00` | oben | `0x04` | unten |
| `0x01` | oben + rechts | `0x05` | unten + links |
| `0x02` | rechts | `0x06` | links |
| `0x03` | unten + rechts | `0x07` | oben + links |

Die Mittelstellung wird üblicherweise als `0x08` gemeldet. Das Skript prüft nicht
darauf: Jeder Wert außerhalb von 0–7 läuft ins Leere und lässt das Steuerkreuz
losgelassen — das deckt die Mittelstellung und jeden unerwarteten Wert gleichermaßen ab.

### Bytes 4–7 — Analogsticks

| | |
|---|---|
| Wertebereich | 0–255, ein Byte je Achse *(gemessen)* |
| Mitte | 128 |
| X | 0 = ganz links, 255 = ganz rechts |
| Y | **0 = oben**, 255 = unten *(gemessen)* |

Die Y-Richtung ist die Stelle, über die man stolpert. HID zählt den Bildschirm hinunter,
XInput hinauf — beide Y-Achsen werden deshalb unterwegs negiert:

```python
gamepad.left_joystick(x_value=axis(data[4], deadzone),
                      y_value=-axis(data[5], deadzone))
```

`axis()` rechnet 0–255 in den XInput-Bereich −32767…32767 um, legt die Totzone um die
Mitte und streckt den Rest wieder auf den vollen Bereich, damit der Stick seine
Endlagen weiterhin erreicht. Die Funktion liefert nie −32768, und genau das macht die
Negierung oben gefahrlos.

## Das eigene Pad ausmessen

Wenn dein Modell anders meldet, findest du es mit `read_hid.py` heraus:

```
python read_hid.py
```

Es gibt pro geändertem Report eine Zeile aus, als Hex-Bytes. Dann:

1. **Zuerst nichts tun.** Die Zeile im Ruhezustand ist deine Ausgangslage. Notiere, was
   die Stick-Bytes in Mittelstellung anzeigen — stehen sie nicht auf 128, ist das genau
   das Driften, das die Totzone auffängt.
2. **Einzeln Tasten drücken** und mit der Ausgangslage vergleichen. Ein Bit kippt.
   Byte-Position und Bit ergeben eine Zeile für `BUTTON_MAP_LOW` oder
   `BUTTON_MAP_HIGH`.
3. **Das Steuerkreuz einmal umrunden**, alle acht Richtungen, und Byte 3 ablesen.
4. **Beide Sticks in die Endlagen drücken**, um Reihenfolge und Richtung der Achsen zu
   bestätigen.

Denk an den Versatz: Der zweite ausgegebene Wert ist Byte 1, weil Byte 0 die Report-ID
ist.

Ein Pull Request mit deinem Modell — Product-ID und alles, was abwich — ist willkommen.
