void DrawStartScreen(void)

{
  HWND in_EAX;
  HFONT h;
  HFONT h_00;
  HFONT h_01;
  HGDIOBJ h_02;
  HDC hdc;
  tagRECT local_20;
  
  lplf_00406374 = (LOGFONTA *)&DAT_00000050;
  h = CreateFontIndirectA((LOGFONTA *)&lplf_00406374);
  lplf_00406374 = (LOGFONTA *)0xe;
  h_00 = CreateFontIndirectA((LOGFONTA *)&lplf_00406374);
  lplf_00406374 = (LOGFONTA *)0x14;
  h_01 = CreateFontIndirectA((LOGFONTA *)&lplf_00406374);
  PatBlt(G_BackBufferDC,0,0,0x140,0xf0,0x42);
  h_02 = SelectObject(G_BackBufferDC,h);
  SetTextColor(G_BackBufferDC,0xffffff);
  SetBkColor(G_BackBufferDC,0);
  local_20.left = 0;
  local_20.top = 0;
  local_20.right = 0x140;
  local_20.bottom = 0x78;
  DrawTextA(G_BackBufferDC,(LPCSTR)&lpWindowName_00405c51,4,&local_20,0x825);
  SelectObject(G_BackBufferDC,h_00);
  local_20.top = local_20.bottom;
  local_20.bottom = 0xf0;
  if (G_DifficultyMode == 0) {
    DrawTextA(G_BackBufferDC,(LPCSTR)((int)&param_2_00405c90 + 3),-1,&local_20,0x821);
LAB_00403c17:
    local_20.top = local_20.top + 0x14;
  }
  else {
    if (G_DifficultyMode == 2) {
      DrawTextA(G_BackBufferDC,(LPCSTR)&lpchText_00405ca3 /* "調子に乗って 100発" */,-1,&local_20,0x821);
      goto LAB_00403c17;
    }
    if (G_DifficultyMode == 3) {
      DrawTextA(G_BackBufferDC,(LPCSTR)&lpchText_00405cb6 /* "怒濤の 200発" */,-1,&local_20,0x821);
      goto LAB_00403c17;
    }
  }
  if (DAT_00406dc4 == 0) {
    DrawTextA(G_BackBufferDC,(LPCSTR)&lpchText_00405cc3,-1,&local_20,0x821);
LAB_00403c66:
    local_20.top = local_20.top + 0x14;
  }
  else if (DAT_00406dc4 == 1) {
    DrawTextA(G_BackBufferDC,(LPCSTR)&lpchText_00405ccc,-1,&local_20,0x821);
    goto LAB_00403c66;
  }
  if (G_HighPriorityMode == 0) {
    DrawTextA(G_BackBufferDC,(LPCSTR)&lpchText_00405cd5 /* "他のプロセスと協調する" */,-1,&local_20,0x821);
    local_20.top = local_20.top + 0x14;
  }
  if (DAT_00406dc8 == 1) {
    DrawTextA(G_BackBufferDC,(LPCSTR)&lpchText_00405cec /* "なんとなく80フレーム/秒" */,-1,&local_20,0x821);
  }
  else {
    if (DAT_00406dc8 != 2) goto LAB_00403ce5;
    DrawTextA(G_BackBufferDC,(LPCSTR)&lpchText_00405d04 /* "勢い余って全速力" */,-1,&local_20,0x821);
  }
  local_20.top = local_20.top + 0x14;
LAB_00403ce5:
  SelectObject(G_BackBufferDC,h_01);
  local_20.top = 200;
  DrawTextA(G_BackBufferDC,(LPCSTR)&lpchText_00405d15 /* "Enterで特訓開始" */,0xf,&local_20,0x821);
  SelectObject(G_BackBufferDC,h_02);
  DeleteObject(h_01);
  DeleteObject(h);
  hdc = GetDC(in_EAX);
  BitBlt(hdc,0,0,0x140,0xf0,G_BackBufferDC,0,0,0xcc0020);
  ReleaseDC(in_EAX,hdc);
  G_InputState = 0;
  G_PauseFlag = 0;
  G_IsGameRunning = 0;
  return;
}


