void Game_CalculateRanking(void)

{
  HWND in_EAX;
  uint *puVar1;
  HFONT h;
  int iVar2;
  HDC hdc;
  LPCSTR lpchText;
  uint uVar3;
  LPCSTR lpString;
  LPCSTR lpString_00;
  LPCSTR lpString_01;
  HFONT local_38;
  HGDIOBJ local_34;
  tagSIZE local_28;
  tagRECT local_20;
  
  uVar3 = G_Score_Time;
  if (G_ScoreMultiplier == 0) {
    uVar3 = G_DeathTime - G_GameStartTime;
  }
  for (puVar1 = &DAT_004067a3; uVar3 < *puVar1; puVar1 = puVar1 + 2) {
  }
  if ((char)puVar1[1] == '\0') {
    lpString = (LPCSTR)0x0;
  }
  else {
    lpString = *(LPCSTR *)(&DAT_00406bf8 + (char)puVar1[1] * 4);
  }
  if (*(char *)((int)puVar1 + 5) == '\0') {
    lpString_01 = (LPCSTR)0x0;
  }
  else {
    lpString_01 = *(LPCSTR *)(&DAT_00406bf8 + *(char *)((int)puVar1 + 5) * 4);
  }
  if (*(char *)((int)puVar1 + 6) == '\0') {
    lpString_00 = (LPCSTR)0x0;
  }
  else {
    lpString_00 = *(LPCSTR *)(&DAT_00406bf8 + *(char *)((int)puVar1 + 6) * 4);
  }
  if (*(char *)((int)puVar1 + 7) == '\0') {
    lpchText = (LPCSTR)0x0;
  }
  else {
    lpchText = *(LPCSTR *)(&DAT_00406bf8 + *(char *)((int)puVar1 + 7) * 4);
  }
  PatBlt(G_BackBufferDC,0,0,0x140,0xf0,0x42);
  lplf_00406374 = (LOGFONTA *)0x10;
  h = CreateFontIndirectA((LOGFONTA *)&lplf_00406374);
  SetTextColor(G_BackBufferDC,0xffffff);
  SetBkMode(G_BackBufferDC,1);
  if (lpString_00 == (LPCSTR)0x0) {
    local_34 = SelectObject(G_BackBufferDC,h);
  }
  else {
    iVar2 = lstrlenA(lpString_00);
    lplf_00406374 = (LOGFONTA *)(0x1e0 / (longlong)iVar2);
    if (0x4f < (int)lplf_00406374) {
      lplf_00406374 = (LOGFONTA *)&DAT_00000050;
    }
    local_38 = CreateFontIndirectA((LOGFONTA *)&lplf_00406374);
    local_34 = SelectObject(G_BackBufferDC,local_38);
    local_20.left = 0;
    local_20.top = 0x14;
    local_20.right = 0x140;
    local_20.bottom = 200;
    DrawTextA(G_BackBufferDC,lpString_00,iVar2,&local_20,0x825);
    SelectObject(G_BackBufferDC,h);
  }
  local_20.left = 0;
  local_20.top = 200;
  local_20.right = 0x140;
  local_20.bottom = 0xf0;
  if (lpchText != (LPCSTR)0x0) {
    DrawTextA(G_BackBufferDC,lpchText,-1,&local_20,0x26);
  }
  local_28.cx = 0;
  if (lpString != (LPCSTR)0x0) {
    iVar2 = lstrlenA(lpString);
    GetTextExtentPoint32A(G_BackBufferDC,lpString,iVar2,&local_28);
    TextOutA(G_BackBufferDC,4,4,lpString,iVar2);
  }
  if (lpString_01 != (LPCSTR)0x0) {
    iVar2 = lstrlenA(lpString_01);
    TextOutA(G_BackBufferDC,local_28.cx + 4,4,lpString_01,iVar2);
  }
  SelectObject(G_BackBufferDC,local_34);
  hdc = GetDC(in_EAX);
  BitBlt(hdc,0,0,0x140,0xf0,G_BackBufferDC,0,0,0xcc0020);
  ReleaseDC(in_EAX,hdc);
  DeleteObject(local_38);
  DeleteObject(h);
  G_InputState = 0;
  G_PauseFlag = 6;
  G_IsGameRunning = 0;
  return;
}



// WARNING: Globals starting with '_' overlap smaller symbols at the same address
