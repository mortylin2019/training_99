; FUN_004046cc_SessionStart
; Address: 0x004046CC  Size: ~200 bytes
; Disassembled from 99.exe via capstone
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
