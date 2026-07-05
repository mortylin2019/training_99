"""tools/dump_resources.py — Extract all embedded data from 99.exe"""
import pefile, os, struct

EXE = r"c:\git\training_99\raw\99.exe"
OUT = r"c:\git\training_99\reverse_engineering_ref\resources"
os.makedirs(OUT, exist_ok=True)

pe = pefile.PE(EXE)
ib = pe.OPTIONAL_HEADER.ImageBase

# ── Sections ─────────────────────────────────────────
print("=== SECTIONS ===")
for s in pe.sections:
    name = s.Name.strip().decode().rstrip('\x00')
    print(f"  {name:8s}: VA=0x{ib+s.VirtualAddress:08X} Size=0x{s.Misc_VirtualSize:X} Raw=0x{s.PointerToRawData:X}")

# ── Strings (Shift-JIS) from .rdata ─────────────────
print("\n=== STRINGS ===")
rdata = None
for s in pe.sections:
    if b'.rdata' in s.Name:
        rdata = s; break
if not rdata:
    for s in pe.sections:
        if b'.data' in s.Name:
            rdata = s; break

all_strings = []
if rdata:
    data = pe.get_data(rdata.VirtualAddress, min(rdata.Misc_VirtualSize, 0x4000))
    i = 0
    while i < len(data) - 2:
        # Shift-JIS: ASCII (0x20-0x7E) or lead byte (0x81-0x9F, 0xE0-0xEF)
        b = data[i]
        if 0x20 <= b <= 0x7e or 0x81 <= b <= 0x9f or 0xe0 <= b <= 0xef:
            start = i
            while i < len(data) and data[i] != 0:
                i += 1
            try:
                txt = data[start:i].decode('shift-jis')
                if len(txt) >= 2 and not all(c < ' ' for c in txt):
                    all_strings.append((start, txt))
            except:
                pass
        i += 1

    # Save strings
    with open(os.path.join(OUT, "strings.txt"), "w", encoding="utf-8") as f:
        for off, s in all_strings:
            f.write(f"0x{off:04X}: {s}\n")

    for off, s in all_strings[:30]:
        print(f"  0x{off:04X}: {s}")
    print(f"  ... ({len(all_strings)} strings total, saved to strings.txt)")

# ── Resources ────────────────────────────────────────
print("\n=== RESOURCES ===")
rtypes = {1:'CURSOR',2:'BITMAP',3:'ICON',4:'MENU',5:'DIALOG',6:'STRING',
          7:'FONTDIR',8:'FONT',9:'ACCEL',10:'RCDATA',11:'MESSAGETABLE',
          12:'GROUP_CURSOR',14:'GROUP_ICON',16:'VERSION',24:'MANIFEST'}

for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries:
    name = rtypes.get(entry.id, f'TYPE_{entry.id}')
    print(f"  {name}:")
    for d in entry.directory.entries:
        for dd in d.directory.entries:
            rva = dd.data.struct.OffsetToData
            size = dd.data.struct.Size
            data = pe.get_data(rva, size)
            ext = {3:'.ico', 2:'.bmp', 14:'.ico', 16:'.bin'}.get(entry.id, '.bin')
            fname = f"{name}_{d.id}_{dd.data.lang}{ext}"
            with open(os.path.join(OUT, fname), 'wb') as f:
                f.write(data)
            print(f"    {fname}: {size} bytes")

# ── Velocity Table ───────────────────────────────────
print("\n=== VELOCITY TABLE (0x00405d74) ===")
vel_rva = 0x00405d74 - ib
data = pe.get_data(vel_rva, 64 * 12)
vel = []
for i in range(64):
    vx, vy, tan = struct.unpack_from('<iii', data, i * 12)
    vel.append((vx, vy, tan))
print(f"  {len(vel)} entries, first 4:")
for i in range(4):
    print(f"    [{i:2d}] vx={vel[i][0]:4d} vy={vel[i][1]:4d} tan={vel[i][2]}")

print("\nDone.")
