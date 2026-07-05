; FUN_00402fbc_EntityLoop
; Address: 0x00402FBC  Size: ~600 bytes
; Disassembled from 99.exe via capstone
; ============================================================

  00402FBC: 53                       push     ebx
  00402FBD: 56                       push     esi
  00402FBE: 57                       push     edi
  00402FBF: 83 c4 e0                 add      esp, -0x20
  00402FC2: be 04 5c 40 00           mov      esi, 0x405c04
  00402FC7: b9 04 00 00 00           mov      ecx, 4
  00402FCC: 8d 7c 24 10              lea      edi, [esp + 0x10]
  00402FD0: f3 a5                    rep movsd dword ptr es:[edi], dword ptr [esi]
  00402FD2: c7 04 24 10 6e 40 00     mov      dword ptr [esp], 0x406e10
  00402FD9: a1 a4 6d 40 00           mov      eax, dword ptr [0x406da4]
  00402FDE: 89 44 24 0c              mov      dword ptr [esp + 0xc], eax
  00402FE2: 33 d2                    xor      edx, edx
  00402FE4: 89 54 24 08              mov      dword ptr [esp + 8], edx
  00402FE8: e9 08 03 00 00           jmp      0x4032f5
  00402FED: 8b 0c 24                 mov      ecx, dword ptr [esp]
  00402FF0: 0f b6 71 08              movzx    esi, byte ptr [ecx + 8]
  00402FF4: 81 fe ff 00 00 00        cmp      esi, 0xff
  00402FFA: 75 0d                    jne      0x403009
  00402FFC: 8b 04 24                 mov      eax, dword ptr [esp]
  00402FFF: e8 84 fe ff ff           call     0x402e88
  00403004: e9 f0 03 00 00           jmp      0x4033f9
  00403009: 8b 14 24                 mov      edx, dword ptr [esp]
  0040300C: 8b 0a                    mov      ecx, dword ptr [edx]
  0040300E: 81 f9 00 51 00 00        cmp      ecx, 0x5100
  00403014: 77 0e                    ja       0x403024
  00403016: 8b 04 24                 mov      eax, dword ptr [esp]
  00403019: 8b 50 04                 mov      edx, dword ptr [eax + 4]
  0040301C: 81 fa 00 3d 00 00        cmp      edx, 0x3d00
  00403022: 76 1c                    jbe      0x403040
  00403024: 8b 0c 24                 mov      ecx, dword ptr [esp]
  00403027: f6 41 0a 02              test     byte ptr [ecx + 0xa], 2
  0040302B: 74 06                    je       0x403033
  0040302D: ff 0d ac 6d 40 00        dec      dword ptr [0x406dac]
  00403033: 8b 04 24                 mov      eax, dword ptr [esp]
  00403036: e8 4d fe ff ff           call     0x402e88
  0040303B: e9 ad 02 00 00           jmp      0x4032ed
  00403040: 8b 14 24                 mov      edx, dword ptr [esp]
  00403043: 8b 04 24                 mov      eax, dword ptr [esp]
  00403046: 8b 0d 80 6d 40 00        mov      ecx, dword ptr [0x406d80]
  0040304C: 8b 1a                    mov      ebx, dword ptr [edx]
  0040304E: 8b 50 04                 mov      edx, dword ptr [eax + 4]
  00403051: c1 ea 06                 shr      edx, 6
  00403054: c1 eb 06                 shr      ebx, 6
  00403057: 83 ea 04                 sub      edx, 4
  0040305A: 83 eb 04                 sub      ebx, 4
  0040305D: 85 c9                    test     ecx, ecx
  0040305F: 89 54 24 04              mov      dword ptr [esp + 4], edx
  00403063: 0f 85 d0 00 00 00        jne      0x403139
  00403069: 8b c3                    mov      eax, ebx
  0040306B: 8b 15 6c 6d 40 00        mov      edx, dword ptr [0x406d6c]
  00403071: 2b c2                    sub      eax, edx
  00403073: 8b 54 24 04              mov      edx, dword ptr [esp + 4]
  00403077: 8b 0d 70 6d 40 00        mov      ecx, dword ptr [0x406d70]
  0040307D: 83 c0 04                 add      eax, 4
  00403080: 2b d1                    sub      edx, ecx
  00403082: 83 c2 06                 add      edx, 6
  00403085: 83 f8 17                 cmp      eax, 0x17
  00403088: 73 45                    jae      0x4030cf
  0040308A: 83 fa 14                 cmp      edx, 0x14
  0040308D: 73 40                    jae      0x4030cf
  0040308F: 8b 0c 24                 mov      ecx, dword ptr [esp]
  00403092: 8a 49 09                 mov      cl, byte ptr [ecx + 9]
  00403095: 84 c9                    test     cl, cl
  00403097: 75 0d                    jne      0x4030a6
  00403099: ff 05 b4 6d 40 00        inc      dword ptr [0x406db4]
  0040309F: 8b 0c 24                 mov      ecx, dword ptr [esp]
  004030A2: c6 41 09 01              mov      byte ptr [ecx + 9], 1
  004030A6: 83 e8 06                 sub      eax, 6
  004030A9: 83 f8 0b                 cmp      eax, 0xb
  004030AC: 0f 83 87 00 00 00        jae      0x403139
  004030B2: 83 ea 06                 sub      edx, 6
  004030B5: 83 fa 0a                 cmp      edx, 0xa
  004030B8: 73 7f                    jae      0x403139
  004030BA: 8b 44 24 0c              mov      eax, dword ptr [esp + 0xc]
  004030BE: a3 98 6d 40 00           mov      dword ptr [0x406d98], eax
  004030C3: c7 05 80 6d 40 00 01 00 00 00 mov      dword ptr [0x406d80], 1
  004030CD: eb 6a                    jmp      0x403139
  004030CF: 8b 14 24                 mov      edx, dword ptr [esp]
  004030D2: 8a 42 09                 mov      al, byte ptr [edx + 9]
  004030D5: 84 c0                    test     al, al
  004030D7: 74 60                    je       0x403139
  004030D9: 8b 14 24                 mov      edx, dword ptr [esp]
  004030DC: c6 42 09 00              mov      byte ptr [edx + 9], 0
  004030E0: ff 0d b4 6d 40 00        dec      dword ptr [0x406db4]
  004030E6: a1 b4 6d 40 00           mov      eax, dword ptr [0x406db4]
  004030EB: 85 c0                    test     eax, eax
  004030ED: 74 4a                    je       0x403139
  004030EF: 01 05 b8 6d 40 00        add      dword ptr [0x406db8], eax
  004030F5: c7 05 04 6e 40 00 64 00 00 00 mov      dword ptr [0x406e04], 0x64
  004030FF: 8b 54 24 0c              mov      edx, dword ptr [esp + 0xc]
  00403103: 8b 0d 08 6e 40 00        mov      ecx, dword ptr [0x406e08]
  00403109: 3b d1                    cmp      edx, ecx
  0040310B: 73 12                    jae      0x40311f
  0040310D: a1 0c 6e 40 00           mov      eax, dword ptr [0x406e0c]
  00403112: 83 f8 0a                 cmp      eax, 0xa
  00403115: 73 12                    jae      0x403129
  00403117: ff 05 0c 6e 40 00        inc      dword ptr [0x406e0c]
  0040311D: eb 0a                    jmp      0x403129
  0040311F: c7 05 0c 6e 40 00 01 00 00 00 mov      dword ptr [0x406e0c], 1
  00403129: 8b 54 24 0c              mov      edx, dword ptr [esp + 0xc]
  0040312D: 81 c2 e8 03 00 00        add      edx, 0x3e8
  00403133: 89 15 08 6e 40 00        mov      dword ptr [0x406e08], edx
  00403139: 8b 0c 24                 mov      ecx, dword ptr [esp]
  0040313C: 8a 41 0a                 mov      al, byte ptr [ecx + 0xa]
  0040313F: fe c8                    dec      al
  00403141: 0f 84 b4 00 00 00        je       0x4031fb
  00403147: fe c8                    dec      al
  00403149: 74 0d                    je       0x403158
  0040314B: fe c8                    dec      al
  0040314D: 0f 84 87 00 00 00        je       0x4031da
  00403153: e9 16 01 00 00           jmp      0x40326e
  00403158: 8b 15 6c 6d 40 00        mov      edx, dword ptr [0x406d6c]
  0040315E: 83 c2 06                 add      edx, 6
  00403161: 3b d3                    cmp      edx, ebx
  00403163: 7e 12                    jle      0x403177
  00403165: 8b 0c 24                 mov      ecx, dword ptr [esp]
  00403168: 8a 41 0d                 mov      al, byte ptr [ecx + 0xd]
  0040316B: 3c 60                    cmp      al, 0x60
  0040316D: 7d 18                    jge      0x403187
  0040316F: 8b 14 24                 mov      edx, dword ptr [esp]
  00403172: fe 42 0d                 inc      byte ptr [edx + 0xd]
  00403175: eb 10                    jmp      0x403187
  00403177: 8b 0c 24                 mov      ecx, dword ptr [esp]
  0040317A: 8a 41 0d                 mov      al, byte ptr [ecx + 0xd]
  0040317D: 3c a0                    cmp      al, 0xa0
  0040317F: 7e 06                    jle      0x403187
  00403181: 8b 14 24                 mov      edx, dword ptr [esp]
  00403184: fe 4a 0d                 dec      byte ptr [edx + 0xd]
  00403187: 8b 0d 70 6d 40 00        mov      ecx, dword ptr [0x406d70]
  0040318D: 83 c1 06                 add      ecx, 6
  00403190: 8b 44 24 04              mov      eax, dword ptr [esp + 4]
  00403194: 3b c8                    cmp      ecx, eax
  00403196: 7e 13                    jle      0x4031ab
  00403198: 8b 14 24                 mov      edx, dword ptr [esp]
  0040319B: 8a 4a 0e                 mov      cl, byte ptr [edx + 0xe]
  0040319E: 80 f9 60                 cmp      cl, 0x60
  004031A1: 7d 19                    jge      0x4031bc
  004031A3: 8b 04 24                 mov      eax, dword ptr [esp]
  004031A6: fe 40 0e                 inc      byte ptr [eax + 0xe]
  004031A9: eb 11                    jmp      0x4031bc
  004031AB: 8b 14 24                 mov      edx, dword ptr [esp]
  004031AE: 8a 4a 0e                 mov      cl, byte ptr [edx + 0xe]
  004031B1: 80 f9 a0                 cmp      cl, 0xa0
  004031B4: 7e 06                    jle      0x4031bc
  004031B6: 8b 04 24                 mov      eax, dword ptr [esp]
  004031B9: fe 48 0e                 dec      byte ptr [eax + 0xe]
  004031BC: 8b 14 24                 mov      edx, dword ptr [esp]
  004031BF: 8b 04 24                 mov      eax, dword ptr [esp]
  004031C2: 0f be 4a 0d              movsx    ecx, byte ptr [edx + 0xd]
  004031C6: 01 08                    add      dword ptr [eax], ecx
  004031C8: 8b 14 24                 mov      edx, dword ptr [esp]
  004031CB: 8b 04 24                 mov      eax, dword ptr [esp]
  004031CE: 0f be 4a 0e              movsx    ecx, byte ptr [edx + 0xe]
  004031D2: 01 48 04                 add      dword ptr [eax + 4], ecx
  004031D5: e9 b0 00 00 00           jmp      0x40328a
  004031DA: 8d 04 76                 lea      eax, [esi + esi*2]
  004031DD: 8b 0c 24                 mov      ecx, dword ptr [esp]
  004031E0: 8b 14 85 74 60 40 00     mov      edx, dword ptr [eax*4 + 0x406074]
  004031E7: 01 11                    add      dword ptr [ecx], edx
  004031E9: 8b 14 24                 mov      edx, dword ptr [esp]
  004031EC: 8b 04 85 78 60 40 00     mov      eax, dword ptr [eax*4 + 0x406078]
  004031F3: 01 42 04                 add      dword ptr [edx + 4], eax
  004031F6: e9 8f 00 00 00           jmp      0x40328a
  004031FB: 8b 0c 24                 mov      ecx, dword ptr [esp]
  004031FE: fe 41 0c                 inc      byte ptr [ecx + 0xc]
  00403201: 8b 04 24                 mov      eax, dword ptr [esp]
  00403204: 8b 0c 24                 mov      ecx, dword ptr [esp]
  00403207: 8a 50 0b                 mov      dl, byte ptr [eax + 0xb]
  0040320A: 8a 41 0c                 mov      al, byte ptr [ecx + 0xc]
  0040320D: 3a d0                    cmp      dl, al
  0040320F: 75 5d                    jne      0x40326e
