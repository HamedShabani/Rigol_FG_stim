# Magnetic Flux Calibration Tool – Operator Quick Guide (SOP)

## Purpose

This tool calculates the **Function Generator Voltage (Vpp)** required to achieve a desired magnetic field **B (mT)** using pre-measured calibration data.

⚠️ The voltage shown is **FG voltage BEFORE the amplifier**.
⚠️ The amplifier gain is fixed and must NOT be changed.

---

## ⚠️ Safety Attention

❗ **Do NOT enter or apply more than 5 Vpp from the Function Generator.**
Higher voltage may damage the amplifier.

---

## How to Use

1. Open the program (.py or HTML file).

2. Select the **Frequency (Hz)**:

   * 5 Hz
   * 10 Hz

3. Select the Mode:

   * **B → FG Voltage** → Find required FG voltage for a target field.
   * **FG Voltage → B** → Estimate magnetic field from a known FG voltage.

4. Enter the value:

   * Target B (mT) **or**
   * FG Voltage (Vpp)

5. Press **Compute**.

The tool will display:

* Required FG Voltage (Vpp)
* Expected Coil Current (App)
* Estimated Magnetic Flux (mT)

---

## Important Notes

* Operator should ONLY adjust **FG Voltage** on the generator.
* Do NOT change amplifier gain.
* Do NOT exceed **5 Vpp**.
* Results are based on interpolation of calibration data.
* Values outside measured range require **Allow Extrapolation**.

---

## Example

Target field = **5 mT** at **10 Hz**
→ Select 10 Hz
→ Mode = B → FG Voltage
→ Enter 5
→ Press Compute

---

## If Something Looks Wrong

* Check correct frequency is selected.
* Verify FG output is enabled.
* Confirm calibration file/version.
* Ask Hamed if unsure.
