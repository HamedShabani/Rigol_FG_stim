import tkinter as tk
from tkinter import ttk, messagebox

# =====================================================
# Calibration Tables
# Operator only changes FG voltage.
# =====================================================

DATA = {
    5: {
        "V": [0.5,1,1.5,2,2.5,3,3.5,4],
        "I": [1.8,3.6,5.3,7.1,9.2,11.03,12.8,14.6],
        "B": [7,14.2,21.3,28.5,35.7,42.8,49.6,56.6],
    },
    10: {
        "V": [0.5,1,1.5,2,2.5,3,3.5,4],
        "I": [1.8,3.1,4.5,5.9,7.3,8.7,10.1,11.7],
        "B": [5.7,11.3,17.03,22.5,28.6,34.1,39.6,45.6],
    }
}

# =====================================================
# Linear interpolation (pure python)
# =====================================================

def interp(x, xp, fp, allow_extrap=False):

    if x < xp[0]:
        if not allow_extrap:
            return None
        x0,x1 = xp[0],xp[1]
        y0,y1 = fp[0],fp[1]
        return y0 + (y1-y0)*(x-x0)/(x1-x0)

    if x > xp[-1]:
        if not allow_extrap:
            return None
        x0,x1 = xp[-2],xp[-1]
        y0,y1 = fp[-2],fp[-1]
        return y0 + (y1-y0)*(x-x1)/(x1-x0)

    for i in range(len(xp)-1):
        if xp[i] <= x <= xp[i+1]:
            x0,x1 = xp[i],xp[i+1]
            y0,y1 = fp[i],fp[i+1]
            return y0 + (y1-y0)*(x-x0)/(x1-x0)

    return None

# =====================================================
# GUI
# =====================================================

class App(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("Magnetic Flux Calibration Tool")
        self.geometry("420x260")

        ttk.Label(self,text="Frequency (Hz)").grid(row=0,column=0,padx=10,pady=6)
        self.freq = tk.IntVar(value=5)
        ttk.Combobox(self,textvariable=self.freq,
                     values=[5,10],state="readonly",width=10)\
                     .grid(row=0,column=1,sticky="w")

        ttk.Label(self,text="Mode").grid(row=1,column=0)
        self.mode = tk.StringVar(value="B_to_V")
        modebox = ttk.Combobox(self,textvariable=self.mode,state="readonly",
            values=["B_to_V (B → FG Voltage)","V_to_B (FG Voltage → B)"],width=26)
        modebox.grid(row=1,column=1,sticky="w")
        modebox.bind("<<ComboboxSelected>>",lambda e:self.update_label())

        self.input_label = ttk.Label(self,text="Target B (mT)")
        self.input_label.grid(row=2,column=0)

        self.input_val = tk.StringVar()
        ttk.Entry(self,textvariable=self.input_val,width=12)\
            .grid(row=2,column=1,sticky="w")

        self.extrap = tk.BooleanVar()
        ttk.Checkbutton(self,text="Allow extrapolation",
                        variable=self.extrap)\
                        .grid(row=3,column=1,sticky="w")

        ttk.Button(self,text="Compute",command=self.compute)\
            .grid(row=4,column=1,pady=10,sticky="w")

        self.out1 = ttk.Label(self,text="")
        self.out2 = ttk.Label(self,text="")
        self.out1.grid(row=5,column=0,columnspan=2,padx=10,sticky="w")
        self.out2.grid(row=6,column=0,columnspan=2,padx=10,sticky="w")

    def update_label(self):
        if self.mode.get().startswith("B_to_V"):
            self.input_label.config(text="Target B (mT)")
        else:
            self.input_label.config(text="FG Voltage p-p (V)")

    def compute(self):

        try:
            val=float(self.input_val.get())
        except:
            messagebox.showerror("Error","Enter numeric value")
            return

        f=self.freq.get()
        table=DATA[f]
        V,I,B = table["V"],table["I"],table["B"]

        allow=self.extrap.get()

        if self.mode.get().startswith("B_to_V"):

            v=interp(val,B,V,allow)
            i=interp(val,B,I,allow)

            if v is None:
                messagebox.showwarning("Out of range",
                f"B range is {B[0]}–{B[-1]} mT")
                return

            self.out1.config(text=f"Required FG Voltage: {v:.3f} Vpp")
            self.out2.config(text=f"Expected Current: {i:.3f} App")

        else:

            b=interp(val,V,B,allow)
            i=interp(val,V,I,allow)

            if b is None:
                messagebox.showwarning("Out of range",
                f"Voltage range is {V[0]}–{V[-1]} V")
                return

            self.out1.config(text=f"B Flux: {b:.3f} mT")
            self.out2.config(text=f"Current: {i:.3f} App")

if __name__=="__main__":
    App().mainloop()
