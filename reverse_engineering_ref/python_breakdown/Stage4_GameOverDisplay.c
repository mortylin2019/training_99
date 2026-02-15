void __fastcall DrawGameOver(undefined4 param_1,uint param_2)

{
  HWND in_EAX;
  HFONT h;
  HFONT h_00;
  HGDIOBJ h_01;
  int iVar1;
  HDC hdc;
  tagRECT local_120;
  CHAR local_110 [256];
  
  lplf_00406374 = (LOGFONTA *)&DAT_00000050;
  h = CreateFontIndirectA((LOGFONTA *)&lplf_00406374);
  lplf_00406374 = (LOGFONTA *)0x10;
  h_00 = CreateFontIndirectA((LOGFONTA *)&lplf_00406374);
  h_01 = SelectObject(G_BackBufferDC,h);
  SetTextColor(G_BackBufferDC,0xffffff);
  SetBkMode(G_BackBufferDC,1);
  local_120.left = 0;
  local_120.top = 0;
  local_120.right = 0x140;
  local_120.bottom = 0x78;
  DrawTextA(G_BackBufferDC,(LPCSTR)&lpchText_00405d25,4,&local_120,0x825);
  local_120.top = local_120.bottom;
  local_120.bottom = 0xf0;
  SelectObject(G_BackBufferDC,h_00);
  iVar1 = wsprintfA(local_110,(LPCSTR)&param_2_00405d2a,param_2 / 1000,param_2 % 1000);
  DrawTextA(G_BackBufferDC,local_110,iVar1,&local_120,0x821);
  local_120.top = local_120.top + 0x20;
  if (G_ScoreMultiplier != 0) {
    G_Score_Time = G_Score_Time * G_ScoreMultiplier;
  }
  iVar1 = wsprintfA(local_110,(LPCSTR)&param_2_00405d3d,G_Score_Time / 1000,G_Score_Time % 1000);
  DrawTextA(G_BackBufferDC,local_110,iVar1,&local_120,0x821);
  local_120.top = local_120.top + 0x20;
  iVar1 = wsprintfA(local_110,(LPCSTR)&param_2_00405d50,G_CurrentBulletCount);
  DrawTextA(G_BackBufferDC,local_110,iVar1,&local_120,0x821);
  if (G_TotalEntitiesSpawned != 0) {
    local_120.top = local_120.top + 0x20;
    iVar1 = wsprintfA(local_110,(LPCSTR)&param_2_00405d5a,G_TotalEntitiesSpawned);
    DrawTextA(G_BackBufferDC,local_110,iVar1,&local_120,0x821);
  }
  if (G_ScoreMultiplier == 0) {
    iVar1 = wsprintfA(local_110,s__d__03dfps_00405d66,(uint)(G_Score_Time * 1000) / param_2,
                      (int)(((ulonglong)(uint)(G_Score_Time * 1000000) / (ulonglong)param_2) % 1000)
                     );
    DrawTextA(G_BackBufferDC,local_110,iVar1,&local_120,0x829);
  }
  SelectObject(G_BackBufferDC,h_01);
  DeleteObject(h);
  DeleteObject(h_00);
  hdc = GetDC(in_EAX);
  BitBlt(hdc,0,0,0x140,0xf0,G_BackBufferDC,0,0,0xcc0020);
  ReleaseDC(in_EAX,hdc);
  G_InputState = 0;
  G_PauseFlag = 5;
  G_IsGameRunning = 0;
  return;
}


