# Rigol DG1022Z Burst Stimulation Controller

Simple Python GUI to control a **Rigol DG1022Z Function Generator** for
repeatable burst stimulation with synchronized TTL output via **SYNC OUT**.

Designed for lab workflows where operators need an easy and safe interface.

---

## ✨ Features

- Auto-connect to DG1022Z (no manual VISA typing required)
- Burst stimulation control:
  - Frequency
  - Duration
  - Amplitude
  - Interval
  - Repetitions
- Real-time progress bar + timeline
- Safe STOP (immediate output OFF)
- SYNC OUT TTL automatically aligned with stimulation

---

## ⚙️ Requirements

### Hardware
- Rigol DG1022Z
- USB data cable

### Software
- Python 3.10+
- NI-VISA (install via Rigol UltraSigma)

Install Python packages:

```bash
pip install pyvisa pyvisa-py
```

---

## 🚀 Run

```bash
python rigol_gui.py
```

Workflow:

```
CONNECT → RUN → STOP → DISC
```

If the VISA field is blank or set to `AUTO`, the software will automatically
detect the DG1022Z using `*IDN?`.

---

## ▶️ Parameters

| Parameter | Description |
|---|---|
| Freq (Hz) | Sine frequency |
| Duration (s) | Burst length |
| Amplitude (Vpp) | Output voltage |
| Interval (s) | Pause between bursts |
| Reps | Number of bursts |

Progress bar:
- 🔵 Blue = Running
- 🟢 Green = Finished
- ⚪ Grey = Idle

---

## 🔌 SYNC Output

Rear **SYNC OUT** provides a TTL signal synchronized with burst stimulation.
No extra configuration required.

---

## 🧪 UltraSigma (Manual Mode)

UltraSigma can be used to:
- Manually test settings
- Inspect SCPI commands

⚠️ Do **not** run UltraSigma at the same time as this GUI.

---

## 🛠️ Troubleshooting

**Device not found**
- Check USB cable
- Install NI-VISA
- Close UltraSigma

**No output**
- Verify amplitude > 0
- Press RUN
- Check cables

**Front panel locked**
Normal during remote control. Press DISC to release.

---

## ⚠️ Safety

- Verify voltage before connecting to experiments
- Do not change cables during active output
- Ensure proper grounding

---

## License
MIT (or your chosen license)
