import pyvisa
import time

# --- CONFIG ---
FC = 250.0   # Carrier Frequency (Hz)
FM = 5.0     # Modulation/Envelope Frequency (Hz)
AMP = 1.0    # Amplitude (Vpp)
DEPTH = 500  # AM Depth (%)

def setup_33210a_internal_am():
    rm = pyvisa.ResourceManager()
    
    # 1. FIND INSTRUMENT
    addr = None
    for r in rm.list_resources():
        try:
            inst = rm.open_resource(r)
            idn = inst.query("*IDN?")
            if "33210A" in idn:
                addr = r
                inst.close()
                break
            inst.close()
        except: pass
    
    if not addr:
        print("Error: Keysight 33210A not found.")
        return

    try:
        inst = rm.open_resource(addr)
        inst.write("*RST") # Reset to factory defaults
        time.sleep(1)

        # 2. CONFIGURE CARRIER (The 250Hz Sine)
        inst.write("FUNC SINE")
        inst.write(f"FREQ {FC}")
        inst.write(f"VOLT {AMP}")
        inst.write("VOLT:OFFS 0")

        # 3. CONFIGURE AM MODULATION (The 5Hz Envelope)
        inst.write("AM:SOURCE INTERNAL")
        inst.write("AM:INT:FUNC SINE") # Envelope shape is Sine
        inst.write(f"AM:INT:FREQ {FM}")
        inst.write(f"AM:DEPT {DEPTH}")
        
        # 4. TURN ON MODULATION AND OUTPUT
        inst.write("AM:STATE ON")
        inst.write("OUTP ON")

        print(f"SUCCESS: Internal AM Active.")
        print(f"Carrier: {FC}Hz | Modulation: {FM}Hz")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    setup_33210a_internal_am()
