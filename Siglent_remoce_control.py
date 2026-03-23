import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import pyvisa

DEFAULT_VISA = ""   # leave blank or write AUTO to auto-detect


class SiglentSDG2082XGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Siglent SDG2082X Burst Controller")
        self.resizable(False, False)

        self.rm = None
        self.instr = None
        self.worker = None
        self.stop_flag = threading.Event()

        self.progress_var = tk.DoubleVar(value=0.0)
        self._run_total_time = 0.0

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

    def build_ui(self):
        pad = {"padx": 10, "pady": 6}
        main = ttk.Frame(self)
        main.grid(row=0, column=0, **pad)

        ttk.Label(main, text="VISA Address").grid(row=0, column=0, sticky="w")
        self.visa_var = tk.StringVar(value=DEFAULT_VISA)
        ttk.Entry(main, textvariable=self.visa_var, width=58).grid(row=0, column=1, columnspan=5, sticky="we")

        self.freq_var = tk.StringVar(value="5")
        self.dur_var = tk.StringVar(value="3")
        self.amp_var = tk.StringVar(value="2")
        self.int_var = tk.StringVar(value="2")
        self.reps_var = tk.StringVar(value="5")
        self.chan_var = tk.StringVar(value="1")

        ttk.Label(main, text="Freq (Hz)").grid(row=1, column=0, sticky="w")
        ttk.Entry(main, textvariable=self.freq_var, width=10).grid(row=1, column=1, sticky="w")

        ttk.Label(main, text="Duration (s)").grid(row=1, column=2, sticky="w")
        ttk.Entry(main, textvariable=self.dur_var, width=10).grid(row=1, column=3, sticky="w")

        ttk.Label(main, text="Amplitude (Vpp)").grid(row=2, column=0, sticky="w")
        ttk.Entry(main, textvariable=self.amp_var, width=10).grid(row=2, column=1, sticky="w")

        ttk.Label(main, text="Interval (s)").grid(row=2, column=2, sticky="w")
        ttk.Entry(main, textvariable=self.int_var, width=10).grid(row=2, column=3, sticky="w")

        ttk.Label(main, text="Channel").grid(row=3, column=0, sticky="w")
        ttk.Entry(main, textvariable=self.chan_var, width=10).grid(row=3, column=1, sticky="w")

        ttk.Label(main, text="Reps").grid(row=3, column=2, sticky="w")
        ttk.Entry(main, textvariable=self.reps_var, width=10).grid(row=3, column=3, sticky="w")

        ops = ttk.Frame(main)
        ops.grid(row=4, column=0, columnspan=6, pady=(10, 0), sticky="we")

        self.connect_btn = ttk.Button(ops, text="CONNECT", command=self.connect, width=14)
        self.connect_btn.grid(row=0, column=0, padx=(0, 6))

        self.run_btn = ttk.Button(ops, text="RUN", command=self.run_sequence, width=14, state="disabled")
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
        prog.grid(row=5, column=0, columnspan=6, sticky="we", pady=(10, 0))
        ttk.Label(prog, text="Progress").grid(row=0, column=0, sticky="w")

        self.bar_container = tk.Frame(prog, width=360, height=18)
        self.bar_container.grid(row=0, column=1, padx=(8, 0), sticky="w")
        self.bar_container.grid_propagate(False)

        self.pbar = ttk.Progressbar(
            self.bar_container,
            variable=self.progress_var,
            maximum=100.0,
            length=360,
            style="Idle.Horizontal.TProgressbar",
        )
        self.pbar.place(x=0, y=0, width=360, height=18)

        self.timeline = tk.Canvas(self.bar_container, width=360, height=18, highlightthickness=0, bd=0)
        self.timeline.place(x=0, y=0, width=360, height=18)

        self.status_var = tk.StringVar(value="")
        ttk.Label(main, textvariable=self.status_var, foreground="blue").grid(
            row=6, column=0, columnspan=6, sticky="w", pady=(6, 0)
        )

        self.err_var = tk.StringVar(value="")
        ttk.Label(main, textvariable=self.err_var, foreground="brown").grid(
            row=7, column=0, columnspan=6, sticky="w"
        )

    def write(self, cmd: str):
        self.instr.write(cmd)

    def query(self, cmd: str) -> str:
        return self.instr.query(cmd).strip()

    def channel_name(self, channel: int) -> str:
        return f"C{channel}"

    def set_status(self, msg):
        self.status_var.set(msg)
        self.update_idletasks()

    def set_err(self, msg):
        self.err_var.set(msg)
        self.update_idletasks()

    def set_progress(self, pct: float):
        self.progress_var.set(max(0.0, min(100.0, pct)))
        self.update_idletasks()

    def query_err(self):
        try:
            err = self.query(":SYST:ERR?")
            self.set_err("FG error: " + err)
        except Exception:
            self.set_err("")

    def auto_find_siglent(self):
        try:
            rm = pyvisa.ResourceManager()
            resources = rm.list_resources()
        except Exception as e:
            return None, None, f"Could not open VISA resource manager: {e}"

        checked = []

        for resource in resources:
            try:
                inst = rm.open_resource(resource)
                inst.timeout = 2000
                inst.write_termination = "\n"
                inst.read_termination = "\n"

                idn = inst.query("*IDN?").strip()
                checked.append(f"{resource} -> {idn}")

                if "SIGLENT" in idn.upper() and "SDG" in idn.upper():
                    inst.close()
                    return resource, idn, "\n".join(checked)

                inst.close()

            except Exception as e:
                checked.append(f"{resource} -> could not query ({e})")

        return None, None, "\n".join(checked)

    def connect(self):
        visa = self.visa_var.get().strip()

        if visa == "" or visa.upper() == "AUTO":
            addr, idn, log_text = self.auto_find_siglent()

            if not addr:
                messagebox.showwarning(
                    "Not found",
                    "No Siglent SDG instrument found.\n\nScan result:\n\n" + (log_text or "No resources found.")
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
            if "SIGLENT" not in idn.upper() or "SDG" not in idn.upper():
                raise RuntimeError(f"Connected instrument is not a Siglent SDG: {idn}")

        except Exception as e:
            self.instr = None
            self.rm = None
            messagebox.showerror("Connect Error", str(e))
            return

        self.set_status(f"Connected: {idn}")
        self.set_err("")
        self.set_progress(0.0)
        self.pbar.configure(style="Idle.Horizontal.TProgressbar")
        self._draw_timeline_static(0, 0, 0)

        self.connect_btn.config(state="disabled")
        self.run_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.idn_btn.config(state="normal")
        self.disconnect_btn.config(state="normal")

    def disconnect(self):
        self.stop()
        try:
            if self.instr:
                try:
                    channel = int(float(self.chan_var.get()))
                except Exception:
                    channel = 1
                try:
                    self.write(f"{self.channel_name(channel)}:OUTP OFF")
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
        self._draw_timeline_static(0, 0, 0)

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

    def _draw_timeline_static(self, reps: int, dur: float, interval: float):
        self.timeline.delete("all")
        w = int(self.timeline.winfo_width() or 360)
        h = int(self.timeline.winfo_height() or 18)

        total = reps * (dur + interval)
        self._run_total_time = total
        if total <= 0:
            return

        for i in range(reps):
            seg = dur + interval
            bx0 = (i * seg) / total * w
            bx1 = ((i * seg) + dur) / total * w
            self.timeline.create_rectangle(bx0, 1, bx1, h - 1, fill="#000000", stipple="gray12", outline="")
            ex = ((i + 1) * seg) / total * w
            self.timeline.create_line(ex, 1, ex, h - 1, fill="#555555")

        self.timeline.create_line(0, 1, 0, h - 1, fill="#555555")

    def _draw_timeline_marker(self, elapsed_s: float):
        self.timeline.delete("marker")
        self.timeline.delete("elapsed")

        w = int(self.timeline.winfo_width() or 360)
        h = int(self.timeline.winfo_height() or 18)
        total = self._run_total_time
        if total <= 0:
            return

        elapsed_s = max(0.0, min(total, elapsed_s))
        x = (elapsed_s / total) * w

        self.timeline.create_rectangle(
            0, 1, x, h - 1,
            fill="#4da6ff",
            stipple="gray25",
            outline="",
            tags="elapsed",
        )
        self.timeline.create_line(x, 1, x, h - 1, fill="#1f77b4", width=2, tags="marker")

    def configure_fg(self, freq: float, dur: float, amp: float, channel: int):
        ch = self.channel_name(channel)
        cycles = max(1, int(round(freq * dur)))

        self.write("*CLS")
        self.write("*RST")
        time.sleep(0.8)

        self.write(f"{ch}:BSWV WVTP,SINE")
        self.write(f"{ch}:BSWV FRQ,{freq}")
        self.write(f"{ch}:BSWV AMP,{amp}")
        self.write(f"{ch}:BSWV OFST,0")
        self.write(f"{ch}:BSWV PHSE,0")

        self.write(f"{ch}:BTWV STATE,ON")
        self.write(f"{ch}:BTWV GATE_NCYC,NCYC")
        self.write(f"{ch}:BTWV TIME,{cycles}")
        self.write(f"{ch}:BTWV TRSR,MAN")

        self.write(f"{ch}:OUTP ON")

        return cycles

    def run_sequence(self):
        if not self.instr:
            return
        if self.worker and self.worker.is_alive():
            messagebox.showwarning("Busy", "A run is already in progress.")
            return

        try:
            freq = float(self.freq_var.get())
            dur = float(self.dur_var.get())
            amp = float(self.amp_var.get())
            interval = float(self.int_var.get())
            reps = int(float(self.reps_var.get()))
            channel = int(float(self.chan_var.get()))

            if freq <= 0 or dur <= 0 or amp <= 0 or reps <= 0 or interval < 0:
                raise ValueError("Values must be positive (interval can be 0).")
            if channel not in (1, 2):
                raise ValueError("Channel must be 1 or 2.")

        except Exception as e:
            messagebox.showerror("Input Error", str(e))
            return

        self.stop_flag.clear()
        self.set_progress(0.0)
        self.pbar.configure(style="Run.Horizontal.TProgressbar")

        self._draw_timeline_static(reps, dur, interval)
        self._draw_timeline_marker(0.0)

        self.connect_btn.config(state="disabled")
        self.run_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.disconnect_btn.config(state="disabled")
        self.idn_btn.config(state="disabled")

        total_time = reps * (dur + interval)

        def worker():
            start_time = time.time()
            ch = self.channel_name(channel)

            try:
                cycles = self.configure_fg(freq, dur, amp, channel)
                self.set_status(f"Configured: CH{channel} | {freq} Hz, {dur} s ({cycles} cycles), {amp} Vpp")

                for i in range(1, reps + 1):
                    if self.stop_flag.is_set():
                        break

                    self.set_status(f"Burst {i}/{reps}")
                    self.write(f"{ch}:BTWV MTRIG")

                    segment = dur + interval
                    t0 = time.time()
                    while (time.time() - t0) < segment:
                        if self.stop_flag.is_set():
                            break
                        elapsed = time.time() - start_time
                        pct = (elapsed / total_time) * 100.0 if total_time > 0 else 100.0
                        self.set_progress(pct)
                        self._draw_timeline_marker(elapsed)
                        time.sleep(0.05)

                if not self.stop_flag.is_set():
                    self.set_progress(100.0)
                    self._draw_timeline_marker(total_time)
                    self.set_status("Done.")
                    self.pbar.configure(style="Done.Horizontal.TProgressbar")
                else:
                    self.set_status("Stopped.")
                    self.pbar.configure(style="Idle.Horizontal.TProgressbar")

            except Exception as e:
                self.set_status("Error.")
                self.pbar.configure(style="Idle.Horizontal.TProgressbar")
                messagebox.showerror("Run Error", str(e))

            finally:
                try:
                    if self.instr:
                        self.write(f"{ch}:OUTP OFF")
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
                channel = int(float(self.chan_var.get()))
            except Exception:
                channel = 1
            try:
                self.write(f"{self.channel_name(channel)}:OUTP OFF")
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
        self.pbar.configure(style="Idle.Horizontal.TProgressbar")
        self.query_err()


if __name__ == "__main__":
    app = SiglentSDG2082XGUI()
    app.mainloop()
