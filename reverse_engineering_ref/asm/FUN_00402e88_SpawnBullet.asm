; FUN_00402e88_SpawnBullet
; Address: 0x00402E88  Size: ~250 bytes
; Disassembled from 99.exe via capstone
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
