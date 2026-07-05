"""
tools/dump_asm.py — Dump clean x86 assembly from 99.exe using capstone.
Saves .asm files for each key function in reverse_engineering_ref/asm/
"""
import os
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from pefile import PE

EXE = r"c:\git\training_99\raw\99.exe"
OUT = r"c:\git\training_99\reverse_engineering_ref\asm"

# Functions to dump: (name, address, size_hint_bytes)
FUNCTIONS = [
    ("FUN_00402000_RNG",              0x00402000, 120),
    ("FUN_00402d68_ComputeAngle",     0x00402d68, 300),
    ("FUN_00402e88_SpawnBullet",      0x00402e88, 250),
    ("FUN_00402fbc_EntityLoop",       0x00402fbc, 600),
    ("FUN_00403400_MainFrame",        0x00403400, 500),
    ("FUN_00404660_GameInit",         0x00404660, 120),
    ("FUN_004046cc_SessionStart",     0x004046cc, 200),
]

def dump_all():
    pe = PE(EXE)
    ib = pe.OPTIONAL_HEADER.ImageBase
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True

    os.makedirs(OUT, exist_ok=True)

    for name, va, size in FUNCTIONS:
        rva = va - ib
        data = pe.get_data(rva, size)
        path = os.path.join(OUT, f"{name}.asm")

        with open(path, "w") as f:
            f.write(f"; {name}\n")
            f.write(f"; Address: 0x{va:08X}  Size: ~{size} bytes\n")
            f.write(f"; Disassembled from 99.exe via capstone\n")
            f.write(f"; {'='*60}\n\n")

            for insn in md.disasm(data, va):
                # Format: address: bytes  mnemonics
                bstr = " ".join(f"{b:02x}" for b in insn.bytes)
                f.write(f"  {insn.address:08X}: {bstr:24s} {insn.mnemonic:8s} {insn.op_str}\n")

        print(f"  {name}.asm — {len(list(md.disasm(data, va)))} instructions")

    # Also dump a combined all-in-one
    all_path = os.path.join(OUT, "99_functions.asm")
    with open(all_path, "w") as f:
        f.write("; 99.exe — All key functions disassembly\n")
        f.write(f"; {'='*60}\n\n")
        for name, va, size in FUNCTIONS:
            rva = va - ib
            data = pe.get_data(rva, size)
            f.write(f"\n; {'='*60}\n")
            f.write(f"; {name}  (0x{va:08X})\n")
            f.write(f"; {'='*60}\n\n")
            for insn in md.disasm(data, va):
                bstr = " ".join(f"{b:02x}" for b in insn.bytes)
                f.write(f"  {insn.address:08X}: {bstr:24s} {insn.mnemonic:8s} {insn.op_str}\n")

    print(f"\n  Combined: {all_path}")
    print("Done.")

if __name__ == "__main__":
    dump_all()
