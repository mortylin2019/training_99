uint Util_Random(void)

{
  DAT_00405c00 = DAT_00405c00 * 0x343fd + 0x269ec3;
  return DAT_00405c00 >> 0x10 & 0x7fff;
}



void entry(void)

{
  ATOM AVar1;
  undefined2 extraout_var;
  BOOL BVar2;
  undefined4 extraout_ECX;
  tagMSG local_20;
  
  DAT_004069d8 = GetModuleHandleA((LPCSTR)0x0);
  AVar1 = FUN_00402208();
  if (CONCAT22(extraout_var,AVar1) == 0) {
    MessageBoxA((HWND)0x0,(LPCSTR)&lpText_00405c3e,(LPCSTR)&lpWindowName_00405c51,0x10);
    local_20.wParam = 1;
  }
  else {
    DAT_004069dc = FUN_00402170();
    if (DAT_004069dc == (HWND)0x0) {
      MessageBoxA((HWND)0x0,(LPCSTR)&lpText_00405c3e,(LPCSTR)&lpWindowName_00405c51,0x10);
      local_20.wParam = 1;
    }
    else {
      while( true ) {
        while( true ) {
          BVar2 = PeekMessageA(&local_20,(HWND)0x0,0,0,1);
          if (BVar2 != 0) break;
          G_CurrentTime_Tick = timeGetTime();
          if ((G_IsGameRunning == 0) || (DAT_00406d9c != 0)) {
            WaitMessage();
          }
          else if ((G_ScoreMultiplier == 0) || (DAT_00406da0 <= G_CurrentTime_Tick)) {
            Sleep(0);
            FUN_00403400(extraout_ECX);
            DAT_00406da0 = DAT_00406da0 + G_ScoreMultiplier;
          }
        }
        if (local_20.message == 0x12) break;
        TranslateMessage(&local_20);
        DispatchMessageA(&local_20);
      }
    }
  }
                    // WARNING: Subroutine does not return
  ExitProcess(local_20.wParam);
}



void __fastcall FUN_00402120(int param_1,undefined1 *param_2)

{
  undefined1 uVar1;
  undefined1 *in_EAX;
  undefined1 *puVar2;
  undefined1 *puVar3;
  
  if (param_1 != 0) {
    if (param_2 < in_EAX) {
      puVar3 = param_2 + param_1;
      puVar2 = in_EAX + param_1;
      while (param_1 != 0) {
        puVar2 = puVar2 + -1;
        puVar3 = puVar3 + -1;
        *puVar2 = *puVar3;
        param_1 = param_1 + -1;
      }
      return;
    }
    while (param_1 != 0) {
      uVar1 = *param_2;
      param_2 = param_2 + 1;
      *in_EAX = uVar1;
      in_EAX = in_EAX + 1;
      param_1 = param_1 + -1;
    }
  }
  return;
}



void __fastcall thunk_FUN_0040215a(undefined4 param_1,int param_2)

{
  undefined1 *in_EAX;
  
  while (0 < param_2) {
    *in_EAX = 0;
    in_EAX = in_EAX + 1;
    param_2 = param_2 + -1;
  }
  return;
}



void __fastcall FUN_0040215a(undefined4 param_1,int param_2)

{
  undefined1 *in_EAX;
  
  while (0 < param_2) {
    *in_EAX = 0;
    in_EAX = in_EAX + 1;
    param_2 = param_2 + -1;
  }
  return;
}



HWND FUN_00402170(void)

{
  HWND hWnd;
  tagRECT local_14;
  
  local_14.top = 0;
  local_14.left = 0;
  local_14.right = 0x140;
  local_14.bottom = 0xf0;
  AdjustWindowRectEx(&local_14,0xca0000,0,0);
  hWnd = CreateWindowExA(0,s_wcTKKN_00405c56,(LPCSTR)&lpWindowName_00405c51,0xca0000,-0x80000000,
                         -0x80000000,local_14.right - local_14.left,local_14.bottom - local_14.top,
                         (HWND)0x0,(HMENU)0x0,DAT_004069d8,(LPVOID)0x0);
  ShowWindow(hWnd,10);
  return hWnd;
}



int FUN_004021f4(void)

{
  byte *in_EAX;
  int iVar1;
  
  iVar1 = 1;
  for (; *in_EAX != 0; in_EAX = in_EAX + 1) {
    *in_EAX = *in_EAX ^ 0xff;
    iVar1 = iVar1 + 1;
  }
  return iVar1;
}



// WARNING: Globals starting with '_' overlap smaller symbols at the same address

ATOM FUN_00402208(void)

{
  ATOM AVar1;
  int iVar2;
  int *piVar3;
  int iVar4;
  char *pcVar5;
  undefined4 *puVar6;
  WNDCLASSA local_34;
  
  DAT_00405c00 = timeGetTime();
  iVar4 = 0;
  do {
    FUN_004021f4();
    iVar4 = iVar4 + 1;
  } while (iVar4 < 0xd);
  _DAT_00406bf8 = 0;
  puVar6 = &DAT_00406bfc;
  for (pcVar5 = &DAT_004063e4 /* "敵前逃亡する" */; *pcVar5 != '\0'; pcVar5 = pcVar5 + iVar4) {
    iVar4 = FUN_004021f4();
    *puVar6 = pcVar5;
    puVar6 = puVar6 + 1;
  }
  iVar4 = 0;
  piVar3 = &DAT_00405d78;
  do {
    if (*piVar3 == 0) {
      piVar3[1] = 0x10000;
    }
    else {
      iVar2 = (piVar3[-1] << 10) / *piVar3;
      piVar3[1] = iVar2;
      if (iVar2 < 0) {
        piVar3[1] = -iVar2;
      }
    }
    iVar4 = iVar4 + 1;
    piVar3 = piVar3 + 3;
  } while (iVar4 < 0x40);
  G_HighPriorityMode = 1;
  G_DifficultyMode = 1;
  DAT_00406dc4 = 2;
  G_PauseFlag = 0;
  local_34.style = 0xb;
  local_34.lpfnWndProc = FUN_00402318;
  local_34.cbClsExtra = 0;
  local_34.cbWndExtra = 0;
  local_34.hInstance = DAT_004069d8;
  local_34.hIcon = LoadIconA(DAT_004069d8,&lpIconName_00000065);
  local_34.hCursor = LoadCursorA((HINSTANCE)0x0,&lpCursorName_00007f00);
  local_34.hbrBackground = (HBRUSH)0x0;
  local_34.lpszMenuName = (LPCSTR)0x0;
  local_34.lpszClassName = s_wcTKKN_00405c56;
  AVar1 = RegisterClassA(&local_34);
  return AVar1;
}



LRESULT __thiscall FUN_00402318(void *this,HWND param_1,UINT param_2,WPARAM param_3,int param_4)

{
  LRESULT LVar1;
  
  if (0x101 < (int)param_2) {
    if (param_2 == 0x102) {
      if (param_4 == 0x40000000) {
        return 0;
      }
      FUN_00402abc(this,(ushort)param_3);
      return 0;
    }
    if (1 < param_2 - 0x104) {
      if (param_2 == 0x111) {
        FUN_00402d5c(param_4,param_3);
        return 0;
      }
      if (param_2 != 0x112) goto LAB_00402592;
    }
    if (DAT_00406d9c == 0) {
      Sys_InputTimerUpdate();
      LVar1 = DefWindowProcA(param_1,param_2,param_3,param_4);
      Sys_InputTimerUpdate();
      return LVar1;
    }
LAB_00402592:
    LVar1 = DefWindowProcA(param_1,param_2,param_3,param_4);
    return LVar1;
  }
  if (param_2 != 0x101) {
    if ((int)param_2 < 7) {
      if (param_2 == 6) {
        Sys_InputTimerUpdate();
        return 0;
      }
      if (param_2 == 1) {
        Entity_UpdateMovement();
        return 0;
      }
      if (param_2 == 2) {
        Entity_Type2_Bounce();
        return 0;
      }
    }
    else {
      if (param_2 == 0xf) {
        Entity_Type1_Homing();
        return 0;
      }
      if (param_2 == 0x100) {
        if (param_4 == 0x40000000) {
          return 0;
        }
        if ((int)param_3 < 0x28) {
          if (param_3 == 0x27) {
LAB_004024b9:
            G_InputState = G_InputState | 8;
            return 0;
          }
          if ((int)param_3 < 0x21) {
            if ((param_3 != 0x20) && (param_3 != 0xd)) {
              if (param_3 != 0x1b) {
                return 0;
              }
              Sys_InputTimerUpdate();
              ShowWindow(param_1,6);
              return 0;
            }
            if (G_PauseFlag == 0) {
              MainLoop_StateMachine();
              return 0;
            }
            if (G_PauseFlag != 1) {
              if (G_PauseFlag == 5) {
                Game_CalculateRanking();
                return 0;
              }
              if (G_PauseFlag != 6) {
                return 0;
              }
              DrawStartScreen();
              return 0;
            }
            if (DAT_00406d9c != 0) {
              Sys_InputTimerUpdate();
              return 0;
            }
            Sys_InputTimerUpdate();
            return 0;
          }
          if (param_3 != 0x25) {
            if (param_3 != 0x26) {
              return 0;
            }
LAB_004024c5:
            G_InputState = G_InputState | 4;
            return 0;
          }
        }
        else {
          if (100 < (int)param_3) {
            if (param_3 != 0x66) {
              if (param_3 != 0x68) {
                return 0;
              }
              goto LAB_004024c5;
            }
            goto LAB_004024b9;
          }
          if (param_3 != 100) {
            if ((param_3 != 0x28) && (param_3 != 0x62)) {
              return 0;
            }
            G_InputState = G_InputState | 2;
            return 0;
          }
        }
        G_InputState = G_InputState | 1;
        return 0;
      }
    }
    goto LAB_00402592;
  }
  if ((int)param_3 < 99) {
    if (param_3 != 0x62) {
      if (param_3 == 0x25) goto LAB_0040252a;
      if (param_3 == 0x26) goto LAB_0040253c;
      if (param_3 == 0x27) goto LAB_00402533;
      if (param_3 != 0x28) {
        return 0;
      }
    }
    G_InputState = G_InputState & 0xfffffffd;
  }
  else {
    if (param_3 != 100) {
      if (param_3 == 0x66) {
LAB_00402533:
        G_InputState = G_InputState & 0xfffffff7;
        return 0;
      }
      if (param_3 != 0x68) {
        return 0;
      }
LAB_0040253c:
      G_InputState = G_InputState & 0xfffffffb;
      return 0;
    }
LAB_0040252a:
    G_InputState = G_InputState & 0xfffffffe;
  }
  return 0;
}


