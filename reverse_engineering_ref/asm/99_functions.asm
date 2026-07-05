; 99.exe ¡X All key functions disassembly
; ============================================================


; ============================================================
; FUN_00402000_RNG  (0x00402000)
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

; ============================================================
; FUN_00402d68_ComputeAngle  (0x00402D68)
; ============================================================

  00402D68: 53                       push     ebx
  00402D69: 56                       push     esi
  00402D6A: 57                       push     edi
  00402D6B: 83 c4 f8                 add      esp, -8
  00402D6E: 8b 35 70 6d 40 00        mov      esi, dword ptr [0x406d70]
  00402D74: 8b 0d 6c 6d 40 00        mov      ecx, dword ptr [0x406d6c]
  00402D7A: 89 14 24                 mov      dword ptr [esp], edx
  00402D7D: 83 c1 06                 add      ecx, 6
  00402D80: 8b 10                    mov      edx, dword ptr [eax]
  00402D82: 8b 40 04                 mov      eax, dword ptr [eax + 4]
  00402D85: c1 e8 06                 shr      eax, 6
  00402D88: 83 c6 06                 add      esi, 6
  00402D8B: c1 ea 06                 shr      edx, 6
  00402D8E: 2b f0                    sub      esi, eax
  00402D90: 2b ca                    sub      ecx, edx
  00402D92: 85 c9                    test     ecx, ecx
  00402D94: 7d 30                    jge      0x402dc6
  00402D96: 85 f6                    test     esi, esi
  00402D98: 7e 18                    jle      0x402db2
  00402D9A: 8b c6                    mov      eax, esi
  00402D9C: f7 d8                    neg      eax
  00402D9E: 3b c8                    cmp      ecx, eax
  00402DA0: 7d 0c                    jge      0x402dae
  00402DA2: b3 18                    mov      bl, 0x18
  00402DA4: 3b c1                    cmp      eax, ecx
  00402DA6: 0f 84 b3 00 00 00        je       0x402e5f
  00402DAC: eb 4e                    jmp      0x402dfc
  00402DAE: b3 10                    mov      bl, 0x10
  00402DB0: eb 4a                    jmp      0x402dfc
  00402DB2: 3b f1                    cmp      esi, ecx
  00402DB4: 7e 0c                    jle      0x402dc2
  00402DB6: b3 20                    mov      bl, 0x20
  00402DB8: 85 f6                    test     esi, esi
  00402DBA: 0f 84 9f 00 00 00        je       0x402e5f
  00402DC0: eb 3a                    jmp      0x402dfc
  00402DC2: b3 28                    mov      bl, 0x28
  00402DC4: eb 36                    jmp      0x402dfc
  00402DC6: 85 f6                    test     esi, esi
  00402DC8: 7d 18                    jge      0x402de2
  00402DCA: 8b c6                    mov      eax, esi
  00402DCC: f7 d8                    neg      eax
  00402DCE: 3b c8                    cmp      ecx, eax
  00402DD0: 7d 0c                    jge      0x402dde
  00402DD2: b3 30                    mov      bl, 0x30
  00402DD4: 85 c9                    test     ecx, ecx
  00402DD6: 0f 84 83 00 00 00        je       0x402e5f
  00402DDC: eb 1e                    jmp      0x402dfc
  00402DDE: b3 38                    mov      bl, 0x38
  00402DE0: eb 1a                    jmp      0x402dfc
  00402DE2: 85 c9                    test     ecx, ecx
  00402DE4: 75 04                    jne      0x402dea
  00402DE6: b3 10                    mov      bl, 0x10
  00402DE8: eb 75                    jmp      0x402e5f
  00402DEA: 85 f6                    test     esi, esi
  00402DEC: 75 04                    jne      0x402df2
  00402DEE: 33 db                    xor      ebx, ebx
  00402DF0: eb 6d                    jmp      0x402e5f
  00402DF2: 3b f1                    cmp      esi, ecx
  00402DF4: 7e 04                    jle      0x402dfa
  00402DF6: b3 08                    mov      bl, 8
  00402DF8: eb 02                    jmp      0x402dfc
  00402DFA: 33 db                    xor      ebx, ebx
  00402DFC: 8b c1                    mov      eax, ecx
  00402DFE: c1 e0 0a                 shl      eax, 0xa
  00402E01: 99                       cdq      
  00402E02: f7 fe                    idiv     esi
  00402E04: 8b c8                    mov      ecx, eax
  00402E06: 85 c9                    test     ecx, ecx
  00402E08: 7d 02                    jge      0x402e0c
  00402E0A: f7 d9                    neg      ecx
  00402E0C: 33 c0                    xor      eax, eax
  00402E0E: 8a c3                    mov      al, bl
  00402E10: 8b d0                    mov      edx, eax
  00402E12: c1 e2 02                 shl      edx, 2
  00402E15: c7 44 24 04 00 00 01 00  mov      dword ptr [esp + 4], 0x10000
  00402E1D: 8d 14 52                 lea      edx, [edx + edx*2]
  00402E20: 81 c2 74 5d 40 00        add      edx, 0x405d74
  00402E26: 33 f6                    xor      esi, esi
  00402E28: 8b 42 04                 mov      eax, dword ptr [edx + 4]
  00402E2B: 85 c0                    test     eax, eax
  00402E2D: 74 15                    je       0x402e44
  00402E2F: 8b 42 08                 mov      eax, dword ptr [edx + 8]
  00402E32: 3b c8                    cmp      ecx, eax
  00402E34: 7e 06                    jle      0x402e3c
  00402E36: 8b f9                    mov      edi, ecx
  00402E38: 2b f8                    sub      edi, eax
  00402E3A: eb 04                    jmp      0x402e40
  00402E3C: 8b f8                    mov      edi, eax
  00402E3E: 2b f9                    sub      edi, ecx
  00402E40: 8b c7                    mov      eax, edi
  00402E42: eb 05                    jmp      0x402e49
  00402E44: b8 ff ff 00 00           mov      eax, 0xffff
  00402E49: 8b 7c 24 04              mov      edi, dword ptr [esp + 4]
  00402E4D: 3b c7                    cmp      eax, edi
  00402E4F: 7d 0e                    jge      0x402e5f
  00402E51: 89 44 24 04              mov      dword ptr [esp + 4], eax
  00402E55: 83 c2 0c                 add      edx, 0xc
  00402E58: 43                       inc      ebx
  00402E59: 46                       inc      esi
  00402E5A: 83 fe 07                 cmp      esi, 7
  00402E5D: 7c c9                    jl       0x402e28
  00402E5F: 8b 04 24                 mov      eax, dword ptr [esp]
  00402E62: 85 c0                    test     eax, eax
  00402E64: 74 1a                    je       0x402e80
  00402E66: e8 95 f1 ff ff           call     0x402000
  00402E6B: 99                       cdq      
  00402E6C: f7 3c 24                 idiv     dword ptr [esp]
  00402E6F: 8b f2                    mov      esi, edx
  00402E71: 8b 14 24                 mov      edx, dword ptr [esp]
  00402E74: 46                       inc      esi
  00402E75: d1 fa                    sar      edx, 1
  00402E77: 8b c6                    mov      eax, esi
  00402E79: 02 d8                    add      bl, al
  00402E7B: 2a da                    sub      bl, dl
  00402E7D: 80 e3 3f                 and      bl, 0x3f
  00402E80: 8b c3                    mov      eax, ebx
  00402E82: 59                       pop      ecx
  00402E83: 5a                       pop      edx
  00402E84: 5f                       pop      edi
  00402E85: 5e                       pop      esi
  00402E86: 5b                       pop      ebx
  00402E87: c3                       ret      
  00402E88: 53                       push     ebx
  00402E89: 56                       push     esi
  00402E8A: 8b d8                    mov      ebx, eax
  00402E8C: e8 6f f1 ff ff           call     0x402000
  00402E91: 83 e0 03                 and      eax, 3

; ============================================================
; FUN_00402e88_SpawnBullet  (0x00402E88)
; ============================================================

  00402E88: 53                       push     ebx
  00402E89: 56                       push     esi
  00402E8A: 8b d8                    mov      ebx, eax
  00402E8C: e8 6f f1 ff ff           call     0x402000
  00402E91: 83 e0 03                 and      eax, 3
  00402E94: 83 e8 01                 sub      eax, 1
  00402E97: 72 0a                    jb       0x402ea3
  00402E99: 74 1e                    je       0x402eb9
  00402E9B: 48                       dec      eax
  00402E9C: 74 33                    je       0x402ed1
  00402E9E: 48                       dec      eax
  00402E9F: 74 46                    je       0x402ee7
  00402EA1: eb 5a                    jmp      0x402efd
  00402EA3: e8 58 f1 ff ff           call     0x402000
  00402EA8: b9 00 51 00 00           mov      ecx, 0x5100
  00402EAD: 99                       cdq      
  00402EAE: f7 f9                    idiv     ecx
  00402EB0: 89 13                    mov      dword ptr [ebx], edx
  00402EB2: 33 c0                    xor      eax, eax
  00402EB4: 89 43 04                 mov      dword ptr [ebx + 4], eax
  00402EB7: eb 44                    jmp      0x402efd
  00402EB9: e8 42 f1 ff ff           call     0x402000
  00402EBE: b9 00 51 00 00           mov      ecx, 0x5100
  00402EC3: 99                       cdq      
  00402EC4: f7 f9                    idiv     ecx
  00402EC6: 89 13                    mov      dword ptr [ebx], edx
  00402EC8: c7 43 04 00 3d 00 00     mov      dword ptr [ebx + 4], 0x3d00
  00402ECF: eb 2c                    jmp      0x402efd
  00402ED1: 33 c0                    xor      eax, eax
  00402ED3: 89 03                    mov      dword ptr [ebx], eax
  00402ED5: e8 26 f1 ff ff           call     0x402000
  00402EDA: b9 00 3d 00 00           mov      ecx, 0x3d00
  00402EDF: 99                       cdq      
  00402EE0: f7 f9                    idiv     ecx
  00402EE2: 89 53 04                 mov      dword ptr [ebx + 4], edx
  00402EE5: eb 16                    jmp      0x402efd
  00402EE7: c7 03 00 51 00 00        mov      dword ptr [ebx], 0x5100
  00402EED: e8 0e f1 ff ff           call     0x402000
  00402EF2: b9 00 3d 00 00           mov      ecx, 0x3d00
  00402EF7: 99                       cdq      
  00402EF8: f7 f9                    idiv     ecx
  00402EFA: 89 53 04                 mov      dword ptr [ebx + 4], edx
  00402EFD: c6 43 0b 00              mov      byte ptr [ebx + 0xb], 0
  00402F01: c6 43 0c 00              mov      byte ptr [ebx + 0xc], 0
  00402F05: c6 43 09 00              mov      byte ptr [ebx + 9], 0
  00402F09: c6 43 0a 00              mov      byte ptr [ebx + 0xa], 0
  00402F0D: be 05 00 00 00           mov      esi, 5
  00402F12: a1 bc 6d 40 00           mov      eax, dword ptr [0x406dbc]
  00402F17: 83 f8 07                 cmp      eax, 7
  00402F1A: 0f 87 8c 00 00 00        ja       0x402fac
  00402F20: ff 24 85 27 2f 40 00     jmp      dword ptr [eax*4 + 0x402f27]
  00402F27: ac                       lodsb    al, byte ptr [esi]
  00402F28: 2f                       das      
  00402F29: 40                       inc      eax
  00402F2A: 00 47 2f                 add      byte ptr [edi + 0x2f], al
  00402F2D: 40                       inc      eax
  00402F2E: 00 4b 2f                 add      byte ptr [ebx + 0x2f], cl
  00402F31: 40                       inc      eax
  00402F32: 00 55 2f                 add      byte ptr [ebp + 0x2f], dl
  00402F35: 40                       inc      eax
  00402F36: 00 5f 2f                 add      byte ptr [edi + 0x2f], bl
  00402F39: 40                       inc      eax
  00402F3A: 00 69 2f                 add      byte ptr [ecx + 0x2f], ch
  00402F3D: 40                       inc      eax
  00402F3E: 00 87 2f 40 00 8d        add      byte ptr [edi - 0x72ffbfd1], al
  00402F44: 2f                       das      
  00402F45: 40                       inc      eax
  00402F46: 00 33                    add      byte ptr [ebx], dh
  00402F48: f6 eb                    imul     bl
  00402F4A: 61                       popal    
  00402F4B: c6 43 0a 01              mov      byte ptr [ebx + 0xa], 1
  00402F4F: c6 43 0b 30              mov      byte ptr [ebx + 0xb], 0x30
  00402F53: eb 57                    jmp      0x402fac
  00402F55: c6 43 0a 01              mov      byte ptr [ebx + 0xa], 1
  00402F59: c6 43 0b 20              mov      byte ptr [ebx + 0xb], 0x20
  00402F5D: eb 4d                    jmp      0x402fac
  00402F5F: c6 43 0a 01              mov      byte ptr [ebx + 0xa], 1
  00402F63: c6 43 0b 10              mov      byte ptr [ebx + 0xb], 0x10
  00402F67: eb 43                    jmp      0x402fac
  00402F69: c6 43 0a 01              mov      byte ptr [ebx + 0xa], 1
  00402F6D: e8 8e f0 ff ff           call     0x402000
  00402F72: 25 03 00 00 80           and      eax, 0x80000003
  00402F77: 79 05                    jns      0x402f7e
  00402F79: 48                       dec      eax
  00402F7A: 83 c8 fc                 or       eax, 0xfffffffc
  00402F7D: 40                       inc      eax
  00402F7E: 40                       inc      eax
  00402F7F: c1 e0 04                 shl      eax, 4

; ============================================================
; FUN_00402fbc_EntityLoop  (0x00402FBC)
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

; ============================================================
; FUN_00403400_MainFrame  (0x00403400)
; ============================================================

  00403400: 53                       push     ebx
  00403401: 56                       push     esi
  00403402: 57                       push     edi
  00403403: 55                       push     ebp
  00403404: 83 c4 d4                 add      esp, -0x2c
  00403407: a1 c4 6d 40 00           mov      eax, dword ptr [0x406dc4]
  0040340C: 85 c0                    test     eax, eax
  0040340E: 0f 84 e7 01 00 00        je       0x4035fb
  00403414: 8b 15 d4 69 40 00        mov      edx, dword ptr [0x4069d4]
  0040341A: 83 fa 0f                 cmp      edx, 0xf
  0040341D: 0f 87 86 00 00 00        ja       0x4034a9
  00403423: 8a 92 30 34 40 00        mov      dl, byte ptr [edx + 0x403430]
  00403429: ff 24 95 40 34 40 00     jmp      dword ptr [edx*4 + 0x403440]
  00403430: 04 00                    add      al, 0
  00403432: 00 00                    add      byte ptr [eax], al
  00403434: 02 00                    add      al, byte ptr [eax]
  00403436: 00 00                    add      byte ptr [eax], al
  00403438: 03 00                    add      eax, dword ptr [eax]
  0040343A: 00 00                    add      byte ptr [eax], al
  0040343C: 02 00                    add      al, byte ptr [eax]
  0040343E: 00 01                    add      byte ptr [ecx], al
  00403440: a9 34 40 00 b1           test     eax, 0xb1004034
  00403445: 34 40                    xor      al, 0x40
  00403447: 00 8b 34 40 00 70        add      byte ptr [ebx + 0x70004034], cl
  0040344D: 34 40                    xor      al, 0x40
  0040344F: 00 54 34 40              add      byte ptr [esp + esi + 0x40], dl
  00403453: 00 8b 0d cc 69 40        add      byte ptr [ebx + 0x4069cc0d], cl
  00403459: 00 85 c9 74 08 ff        add      byte ptr [ebp - 0xf78b37], al
  0040345F: 0d cc 69 40 00           or       eax, 0x4069cc
  00403464: eb 0a                    jmp      0x403470
  00403466: c7 05 cc 69 40 00 ef 00 00 00 mov      dword ptr [0x4069cc], 0xef
  00403470: a1 d0 69 40 00           mov      eax, dword ptr [0x4069d0]
  00403475: 85 c0                    test     eax, eax
  00403477: 74 08                    je       0x403481
  00403479: ff 0d d0 69 40 00        dec      dword ptr [0x4069d0]
  0040347F: eb 0a                    jmp      0x40348b
  00403481: c7 05 d0 69 40 00 ef 00 00 00 mov      dword ptr [0x4069d0], 0xef
  0040348B: 8b 15 c8 69 40 00        mov      edx, dword ptr [0x4069c8]
  00403491: 81 fa ef 00 00 00        cmp      edx, 0xef
  00403497: 7d 08                    jge      0x4034a1
  00403499: ff 05 c8 69 40 00        inc      dword ptr [0x4069c8]
  0040349F: eb 08                    jmp      0x4034a9
  004034A1: 33 c9                    xor      ecx, ecx
  004034A3: 89 0d c8 69 40 00        mov      dword ptr [0x4069c8], ecx
  004034A9: ff 05 d4 69 40 00        inc      dword ptr [0x4069d4]
  004034AF: eb 07                    jmp      0x4034b8
  004034B1: 33 c0                    xor      eax, eax
  004034B3: a3 d4 69 40 00           mov      dword ptr [0x4069d4], eax
  004034B8: a1 c8 69 40 00           mov      eax, dword ptr [0x4069c8]
  004034BD: 85 c0                    test     eax, eax
  004034BF: 74 56                    je       0x403517
  004034C1: 8b 3d fc 69 40 00        mov      edi, dword ptr [0x4069fc]
  004034C7: 8b d0                    mov      edx, eax
  004034C9: c1 e2 06                 shl      edx, 6
  004034CC: 8d 14 92                 lea      edx, [edx + edx*4]
  004034CF: 8b 0d 00 6a 40 00        mov      ecx, dword ptr [0x406a00]
  004034D5: 03 d1                    add      edx, ecx
  004034D7: b9 f0 00 00 00           mov      ecx, 0xf0
  004034DC: 2b c8                    sub      ecx, eax
  004034DE: 8b c1                    mov      eax, ecx
  004034E0: c1 e0 06                 shl      eax, 6
  004034E3: 8d 04 80                 lea      eax, [eax + eax*4]
  004034E6: 85 c0                    test     eax, eax
  004034E8: 7e 0b                    jle      0x4034f5
  004034EA: 8a 0a                    mov      cl, byte ptr [edx]
  004034EC: 88 0f                    mov      byte ptr [edi], cl
  004034EE: 42                       inc      edx
  004034EF: 47                       inc      edi
  004034F0: 48                       dec      eax
  004034F1: 85 c0                    test     eax, eax
  004034F3: 7f f5                    jg       0x4034ea
  004034F5: 8b 15 00 6a 40 00        mov      edx, dword ptr [0x406a00]
  004034FB: a1 c8 69 40 00           mov      eax, dword ptr [0x4069c8]
  00403500: c1 e0 06                 shl      eax, 6
  00403503: 8d 04 80                 lea      eax, [eax + eax*4]
  00403506: 85 c0                    test     eax, eax
  00403508: 7e 22                    jle      0x40352c
  0040350A: 8a 0a                    mov      cl, byte ptr [edx]
  0040350C: 88 0f                    mov      byte ptr [edi], cl
  0040350E: 42                       inc      edx
  0040350F: 47                       inc      edi
  00403510: 48                       dec      eax
  00403511: 85 c0                    test     eax, eax
  00403513: 7f f5                    jg       0x40350a
  00403515: eb 15                    jmp      0x40352c
  00403517: b9 00 2c 01 00           mov      ecx, 0x12c00
  0040351C: 8b 15 00 6a 40 00        mov      edx, dword ptr [0x406a00]
  00403522: a1 fc 69 40 00           mov      eax, dword ptr [0x4069fc]
  00403527: e8 f4 eb ff ff           call     0x402120
  0040352C: a1 c4 6d 40 00           mov      eax, dword ptr [0x406dc4]
  00403531: 83 f8 02                 cmp      eax, 2
  00403534: 0f 85 d0 00 00 00        jne      0x40360a
  0040353A: c7 44 24 08 fe 6a 40 00  mov      dword ptr [esp + 8], 0x406afe
  00403542: c7 44 24 04 c6 6b 40 00  mov      dword ptr [esp + 4], 0x406bc6
  0040354A: c7 04 24 62 6b 40 00     mov      dword ptr [esp], 0x406b62
  00403551: 33 c0                    xor      eax, eax
  00403553: bf 04 6a 40 00           mov      edi, 0x406a04
  00403558: b9 cc 6a 40 00           mov      ecx, 0x406acc
  0040355D: ba 68 6a 40 00           mov      edx, 0x406a68
  00403562: 0f b7 32                 movzx    esi, word ptr [edx]
  00403565: 8b 1d cc 69 40 00        mov      ebx, dword ptr [0x4069cc]
  0040356B: 03 f3                    add      esi, ebx
  0040356D: 81 fe f0 00 00 00        cmp      esi, 0xf0
  00403573: 7c 06                    jl       0x40357b
  00403575: 81 ee f0 00 00 00        sub      esi, 0xf0
  0040357B: 0f b7 1f                 movzx    ebx, word ptr [edi]
  0040357E: 8b 2d fc 69 40 00        mov      ebp, dword ptr [0x4069fc]
  00403584: 8d 5c 1d 00              lea      ebx, [ebp + ebx]
  00403588: 53                       push     ebx
  00403589: 8b de                    mov      ebx, esi
  0040358B: c1 e3 03                 shl      ebx, 3
  0040358E: 8d 1c 9b                 lea      ebx, [ebx + ebx*4]
  00403591: 5e                       pop      esi
  00403592: 8d 34 de                 lea      esi, [esi + ebx*8]
  00403595: 8a 19                    mov      bl, byte ptr [ecx]
  00403597: 88 1e                    mov      byte ptr [esi], bl
  00403599: 8b 1c 24                 mov      ebx, dword ptr [esp]
  0040359C: 0f b7 33                 movzx    esi, word ptr [ebx]
  0040359F: 8b 1d d0 69 40 00        mov      ebx, dword ptr [0x4069d0]
  004035A5: 03 f3                    add      esi, ebx
  004035A7: 81 fe f0 00 00 00        cmp      esi, 0xf0
  004035AD: 7c 06                    jl       0x4035b5
  004035AF: 81 ee f0 00 00 00        sub      esi, 0xf0
  004035B5: 8b 5c 24 08              mov      ebx, dword ptr [esp + 8]
  004035B9: 8b 2d fc 69 40 00        mov      ebp, dword ptr [0x4069fc]
  004035BF: 40                       inc      eax
  004035C0: 83 c7 02                 add      edi, 2
  004035C3: 0f b7 1b                 movzx    ebx, word ptr [ebx]
  004035C6: 41                       inc      ecx
  004035C7: 83 c2 02                 add      edx, 2
  004035CA: 8d 5c 1d 00              lea      ebx, [ebp + ebx]
  004035CE: 53                       push     ebx
  004035CF: 8b de                    mov      ebx, esi
  004035D1: c1 e3 03                 shl      ebx, 3
  004035D4: 5e                       pop      esi
  004035D5: 8d 1c 9b                 lea      ebx, [ebx + ebx*4]
  004035D8: 8d 34 de                 lea      esi, [esi + ebx*8]
  004035DB: 8b 5c 24 04              mov      ebx, dword ptr [esp + 4]
  004035DF: 8a 1b                    mov      bl, byte ptr [ebx]
  004035E1: 88 1e                    mov      byte ptr [esi], bl
  004035E3: 83 44 24 08 02           add      dword ptr [esp + 8], 2
  004035E8: ff 44 24 04              inc      dword ptr [esp + 4]
  004035EC: 83 04 24 02              add      dword ptr [esp], 2
  004035F0: 83 f8 32                 cmp      eax, 0x32

; ============================================================
; FUN_00404660_GameInit  (0x00404660)
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

; ============================================================
; FUN_004046cc_SessionStart  (0x004046CC)
; ============================================================

  004046CC: 53                       push     ebx
  004046CD: 8b 15 84 6d 40 00        mov      edx, dword ptr [0x406d84]
  004046D3: 4a                       dec      edx
  004046D4: 0f 85 ec 00 00 00        jne      0x4047c6
  004046DA: 85 c0                    test     eax, eax
  004046DC: 74 6d                    je       0x40474b
  004046DE: a1 9c 6d 40 00           mov      eax, dword ptr [0x406d9c]
  004046E3: 85 c0                    test     eax, eax
  004046E5: 0f 85 db 00 00 00        jne      0x4047c6
  004046EB: e8 92 01 00 00           call     0x404882
  004046F0: a3 9c 6d 40 00           mov      dword ptr [0x406d9c], eax
  004046F5: 6a 01                    push     1
  004046F7: e8 26 01 00 00           call     0x404822
  004046FC: 8b 0d cc 6d 40 00        mov      ecx, dword ptr [0x406dcc]
  00404702: 85 c9                    test     ecx, ecx
  00404704: 74 0d                    je       0x404713
  00404706: 6a 20                    push     0x20
  00404708: e8 f1 00 00 00           call     0x4047fe
  0040470D: 50                       push     eax
  0040470E: e8 c7 00 00 00           call     0x4047da
  00404713: 6a 00                    push     0
  00404715: e8 de 00 00 00           call     0x4047f8
  0040471A: 50                       push     eax
  0040471B: e8 b4 00 00 00           call     0x4047d4
  00404720: 68 20 00 cc 00           push     0xcc0020
  00404725: 6a 00                    push     0
  00404727: 6a 00                    push     0
  00404729: a1 e0 69 40 00           mov      eax, dword ptr [0x4069e0]
  0040472E: 50                       push     eax
  0040472F: 68 f0 00 00 00           push     0xf0
  00404734: 68 40 01 00 00           push     0x140
  00404739: 6a 00                    push     0
  0040473B: 6a 00                    push     0
  0040473D: 8b 15 e4 69 40 00        mov      edx, dword ptr [0x4069e4]
  00404743: 52                       push     edx
  00404744: e8 9f 01 00 00           call     0x4048e8
  00404749: 5b                       pop      ebx
  0040474A: c3                       ret      
  0040474B: 8b 0d cc 6d 40 00        mov      ecx, dword ptr [0x406dcc]
  00404751: 85 c9                    test     ecx, ecx
  00404753: 74 10                    je       0x404765
  00404755: 68 80 00 00 00           push     0x80
  0040475A: e8 9f 00 00 00           call     0x4047fe
  0040475F: 50                       push     eax
  00404760: e8 75 00 00 00           call     0x4047da
  00404765: 6a 00                    push     0
  00404767: e8 8c 00 00 00           call     0x4047f8
  0040476C: 50                       push     eax
  0040476D: e8 62 00 00 00           call     0x4047d4
  00404772: a1 9c 6d 40 00           mov      eax, dword ptr [0x406d9c]
  00404777: 85 c0                    test     eax, eax
  00404779: 74 4b                    je       0x4047c6
  0040477B: 6a 00                    push     0
  0040477D: e8 a0 00 00 00           call     0x404822
  00404782: e8 fb 00 00 00           call     0x404882
  00404787: 8b d8                    mov      ebx, eax
  00404789: a1 9c 6d 40 00           mov      eax, dword ptr [0x406d9c]
  0040478E: 2b d8                    sub      ebx, eax
