import time
import pyvisa

FG = "USB0::0x1AB1::0x0642::DG1ZA273904603::INSTR"

def q(inst, cmd):
    return inst.query(cmd).strip()

def w(inst, cmd):
    inst.write(cmd)

def drain_errors(inst, label="FG"):
    # Read a few errors (if any). Some devices keep a queue.
    errs = []
    for _ in range(10):
        try:
            e = q(inst, ":SYST:ERR?")
        except Exception:
            break
        if e.startswith("+0") or e.startswith("0"):
            break
        errs.append(e)
    if errs:
        print(f"{label} errors:")
        for e in errs:
            print("  ", e)

def stim_burst_ch1(inst, freq_hz, amp_vpp, duration_s, reps, isi_s=1.0):
    cycles = max(1, int(round(freq_hz * duration_s)))  # duration via cycles
    print("Burst cycles:", cycles)

    # Clean start
    w(inst, "*CLS")
    w(inst, "*RST")   # optional but makes tests repeatable
    time.sleep(0.2)

    # CH1 sine setup
    w(inst, ":SOUR1:FUNC SIN")
    w(inst, f":SOUR1:FREQ {freq_hz}")
    w(inst, f":SOUR1:VOLT {amp_vpp}")       # typically Vpp on DG1000Z
    w(inst, ":SOUR1:VOLT:OFFS 0")
    w(inst, ":SOUR1:PHAS 0")

    # Burst setup (triggered burst)
    w(inst, ":SOUR1:BURS:STAT ON")
    w(inst, ":SOUR1:BURS:MODE TRIG")
    w(inst, f":SOUR1:BURS:NCYC {cycles}")

    # Trigger from bus (so laptop can fire it)
    w(inst, ":TRIG1:SOUR BUS")






    # Output on
    w(inst, ":OUTP1 ON")

    drain_errors(inst)

    # Fire bursts
    for i in range(1, reps + 1):
        w(inst, "*TRG")
        print(f"Triggered {i}/{reps}")
        time.sleep(duration_s + isi_s)

    # Output off
    w(inst, ":OUTP1 OFF")
    drain_errors(inst)

def main():
    rm = pyvisa.ResourceManager()
    fg = rm.open_resource(FG)
    fg.timeout = 5000
    fg.read_termination = "\n"
    fg.write_termination = "\n"

    print("Connected:", q(fg, "*IDN?"))
    stim_burst_ch1(
        fg,
        freq_hz=5.0,
        amp_vpp=2.0,
        duration_s=3.0,
        reps=5,
        isi_s=2.0
    )

if __name__ == "__main__":
    main()
