import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import pyvisa

DEFAULT_VISA = "USB0::0x0957::0x0407::MY44008868::INSTR"  # replace if needed


class KeysightAMGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Keysight 33210A AM Controller")
        self.resizable(False, False)

        self.rm = None
        self.instr = None
        self.worker = None
        self.stop_flag = threading.Event()

        self.progress_var = tk.DoubleVar(value=0.0)
        self.status_var = tk.StringVar(value="")
        self.err_var = tk.StringVar(value="")

        style = ttk.Style(self)
        style.configure(
            "Idle.Horizontal.TProgressbar",
            troughcolor="#e6e6e6",
            background="#9aa5b1",
            lightcolor="#9aa5b1",
            darkcolor="#9aa5b1",
            bordercolor="#e6e6e6",
        )
        style.configure(
            "Run.Horizontal.TProgressbar",
            troughcolor="#e6e6e6",
            background="#0078d7",
            lightcolor="#0078d7",
            darkcolor="#0078d7",
            bordercolor="#e6e6e6",
        )
        style.configure(
            "Done.Horizontal.TProgressbar",
            troughcolor="#e6e6e6",
            background="#2ecc71",
            lightcolor="#2ecc71",
            darkcolor="#2ecc71",
            bordercolor="#e6e6e6",
        )

        self.build_ui()
        self.set_status("Not connected.")
        self.set_progress(0.0)

    # ---------------- UI ----------------
    def build_ui(self):
        pad = {"padx": 10, "pady": 6}
        main = ttk.Frame(self)
        main.grid(row=0, column=0, **pad)

        ttk.Label(main, text="VISA Address").grid(row=0, column=0, sticky="w")
        self.visa_var = tk.StringVar(value=DEFAULT_VISA)
        ttk.Entry(main, textvariable=self.visa_var, width=54).grid(
            row=0, column=1, columnspan=5, sticky="we"
        )

        self.carrier_var = tk.StringVar(value="250")
        self.mod_var = tk.StringVar(value="5")
        self.amp_var = tk.StringVar(value="1")
        self.depth_var = tk.StringVar(value="100")

        ttk.Label(main, text="Carrier Freq (Hz)").grid(row=1, column=0, sticky="w")
        ttk.Entry(main, textvariable=self.carrier_var, width=12).grid(row=1, column=1, sticky="w")

        ttk.Label(main, text="Mod Freq (Hz)").grid(row=1, column=2, sticky="w")
        ttk.Entry(main, textvariable=self.mod_var, width=12).grid(row=1, column=3, sticky="w")

        ttk.Label(main, text="Amplitude (Vpp)").grid(row=2, column=0, sticky="w")
        ttk.Entry(main, textvariable=self.amp_var, width=12).grid(row=2, column=1, sticky="w")

        ttk.Label(main, text="AM Depth (%)").grid(row=2, column=2, sticky="w")
        ttk.Entry(main, textvariable=self.depth_var, width=12).grid(row=2, column=3, sticky="w")

        ops = ttk.Frame(main)
        ops.grid(row=3, column=0, columnspan=6, pady=(10, 0), sticky="we")

        self.connect_btn = ttk.Button(ops, text="CONNECT", command=self.connect, width=14)
        self.connect_btn.grid(row=0, column=0, padx=(0, 6))

        self.run_btn = ttk.Button(ops, text="APPLY", command=self.apply_am, width=14, state="disabled")
        self.run_btn.grid(row=0, column=1, padx=6)

        self.stop_btn = ttk.Button(ops, text="STOP", command=self.stop, width=14, state="disabled")
        self.stop_btn.grid(row=0, column=2, padx=6)

        ops.columnconfigure(3, weight=1)
        ttk.Label(ops, text="").grid(row=0, column=3, sticky="we")

        self.idn_btn = ttk.Button(ops, text="IDN?", command=self.show_idn, width=8, state="disabled")
        self.idn_btn.grid(row=0, column=4, padx=(18, 6))

        self.disconnect_btn = ttk.Button(ops, text="DISC", command=self.disconnect, width=8, state="disabled")
        self.disconnect_btn.grid(row=0, column=5, padx=(6, 0))

        prog = ttk.Frame(main)
        prog.grid(row=4, column=0, columnspan=6, sticky="we", pady=(10, 0))
        ttk.Label(prog, text="Progress").grid(row=0, column=0, sticky="w")

        self.pbar = ttk.Progressbar(
            prog,
            variable=self.progress_var,
            maximum=100.0,
            length=360,
            style="Idle.Horizontal.TProgressbar",
        )
        self.pbar.grid(row=0, column=1, padx=(8, 0), sticky="w")

        prog.columnconfigure(1, weight=1)

        ttk.Label(main, textvariable=self.status_var, foreground="blue").grid(
            row=5, column=0, columnspan=6, sticky="w", pady=(6, 0)
        )
        ttk.Label(main, textvariable=self.err_var, foreground="brown").grid(
            row=6, column=0, columnspan=6, sticky="w"
        )

    # ---------------- Thread-safe UI helpers ----------------
    def ui(self, fn, *args, **kwargs):
        self.after(0, lambda: fn(*args, **kwargs))

    def set_status(self, msg):
        self.status_var.set(msg)

    def set_err(self, msg):
        self.err_var.set(msg)

    def set_progress(self, pct: float):
        self.progress_var.set(max(0.0, min(100.0, pct)))

    def set_buttons_connected(self):
        self.connect_btn.config(state="disabled")
        self.run_btn.config(state="normal")
        self.stop_btn.config(state="normal")
        self.idn_btn.config(state="normal")
        self.disconnect_btn.config(state="normal")

    def set_buttons_disconnected(self):
        self.connect_btn.config(state="normal")
        self.run_btn.config(state="disabled")
        self.stop_btn.config(state="disabled")
        self.idn_btn.config(state="disabled")
        self.disconnect_btn.config(state="disabled")

    def set_buttons_running(self):
        self.connect_btn.config(state="disabled")
        self.run_btn.config(state="disabled")
        self.stop_btn.config(state="disabled")
        self.idn_btn.config(state="disabled")
        self.disconnect_btn.config(state="disabled")

    # ---------------- VISA helpers ----------------
    def write(self, cmd):
        self.instr.write(cmd)

    def query(self, cmd):
        return self.instr.query(cmd).strip()

    def drain_errors(self):
        if not self.instr:
            return []
        errs = []
        try:
            for _ in range(10):
                e = self.query("SYST:ERR?")
                errs.append(e)
                if e.startswith("+0") or e.startswith("0,"):
                    break
        except Exception as ex:
            errs.append(f"(could not read error queue: {ex})")
        return errs

    def show_last_error(self):
        errs = self.drain_errors()
        meaningful = [e for e in errs if not (e.startswith("+0") or e.startswith("0,"))]
        if meaningful:
            self.ui(self.set_err, "FG error: " + " | ".join(meaningful))
        else:
            self.ui(self.set_err, "")

    def write_checked(self, cmd, allow_warnings=False):
        self.write(cmd)
        errs = self.drain_errors()
        meaningful = [e for e in errs if not (e.startswith("+0") or e.startswith("0,"))]
        if meaningful and not allow_warnings:
            raise RuntimeError(f"{cmd} -> {' | '.join(meaningful)}")

    # ---------------- Auto-find Keysight 33210A ----------------
    def auto_find_33210a(self):
        rm = pyvisa.ResourceManager()
        for r in rm.list_resources():
            try:
                inst = rm.open_resource(r)
                inst.timeout = 1500
                inst.read_termination = "\n"
                inst.write_termination = "\n"
                idn = inst.query("*IDN?").strip()
                inst.close()
                if ("Keysight" in idn or "Agilent" in idn or "HEWLETT-PACKARD" in idn) and "33210A" in idn:
                    return r, idn
            except Exception:
                pass
        return None, None

    # ---------------- Connection ----------------
    def connect(self):
        visa = self.visa_var.get().strip()
        if visa == "" or visa.upper() == "AUTO":
            addr, idn = self.auto_find_33210a()
            if not addr:
                messagebox.showwarning(
                    "Not found",
                    "Keysight 33210A not found.\n\nCheck:\n- USB cable\n- VISA installed\n- instrument powered on"
                )
                return
            self.visa_var.set(addr)
            visa = addr
            self.set_status(f"Found: {idn}")

        try:
            self.rm = pyvisa.ResourceManager()
            self.instr = self.rm.open_resource(visa)
            self.instr.timeout = 5000
            self.instr.read_termination = "\n"
            self.instr.write_termination = "\n"
            idn = self.query("*IDN?")
        except Exception as e:
            messagebox.showerror("Connect Error", str(e))
            self.instr = None
            self.rm = None
            return

        self.set_status(f"Connected: {idn}")
        self.show_last_error()
        self.set_progress(0.0)
        self.pbar.configure(style="Idle.Horizontal.TProgressbar")
        self.set_buttons_connected()

    def disconnect(self):
        self.stop_flag.set()
        try:
            if self.instr:
                try:
                    self.instr.write("AM:STAT OFF")
                    self.instr.write("OUTP OFF")
                except Exception:
                    pass
                self.instr.close()
        finally:
            self.instr = None
            self.rm = None

        self.set_status("Disconnected.")
        self.set_err("")
        self.set_progress(0.0)
        self.pbar.configure(style="Idle.Horizontal.TProgressbar")
        self.set_buttons_disconnected()

    def show_idn(self):
        if not self.instr:
            return
        try:
            messagebox.showinfo("IDN", self.query("*IDN?"))
        except Exception as e:
            messagebox.showerror("IDN Error", str(e))

    # ---------------- 33210A AM config ----------------
    def configure_am(self, carrier_freq, mod_freq, amp, depth):
        self.write("*CLS")
        time.sleep(0.1)

        # Optional reset
        self.write("*RST")
        time.sleep(0.5)

        # Carrier
        self.write_checked("FUNC SIN")
        self.write_checked(f"FREQ {carrier_freq}")
        self.write_checked(f"VOLT {amp}")
        self.write_checked("VOLT:OFFS 0")

        # Internal AM
        self.write_checked("AM:STAT OFF", allow_warnings=True)
        self.write_checked("AM:SOUR INT")
        self.write_checked("AM:INT:FUNC SIN")
        self.write_checked(f"AM:INT:FREQ {mod_freq}")
        self.write_checked(f"AM:DEPT {depth}")

        # Enable output
        self.write_checked("AM:STAT ON")
        self.write_checked("OUTP ON")

    # ---------------- Apply logic ----------------
    def apply_am(self):
        if not self.instr:
            return
        if self.worker and self.worker.is_alive():
            messagebox.showwarning("Busy", "An operation is already in progress.")
            return

        try:
            carrier = float(self.carrier_var.get())
            mod = float(self.mod_var.get())
            amp = float(self.amp_var.get())
            depth = float(self.depth_var.get())

            if carrier <= 0:
                raise ValueError("Carrier frequency must be > 0.")
            if mod <= 0:
                raise ValueError("Modulation frequency must be > 0.")
            if amp <= 0:
                raise ValueError("Amplitude must be > 0.")
            if not (0 <= depth <= 120):
                raise ValueError("AM depth must be between 0 and 120.")
        except Exception as e:
            messagebox.showerror("Input Error", str(e))
            return

        self.stop_flag.clear()
        self.set_progress(0.0)
        self.pbar.configure(style="Run.Horizontal.TProgressbar")
        self.set_buttons_running()

        def worker():
            try:
                for pct in (10, 25, 45, 65, 85):
                    if self.stop_flag.is_set():
                        break
                    self.ui(self.set_progress, pct)
                    time.sleep(0.08)

                if self.stop_flag.is_set():
                    self.ui(self.set_status, "Stopped.")
                    self.ui(self.pbar.configure, style="Idle.Horizontal.TProgressbar")
                    return

                self.configure_am(carrier, mod, amp, depth)
                self.show_last_error()

                self.ui(self.set_progress, 100.0)
                self.ui(self.set_status,
                        f"AM active: Carrier={carrier} Hz | Mod={mod} Hz | Amp={amp} Vpp | Depth={depth}%")
                self.ui(self.pbar.configure, style="Done.Horizontal.TProgressbar")

            except Exception as e:
                self.ui(self.set_status, "Error.")
                self.ui(self.pbar.configure, style="Idle.Horizontal.TProgressbar")
                self.ui(messagebox.showerror, "Apply Error", str(e))

            finally:
                self.show_last_error()
                if self.instr:
                    self.ui(self.set_buttons_connected)
                else:
                    self.ui(self.set_buttons_disconnected)

        self.worker = threading.Thread(target=worker, daemon=True)
        self.worker.start()

    def stop(self):
        self.stop_flag.set()
        if self.instr:
            try:
                self.instr.write("AM:STAT OFF")
                self.instr.write("OUTP OFF")
            except Exception:
                pass

        if self.instr:
            self.set_buttons_connected()
        else:
            self.set_buttons_disconnected()

        self.set_status("AM stopped, output off.")
        self.pbar.configure(style="Idle.Horizontal.TProgressbar")
        self.set_progress(0.0)
        self.show_last_error()


if __name__ == "__main__":
    app = KeysightAMGUI()
    app.mainloop()
