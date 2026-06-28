; FUN_00402d68_ComputeAngle
; Address: 0x00402D68  Size: ~300 bytes
; Disassembled from 99.exe via capstone
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
