; FUN_00402000_RNG
; Address: 0x00402000  Size: ~120 bytes
; Disassembled from 99.exe via capstone
; ============================================================

  00402000: 69 05 00 5c 40 00 fd 43 03 00 imul     eax, dword ptr [0x405c00], 0x343fd
  0040200A: 05 c3 9e 26 00           add      eax, 0x269ec3
  0040200F: a3 00 5c 40 00           mov      dword ptr [0x405c00], eax
  00402014: c1 f8 10                 sar      eax, 0x10
  00402017: 25 ff 7f 00 00           and      eax, 0x7fff
  0040201C: c3                       ret      
  0040201D: 90                       nop      
  0040201E: 90                       nop      
  0040201F: 90                       nop      
  00402020: 53                       push     ebx
  00402021: 83 c4 e4                 add      esp, -0x1c
  00402024: 6a 00                    push     0
  00402026: e8 c7 27 00 00           call     0x4047f2
  0040202B: a3 d8 69 40 00           mov      dword ptr [0x4069d8], eax
  00402030: e8 d3 01 00 00           call     0x402208
  00402035: 85 c0                    test     eax, eax
  00402037: 75 20                    jne      0x402059
  00402039: 6a 10                    push     0x10
  0040203B: 68 51 5c 40 00           push     0x405c51
  00402040: 68 3e 5c 40 00           push     0x405c3e
  00402045: 6a 00                    push     0
  00402047: e8 f4 27 00 00           call     0x404840
  0040204C: c7 44 24 08 01 00 00 00  mov      dword ptr [esp + 8], 1
  00402054: e9 b5 00 00 00           jmp      0x40210e
  00402059: e8 12 01 00 00           call     0x402170
  0040205E: 8b d8                    mov      ebx, eax
  00402060: 89 1d dc 69 40 00        mov      dword ptr [0x4069dc], ebx
  00402066: 85 db                    test     ebx, ebx
  00402068: 75 37                    jne      0x4020a1
  0040206A: 6a 10                    push     0x10
  0040206C: 68 51 5c 40 00           push     0x405c51
  00402071: 68 3e 5c 40 00           push     0x405c3e
  00402076: 6a 00                    push     0
