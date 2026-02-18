
import ctypes
import struct

PROCESS_ALL_ACCESS = 0x1F0FFF

def read_memory(process_handle, address, size):
    buffer = ctypes.create_string_buffer(size)
    bytes_read = ctypes.c_size_t()
    if ctypes.windll.kernel32.ReadProcessMemory(process_handle, address, buffer, size, ctypes.byref(bytes_read)):
        return buffer.raw
    return None

def main():
    hwnd = ctypes.windll.user32.FindWindowW(None, "特訓９９")
    if not hwnd:
        print("Game not found")
        return
    
    pid = ctypes.c_ulong()
    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    phandle = ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid.value)
    
    # Dump table at 0x00405d74
    # 64 entries, each 12 bytes (vx, vy, ?)
    table_data = read_memory(phandle, 0x00405d74, 64 * 12)
    if table_data:
        print("Angle Table (vx, vy):")
        for i in range(16): # Just show first 16
            vx, vy, pad = struct.unpack("<iii", table_data[i*12 : i*12+12])
            print(f"Angle {i:02}: vx={vx:>4}, vy={vy:>4}")
    
    ctypes.windll.kernel32.CloseHandle(phandle)

if __name__ == "__main__":
    main()
