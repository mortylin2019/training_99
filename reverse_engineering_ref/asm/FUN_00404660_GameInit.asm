; FUN_00404660_GameInit
; Address: 0x00404660  Size: ~120 bytes
; Disassembled from 99.exe via capstone
; ============================================================

  00404660: b8 10 6e 40 00           mov      eax, 0x406e10
  00404665: 33 d2                    xor      edx, edx
  00404667: c6 40 08 ff              mov      byte ptr [eax + 8], 0xff
  0040466B: 83 c0 0f                 add      eax, 0xf
  0040466E: 42                       inc      edx
  0040466F: 81 fa 2c 01 00 00        cmp      edx, 0x12c
  00404675: 7c f0                    jl       0x404667
  00404677: 8b 0d c0 6d 40 00        mov      ecx, dword ptr [0x406dc0]
  0040467D: 83 e9 01                 sub      ecx, 1
  00404680: 72 0a                    jb       0x40468c
  00404682: 74 14                    je       0x404698
  00404684: 49                       dec      ecx
  00404685: 74 1d                    je       0x4046a4
  00404687: 49                       dec      ecx
  00404688: 74 26                    je       0x4046b0
  0040468A: eb 0c                    jmp      0x404698
  0040468C: c7 05 a8 6d 40 00 1e 00 00 00 mov      dword ptr [0x406da8], 0x1e
  00404696: eb 22                    jmp      0x4046ba
  00404698: c7 05 a8 6d 40 00 32 00 00 00 mov      dword ptr [0x406da8], 0x32
  004046A2: eb 16                    jmp      0x4046ba
  004046A4: c7 05 a8 6d 40 00 64 00 00 00 mov      dword ptr [0x406da8], 0x64
  004046AE: eb 0a                    jmp      0x4046ba
  004046B0: c7 05 a8 6d 40 00 c8 00 00 00 mov      dword ptr [0x406da8], 0xc8
  004046BA: 33 c0                    xor      eax, eax
  004046BC: 33 d2                    xor      edx, edx
  004046BE: a3 ac 6d 40 00           mov      dword ptr [0x406dac], eax
  004046C3: 89 15 bc 6d 40 00        mov      dword ptr [0x406dbc], edx
  004046C9: c3                       ret      
  004046CA: 90                       nop      
  004046CB: 90                       nop      
  004046CC: 53                       push     ebx
  004046CD: 8b 15 84 6d 40 00        mov      edx, dword ptr [0x406d84]
  004046D3: 4a                       dec      edx
