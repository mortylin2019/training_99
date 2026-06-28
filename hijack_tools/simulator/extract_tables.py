"""
simulator/extract_tables.py - Extract real velocity tables from running 99.exe.

Usage: python -m hijack_tools.simulator.extract_tables
       (game must be running)

Reads 0x00405d74 and 0x00406074 and prints Python list format.
Paste output into tables.py to replace approximate values.
"""

import ctypes
import struct
import time
import subprocess


def _find_window(pid, timeout=5.0):
    """Find visible main window belonging to PID using EnumWindows."""
    import ctypes.wintypes

    result = []

    @ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL,
                        ctypes.wintypes.HWND,
                        ctypes.wintypes.LPARAM)
    def enum_callback(hwnd, lparam):
        proc_id = ctypes.c_ulong()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(proc_id))
        if proc_id.value == pid:
            if ctypes.windll.user32.IsWindowVisible(hwnd):
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    result.append(hwnd)
                    return False
        return True

    start = time.time()
    while time.time() - start < timeout:
        result.clear()
        ctypes.windll.user32.EnumWindows(enum_callback, 0)
        if result:
            return result[0]
        time.sleep(0.2)
    return None


def extract():
    """Launch game, read velocity tables, print Python code."""
    print("Launching 99.exe...")
    proc = subprocess.Popen(
        r"c:\git\training_99\raw\99.exe",
        cwd=r"c:\git\training_99\raw"
    )
    time.sleep(2)

    hwnd = _find_window(proc.pid, timeout=5)
    if not hwnd:
        print("ERROR: Could not find game window (PID={})".format(proc.pid))
        proc.terminate()
        return
    print(f"Found window: 0x{hwnd:X}")

    pid = ctypes.c_ulong()
    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    ph = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, pid.value)
    if not ph:
        print("ERROR: Could not open process")
        proc.terminate()
        return

    # Read velocity table (64 * 12 bytes from 0x00405d74)
    buf = ctypes.create_string_buffer(64 * 12)
    vel_lines = []
    if ctypes.windll.kernel32.ReadProcessMemory(ph, 0x00405d74, buf, 64 * 12, None):
        vel_lines.append("VEL_TABLE = [\n")
        for i in range(64):
            vx, vy, _ = struct.unpack("<iii", buf.raw[i * 12:i * 12 + 12])
            vel_lines.append(f"    ({vx:>6}, {vy:>6}),\n")
        vel_lines.append("]\n")
        print(f"VEL_TABLE: {len(vel_lines)-2} angles read")

    # Read accel table (64 * 12 bytes from 0x00406074)
    accel_lines = []
    if ctypes.windll.kernel32.ReadProcessMemory(ph, 0x00406074, buf, 64 * 12, None):
        accel_lines.append("\nACCEL_TABLE = [\n")
        for i in range(64):
            vx, vy, _ = struct.unpack("<iii", buf.raw[i * 12:i * 12 + 12])
            accel_lines.append(f"    ({vx:>6}, {vy:>6}),\n")
        accel_lines.append("]\n")
        print(f"ACCEL_TABLE: {len(accel_lines)-2} angles read")

    ctypes.windll.kernel32.CloseHandle(ph)
    proc.terminate()

    if vel_lines:
        # Write tables.py with header + real data
        import os as _os
        path = _os.path.join(_os.path.dirname(__file__), "tables.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write('"""\n')
            f.write('simulator/tables.py - Real velocity tables from game binary.\n')
            f.write('Auto-extracted from running 99.exe.\n')
            f.write('"""\n\n')
            f.writelines(vel_lines)
            f.writelines(accel_lines)
        print(f"\nSaved to {path}")
        # Show first few values
        print("\nFirst 4 VEL entries:")
        for line in vel_lines[1:5]:
            print(f"  {line.rstrip()}")
    else:
        print("ERROR: Could not read tables")


if __name__ == "__main__":
    extract()
