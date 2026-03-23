import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np
import pyvisa

# Change this to your actual VISA resource if you want a default.
DEFAULT_VISA = "USB0::2391::1031::MY00000000::INSTR"


class Keysight33210A_AM_GUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Keysight 33210A - AM Envelope Arb Output")
        self.resizable(False, False)

        self.rm = None
        self.instr = None
        self.worker = None
        self.stop_flag = threading.Event()

        self.build_ui()
        self.set_status("Not connected.")

    # ---------------- UI ----------------
    def build_ui(self):
        pad = {"padx": 10, "pady": 6}
        main = ttk.Frame(self)
        main.grid(row=0, column=0, **pad)

        self.visa_var = tk.StringVar(value=DEFAULT_VISA)
        self.fm_var = tk.StringVar(value="5")
        self.fc_var = tk.StringVar(value="250")
        self.duty_var = tk.StringVar(value="1.0")
        self.amp_var = tk.StringVar(value="5")
        self.reps_var = tk.StringVar(value="5")
        self.interval_var = tk.StringVar(value="2")

        ttk.Label(main, text="VISA Address").grid(row=0, column=0, sticky="w")
        ttk.Entry(main, textvariable=self.visa_var, width=44).grid(
            row=0, column=1, columnspan=3, sticky="we"
        )

        ttk.Label(main, text="fm (Hz)").grid(row=1, column=0, sticky="w")
        ttk.Entry(main, textvariable=self.fm_var, width=12).grid(row=1, column=1, sticky="w")

        ttk.Label(main, text="fc (Hz)").grid(row=1, column=2, sticky="w")
        ttk.Entry(main, textvariable=self.fc_var, width=12).grid(row=1, column=3, sticky="w")

        ttk.Label(main, text="Duty (0..1)").grid(row=2, column=0, sticky="w")
        ttk.Entry(main, textvariable=self.duty_var, width=12).grid(row=2, column=1, sticky="w")

        ttk.Label(main, text="Amplitude (Vpp)").grid(row=2, column=2, sticky="w")
        ttk.Entry(main, textvariable=self.amp_var, width=12).grid(row=2, column=3, sticky="w")

        ttk.Label(main, text="Repetitions").grid(row=3, column=0, sticky="w")
        ttk.Entry(main, textvariable=self.reps_var, width=12).grid(row=3, column=1, sticky="w")

        ttk.Label(main, text="Interval after run (s)").grid(row=3, column=2, sticky="w")
        ttk.Entry(main, textvariable=self.interval_var, width=12).grid(row=3, column=3, sticky="w")

        ops = ttk.Frame(main)
        ops.grid(row=4, column=0, columnspan=4, pady=(10, 0), sticky="we")

        self.connect_btn = ttk.Button(ops, text="CONNECT", command=self.connect, width=14)
        self.connect_btn.grid(row=0, column=0, padx=(0, 6))

        self.run_btn = ttk.Button(ops, text="RUN", command=self.run_sequence, width=14, state="disabled")
        self.run_btn.grid(row=0, column=1, padx=6)

        self.stop_btn = ttk.Button(ops, text="STOP", command=self.stop, width=14, state="disabled")
        self.stop_btn.grid(row=0, column=2, padx=6)

        self.idn_btn = ttk.Button(ops, text="IDN?", command=self.show_idn, width=10, state="disabled")
        self.idn_btn.grid(row=0, column=3, padx=(20, 6))

        self.disconnect_btn = ttk.Button(ops, text="DISC", command=self.disconnect, width=10, state="disabled")
        self.disconnect_btn.grid(row=0, column=4, padx=(6, 0))

        self.status_var = tk.StringVar(value="")
        ttk.Label(main, textvariable=self.status_var, foreground="blue").grid(
            row=5, column=0, columnspan=4, sticky="w", pady=(8, 0)
        )

        self.err_var = tk.StringVar(value="")
        ttk.Label(main, textvariable=self.err_var, foreground="brown").grid(
            row=6, column=0, columnspan=4, sticky="w"
        )

    # ---------------- VISA helpers ----------------
    def write(self, cmd):
        self.instr.write(cmd)

    def query(self, cmd):
        return self.instr.query(cmd).strip()

    def set_status(self, msg):
        self.status_var.set(msg)
        self.update_idletasks()

    def set_err(self, msg):
        self.err_var.set(msg)
        self.update_idletasks()

    def query_err(self):
        if not self.instr:
            self.set_err("")
            return
        try:
            self.set_err("FG error: " + self.query("SYST:ERR?"))
        except Exception as e:
            self.set_err(f"FG error: could not read error queue ({e})")

    # ---------------- connection ----------------
    def connect(self):
        visa = self.visa_var.get().strip()
        if not visa:
            messagebox.showerror("Connect Error", "Please enter a VISA address.")
            return

        try:
            self.rm = pyvisa.ResourceManager()
            self.instr = self.rm.open_resource(visa)
            self.instr.timeout = 10000
            self.instr.read_termination = "\n"
            self.instr.write_termination = "\n"

            idn = self.query("*IDN?")
            self.set_status(f"Connected: {idn}")
            self.query_err()

            self.connect_btn.config(state="disabled")
            self.run_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.idn_btn.config(state="normal")
            self.disconnect_btn.config(state="normal")

        except Exception as e:
            self.instr = None
            self.rm = None
            messagebox.showerror("Connect Error", str(e))

    def disconnect(self):
        self.stop()
        try:
            if self.instr:
                try:
                    self.instr.write("OUTP OFF")
                except Exception:
                    pass
                self.instr.close()
        finally:
            self.instr = None
            self.rm = None

        self.set_status("Disconnected.")
        self.set_err("")

        self.connect_btn.config(state="normal")
        self.run_btn.config(state="disabled")
        self.stop_btn.config(state="disabled")
        self.idn_btn.config(state="disabled")
        self.disconnect_btn.config(state="disabled")

    def show_idn(self):
        if not self.instr:
            return
        try:
            messagebox.showinfo("IDN", self.query("*IDN?"))
        except Exception as e:
            messagebox.showerror("IDN Error", str(e))

    # ---------------- waveform generation ----------------
    @staticmethod
    def burst_envelope_idx(n, N, duty=0.5):
        phase = n / N
        env = np.zeros_like(phase)

        active = phase < duty
        if duty > 0:
            ph = phase[active] / duty
            env[active] = 0.5 * (1 - np.cos(2 * np.pi * ph))
        return env

    @staticmethod
    def choose_num_points(fm, fc, max_points=8192):
        """
        Pick N automatically.
        We try to preserve the fc/fm ratio well enough while staying <= 8192.
        """
        carrier_cycles = fc / fm

        # Start with a decent points-per-carrier-cycle target.
        target_ppc = 80
        N = int(round(carrier_cycles * target_ppc))

        # Clamp to instrument range.
        N = max(64, min(max_points, N))

        # Make N an integer multiple of the number of carrier cycles when possible.
        # This helps keep the carrier clean if fc/fm is an integer.
        if abs(carrier_cycles - round(carrier_cycles)) < 1e-9:
            cc = int(round(carrier_cycles))
            if cc > 0:
                N = max(cc, (N // cc) * cc)
                N = max(64, min(max_points, N))

        return N

    def generate_am_waveform(self, fm, fc, duty=1.0):
        N = self.choose_num_points(fm, fc, max_points=8192)
        n = np.arange(N, dtype=float)

        envelope = self.burst_envelope_idx(n, N, duty)
        carrier_cycles = fc / fm
        carrier = np.sin(2 * np.pi * carrier_cycles * n / N)

        signal = envelope * carrier

        peak = np.max(np.abs(signal))
        if peak > 0:
            signal = signal / peak

        return signal, N

    # ---------------- instrument setup ----------------
    def require_arb_option(self):
        opt = self.query("*OPT?")
        # Manuals show 002 when arb option is installed.
        if "002" not in opt:
            raise RuntimeError(
                "This 33210A does not report Option 002 via *OPT?. "
                "Custom downloaded arbitrary waveforms require Option 002."
            )

    def configure_arb_am(self, fm, fc, amp_vpp, duty):
        self.require_arb_option()

        data, N = self.generate_am_waveform(fm, fc, duty)

        # Build DATA VOLATILE command using float points in [-1, +1].
        # This is slower than DATA:DAC but simpler and directly matches your Python signal.
        data_str = ", ".join(f"{x:.6f}" for x in data)

        self.write("*CLS")
        self.write("*RST")
        time.sleep(0.25)

        # Download waveform into volatile arb memory.
        self.write(f"DATA VOLATILE, {data_str}")

        # Select the waveform in volatile memory and output USER function.
        self.write("FUNC:USER VOLATILE")
        self.write("FUNC USER")

        # Frequency here is the repetition rate of the full arb waveform buffer.
        self.write(f"FREQ {fm}")
        self.write(f"VOLT {amp_vpp}")
        self.write("VOLT:OFFS 0")
        self.write("OUTP:LOAD INF")   # high impedance load assumption
        self.write("OUTP OFF")

        return N

    # ---------------- run logic ----------------
    def run_sequence(self):
        if not self.instr:
            return
        if self.worker and self.worker.is_alive():
            messagebox.showwarning("Busy", "A run is already in progress.")
            return

        try:
            fm = float(self.fm_var.get())
            fc = float(self.fc_var.get())
            duty = float(self.duty_var.get())
            amp = float(self.amp_var.get())
            repetitions = int(float(self.reps_var.get()))
            interval = float(self.interval_var.get())

            if fm <= 0 or fc <= 0 or amp <= 0 or repetitions <= 0:
                raise ValueError("fm, fc, amplitude, and repetitions must be > 0.")
            if not (0.0 < duty <= 1.0):
                raise ValueError("Duty must be in the range 0 < duty <= 1.")
            if interval < 0:
                raise ValueError("Interval must be >= 0.")

            # Useful sanity check
            if fc / fm > 5000:
                raise ValueError("fc/fm is extremely large. Reduce fc or increase fm.")

        except Exception as e:
            messagebox.showerror("Input Error", str(e))
            return

        self.stop_flag.clear()

        self.connect_btn.config(state="disabled")
        self.run_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.disconnect_btn.config(state="disabled")
        self.idn_btn.config(state="disabled")

        def worker():
            try:
                N = self.configure_arb_am(fm, fc, amp, duty)
                run_time = repetitions / fm

                self.set_status(
                    f"Loaded arb: fm={fm} Hz, fc={fc} Hz, duty={duty}, "
                    f"amp={amp} Vpp, points={N}, run_time={run_time:.3f} s"
                )
                self.query_err()

                # ARB burst is not supported on 33210A, so we do the repetition timing in software.
                self.write("OUTP ON")
                t0 = time.time()

                while (time.time() - t0) < run_time:
                    if self.stop_flag.is_set():
                        break
                    elapsed = time.time() - t0
                    done = int(elapsed * fm)
                    if done > repetitions:
                        done = repetitions
                    self.set_status(
                        f"Output running... {done}/{repetitions} envelope repetitions"
                    )
                    time.sleep(0.05)

                self.write("OUTP OFF")

                if interval > 0 and not self.stop_flag.is_set():
                    self.set_status(f"Waiting interval: {interval:.2f} s")
                    t1 = time.time()
                    while (time.time() - t1) < interval:
                        if self.stop_flag.is_set():
                            break
                        time.sleep(0.05)

                if self.stop_flag.is_set():
                    self.set_status("Stopped.")
                else:
                    self.set_status("Done.")

            except Exception as e:
                self.set_status("Error.")
                messagebox.showerror("Run Error", str(e))
            finally:
                try:
                    if self.instr:
                        self.instr.write("OUTP OFF")
                except Exception:
                    pass

                self.query_err()

                if self.instr:
                    self.run_btn.config(state="normal")
                    self.disconnect_btn.config(state="normal")
                    self.idn_btn.config(state="normal")
                    self.connect_btn.config(state="disabled")
                else:
                    self.connect_btn.config(state="normal")

                self.stop_btn.config(state="disabled")

        self.worker = threading.Thread(target=worker, daemon=True)
        self.worker.start()

    def stop(self):
        self.stop_flag.set()
        if self.instr:
            try:
                self.instr.write("OUTP OFF")
            except Exception:
                pass

        if self.instr:
            self.run_btn.config(state="normal")
            self.disconnect_btn.config(state="normal")
            self.idn_btn.config(state="normal")
            self.connect_btn.config(state="disabled")
        else:
            self.connect_btn.config(state="normal")

        self.stop_btn.config(state="disabled")
        self.set_status("Stopping...")
        self.query_err()


if __name__ == "__main__":
    app = Keysight33210A_AM_GUI()
    app.mainloop()
