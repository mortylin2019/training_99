; FUN_00403400_MainFrame
; Address: 0x00403400  Size: ~500 bytes
; Disassembled from 99.exe via capstone
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
