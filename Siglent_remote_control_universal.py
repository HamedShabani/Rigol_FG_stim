import pyvisa

VISA_ADDRESS = ""   # leave blank for auto-find
CHANNEL = 1

fc = 250.0   # carrier frequency, Hz
fm = 5.0     # modulation frequency, Hz
amp = 5.0    # carrier amplitude, Vpp
depth = 99  # AM depth, percent


def auto_find_siglent():
    rm = pyvisa.ResourceManager()
    for r in rm.list_resources():
        try:
            inst = rm.open_resource(r)
            inst.timeout = 2000
            inst.write_termination = '\n'
            inst.read_termination = '\n'
            idn = inst.query("*IDN?").strip()
            inst.close()
            if "SIGLENT" in idn.upper() and "SDG" in idn.upper():
                return r, idn
        except Exception:
            pass
    return None, None


if VISA_ADDRESS:
    addr = VISA_ADDRESS
else:
    addr, idn = auto_find_siglent()
    if not addr:
        raise RuntimeError("Siglent generator not found")
    print("Found:", idn)
    print("VISA:", addr)

rm = pyvisa.ResourceManager()
inst = rm.open_resource(addr)
inst.write_termination = '\n'
inst.read_termination = '\n'

ch = f"C{CHANNEL}"

inst.write("*CLS")

# Carrier
inst.write(f"{ch}:BSWV WVTP,SINE")
inst.write(f"{ch}:BSWV FRQ,{fc}")
inst.write(f"{ch}:BSWV AMP,{amp}")
inst.write(f"{ch}:BSWV OFST,0")

# AM modulation, internal sine modulator
inst.write(f"{ch}:MDWV AM")
inst.write(f"{ch}:MDWV STATE,ON")
inst.write(f"{ch}:MDWV SRC,INT")
inst.write(f"{ch}:MDWV FRQ,{fm}")
inst.write(f"{ch}:MDWV DEPTH,{depth}")
inst.write(f"{ch}:MDWV AM,MDSP,SINE")
inst.write(f"{ch}:MDWV CARR,WVTP,SINE")
inst.write(f"{ch}:MDWV CARR,FRQ,{fc}")

inst.write(f"{ch}:OUTP ON")

print("Done. AM-modulated sine should be on the output.")
