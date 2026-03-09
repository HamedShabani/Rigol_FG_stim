import pyvisa

rm = pyvisa.ResourceManager()

print("Available VISA resources:")
resources = rm.list_resources()
for r in resources:
    print("  ", r)

print("\nChecking instruments...\n")

for resource in resources:
    try:
        inst = rm.open_resource(resource)
        inst.timeout = 2000  # ms

        # Optional: some USB/GPIB instruments need these
        inst.write_termination = '\n'
        inst.read_termination = '\n'

        idn = inst.query("*IDN?").strip()
        print(f"{resource} -> {idn}")

        if "33210A" in idn or "KEYSIGHT" in idn or "AGILENT" in idn:
            print("\nFound possible Keysight 33210A address:")
            print(resource)

        inst.close()

    except Exception as e:
        print(f"{resource} -> could not query ({e})")
