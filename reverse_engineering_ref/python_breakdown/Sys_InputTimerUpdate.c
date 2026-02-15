void Sys_InputTimerUpdate(void)

{
  int in_EAX;
  HANDLE pvVar1;
  DWORD DVar2;
  int iVar3;
  
  if (G_PauseFlag == 1) {
    if (in_EAX == 0) {
      if (G_HighPriorityMode != 0) {
        DVar2 = 0x80;
        pvVar1 = GetCurrentProcess();
        SetPriorityClass(pvVar1,DVar2);
      }
      iVar3 = 0;
      pvVar1 = GetCurrentThread();
      SetThreadPriority(pvVar1,iVar3);
      if (DAT_00406d9c != 0) {
        ShowCursor(0);
        DVar2 = timeGetTime();
        iVar3 = DVar2 - DAT_00406d9c;
        DAT_00406da0 = DAT_00406da0 + iVar3;
        G_NextSpawnTime = G_NextSpawnTime + iVar3;
        G_NextPatternTime = G_NextPatternTime + iVar3;
        G_PatternTimer2 = G_PatternTimer2 + iVar3;
        if (G_DeathTime == 0) {
          G_GameStartTime = G_GameStartTime + iVar3;
        }
        DAT_00406d9c = 0;
      }
    }
    else if (DAT_00406d9c == 0) {
      DAT_00406d9c = timeGetTime();
      ShowCursor(1);
      if (G_HighPriorityMode != 0) {
        DVar2 = 0x20;
        pvVar1 = GetCurrentProcess();
        SetPriorityClass(pvVar1,DVar2);
      }
      iVar3 = 0;
      pvVar1 = GetCurrentThread();
      SetThreadPriority(pvVar1,iVar3);
      BitBlt(G_BackBufferDC,0,0,0x140,0xf0,G_SpriteDC,0,0,0xcc0020);
      return;
    }
  }
  return;
}



int lstrlenA(LPCSTR lpString)

{
  int iVar1;
  
                    // WARNING: Could not recover jumptable at 0x004047c8. Too many branches
                    // WARNING: Treating indirect jump as call
  iVar1 = lstrlenA(lpString);
  return iVar1;
}



void Sleep(DWORD dwMilliseconds)

{
                    // WARNING: Could not recover jumptable at 0x004047ce. Too many branches
                    // WARNING: Treating indirect jump as call
  Sleep(dwMilliseconds);
  return;
}



BOOL SetThreadPriority(HANDLE hThread,int nPriority)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x004047d4. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = SetThreadPriority(hThread,nPriority);
  return BVar1;
}



BOOL SetPriorityClass(HANDLE hProcess,DWORD dwPriorityClass)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x004047da. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = SetPriorityClass(hProcess,dwPriorityClass);
  return BVar1;
}



BOOL HeapFree(HANDLE hHeap,DWORD dwFlags,LPVOID lpMem)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x004047e0. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = HeapFree(hHeap,dwFlags,lpMem);
  return BVar1;
}



LPVOID HeapAlloc(HANDLE hHeap,DWORD dwFlags,SIZE_T dwBytes)

{
  LPVOID pvVar1;
  
                    // WARNING: Could not recover jumptable at 0x004047e6. Too many branches
                    // WARNING: Treating indirect jump as call
  pvVar1 = HeapAlloc(hHeap,dwFlags,dwBytes);
  return pvVar1;
}



HANDLE GetProcessHeap(void)

{
  HANDLE pvVar1;
  
                    // WARNING: Could not recover jumptable at 0x004047ec. Too many branches
                    // WARNING: Treating indirect jump as call
  pvVar1 = GetProcessHeap();
  return pvVar1;
}



HMODULE GetModuleHandleA(LPCSTR lpModuleName)

{
  HMODULE pHVar1;
  
                    // WARNING: Could not recover jumptable at 0x004047f2. Too many branches
                    // WARNING: Treating indirect jump as call
  pHVar1 = GetModuleHandleA(lpModuleName);
  return pHVar1;
}



HANDLE GetCurrentThread(void)

{
  HANDLE pvVar1;
  
                    // WARNING: Could not recover jumptable at 0x004047f8. Too many branches
                    // WARNING: Treating indirect jump as call
  pvVar1 = GetCurrentThread();
  return pvVar1;
}



HANDLE GetCurrentProcess(void)

{
  HANDLE pvVar1;
  
                    // WARNING: Could not recover jumptable at 0x004047fe. Too many branches
                    // WARNING: Treating indirect jump as call
  pvVar1 = GetCurrentProcess();
  return pvVar1;
}



void ExitProcess(UINT uExitCode)

{
                    // WARNING: Could not recover jumptable at 0x00404804. Too many branches
                    // WARNING: Subroutine does not return
                    // WARNING: Treating indirect jump as call
  ExitProcess(uExitCode);
  return;
}



int __cdecl wsprintfA(LPSTR param_1,LPCSTR param_2,...)

{
  int iVar1;
  
                    // WARNING: Could not recover jumptable at 0x0040480a. Too many branches
                    // WARNING: Treating indirect jump as call
  iVar1 = wsprintfA(param_1,param_2);
  return iVar1;
}



BOOL WaitMessage(void)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404810. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = WaitMessage();
  return BVar1;
}



BOOL TranslateMessage(MSG *lpMsg)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404816. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = TranslateMessage(lpMsg);
  return BVar1;
}



BOOL ShowWindow(HWND hWnd,int nCmdShow)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x0040481c. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = ShowWindow(hWnd,nCmdShow);
  return BVar1;
}



int ShowCursor(BOOL bShow)

{
  int iVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404822. Too many branches
                    // WARNING: Treating indirect jump as call
  iVar1 = ShowCursor(bShow);
  return iVar1;
}



int ReleaseDC(HWND hWnd,HDC hDC)

{
  int iVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404828. Too many branches
                    // WARNING: Treating indirect jump as call
  iVar1 = ReleaseDC(hWnd,hDC);
  return iVar1;
}



ATOM RegisterClassA(WNDCLASSA *lpWndClass)

{
  ATOM AVar1;
  
                    // WARNING: Could not recover jumptable at 0x0040482e. Too many branches
                    // WARNING: Treating indirect jump as call
  AVar1 = RegisterClassA(lpWndClass);
  return AVar1;
}



void PostQuitMessage(int nExitCode)

{
                    // WARNING: Could not recover jumptable at 0x00404834. Too many branches
                    // WARNING: Treating indirect jump as call
  PostQuitMessage(nExitCode);
  return;
}



BOOL PeekMessageA(LPMSG lpMsg,HWND hWnd,UINT wMsgFilterMin,UINT wMsgFilterMax,UINT wRemoveMsg)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x0040483a. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = PeekMessageA(lpMsg,hWnd,wMsgFilterMin,wMsgFilterMax,wRemoveMsg);
  return BVar1;
}



int MessageBoxA(HWND hWnd,LPCSTR lpText,LPCSTR lpCaption,UINT uType)

{
  int iVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404840. Too many branches
                    // WARNING: Treating indirect jump as call
  iVar1 = MessageBoxA(hWnd,lpText,lpCaption,uType);
  return iVar1;
}



HICON LoadIconA(HINSTANCE hInstance,LPCSTR lpIconName)

{
  HICON pHVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404846. Too many branches
                    // WARNING: Treating indirect jump as call
  pHVar1 = LoadIconA(hInstance,lpIconName);
  return pHVar1;
}



HCURSOR LoadCursorA(HINSTANCE hInstance,LPCSTR lpCursorName)

{
  HCURSOR pHVar1;
  
                    // WARNING: Could not recover jumptable at 0x0040484c. Too many branches
                    // WARNING: Treating indirect jump as call
  pHVar1 = LoadCursorA(hInstance,lpCursorName);
  return pHVar1;
}



HDC GetDC(HWND hWnd)

{
  HDC pHVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404852. Too many branches
                    // WARNING: Treating indirect jump as call
  pHVar1 = GetDC(hWnd);
  return pHVar1;
}



BOOL EndPaint(HWND hWnd,PAINTSTRUCT *lpPaint)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404858. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = EndPaint(hWnd,lpPaint);
  return BVar1;
}



int DrawTextA(HDC hdc,LPCSTR lpchText,int cchText,LPRECT lprc,UINT format)

{
  int iVar1;
  
                    // WARNING: Could not recover jumptable at 0x0040485e. Too many branches
                    // WARNING: Treating indirect jump as call
  iVar1 = DrawTextA(hdc,lpchText,cchText,lprc,format);
  return iVar1;
}



LRESULT DispatchMessageA(MSG *lpMsg)

{
  LRESULT LVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404864. Too many branches
                    // WARNING: Treating indirect jump as call
  LVar1 = DispatchMessageA(lpMsg);
  return LVar1;
}



LRESULT DefWindowProcA(HWND hWnd,UINT Msg,WPARAM wParam,LPARAM lParam)

{
  LRESULT LVar1;
  
                    // WARNING: Could not recover jumptable at 0x0040486a. Too many branches
                    // WARNING: Treating indirect jump as call
  LVar1 = DefWindowProcA(hWnd,Msg,wParam,lParam);
  return LVar1;
}



HWND CreateWindowExA(DWORD dwExStyle,LPCSTR lpClassName,LPCSTR lpWindowName,DWORD dwStyle,int X,
                    int Y,int nWidth,int nHeight,HWND hWndParent,HMENU hMenu,HINSTANCE hInstance,
                    LPVOID lpParam)

{
  HWND pHVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404870. Too many branches
                    // WARNING: Treating indirect jump as call
  pHVar1 = CreateWindowExA(dwExStyle,lpClassName,lpWindowName,dwStyle,X,Y,nWidth,nHeight,hWndParent,
                           hMenu,hInstance,lpParam);
  return pHVar1;
}



HDC BeginPaint(HWND hWnd,LPPAINTSTRUCT lpPaint)

{
  HDC pHVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404876. Too many branches
                    // WARNING: Treating indirect jump as call
  pHVar1 = BeginPaint(hWnd,lpPaint);
  return pHVar1;
}



BOOL AdjustWindowRectEx(LPRECT lpRect,DWORD dwStyle,BOOL bMenu,DWORD dwExStyle)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x0040487c. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = AdjustWindowRectEx(lpRect,dwStyle,bMenu,dwExStyle);
  return BVar1;
}



DWORD timeGetTime(void)

{
  DWORD DVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404882. Too many branches
                    // WARNING: Treating indirect jump as call
  DVar1 = timeGetTime();
  return DVar1;
}



BOOL TextOutA(HDC hdc,int x,int y,LPCSTR lpString,int c)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404888. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = TextOutA(hdc,x,y,lpString,c);
  return BVar1;
}



COLORREF SetTextColor(HDC hdc,COLORREF color)

{
  COLORREF CVar1;
  
                    // WARNING: Could not recover jumptable at 0x0040488e. Too many branches
                    // WARNING: Treating indirect jump as call
  CVar1 = SetTextColor(hdc,color);
  return CVar1;
}



UINT SetDIBColorTable(HDC hdc,UINT iStart,UINT cEntries,RGBQUAD *prgbq)

{
  UINT UVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404894. Too many branches
                    // WARNING: Treating indirect jump as call
  UVar1 = SetDIBColorTable(hdc,iStart,cEntries,prgbq);
  return UVar1;
}



int SetBkMode(HDC hdc,int mode)

{
  int iVar1;
  
                    // WARNING: Could not recover jumptable at 0x0040489a. Too many branches
                    // WARNING: Treating indirect jump as call
  iVar1 = SetBkMode(hdc,mode);
  return iVar1;
}



COLORREF SetBkColor(HDC hdc,COLORREF color)

{
  COLORREF CVar1;
  
                    // WARNING: Could not recover jumptable at 0x004048a0. Too many branches
                    // WARNING: Treating indirect jump as call
  CVar1 = SetBkColor(hdc,color);
  return CVar1;
}



HGDIOBJ SelectObject(HDC hdc,HGDIOBJ h)

{
  HGDIOBJ pvVar1;
  
                    // WARNING: Could not recover jumptable at 0x004048a6. Too many branches
                    // WARNING: Treating indirect jump as call
  pvVar1 = SelectObject(hdc,h);
  return pvVar1;
}



int SaveDC(HDC hdc)

{
  int iVar1;
  
                    // WARNING: Could not recover jumptable at 0x004048ac. Too many branches
                    // WARNING: Treating indirect jump as call
  iVar1 = SaveDC(hdc);
  return iVar1;
}



BOOL RestoreDC(HDC hdc,int nSavedDC)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x004048b2. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = RestoreDC(hdc,nSavedDC);
  return BVar1;
}



BOOL PatBlt(HDC hdc,int x,int y,int w,int h,DWORD rop)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x004048b8. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = PatBlt(hdc,x,y,w,h,rop);
  return BVar1;
}



BOOL GetTextExtentPoint32A(HDC hdc,LPCSTR lpString,int c,LPSIZE psizl)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x004048be. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = GetTextExtentPoint32A(hdc,lpString,c,psizl);
  return BVar1;
}



BOOL DeleteObject(HGDIOBJ ho)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x004048c4. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = DeleteObject(ho);
  return BVar1;
}



BOOL DeleteDC(HDC hdc)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x004048ca. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = DeleteDC(hdc);
  return BVar1;
}



HFONT CreateFontIndirectA(LOGFONTA *lplf)

{
  HFONT pHVar1;
  
                    // WARNING: Could not recover jumptable at 0x004048d0. Too many branches
                    // WARNING: Treating indirect jump as call
  pHVar1 = CreateFontIndirectA(lplf);
  return pHVar1;
}



HBITMAP CreateDIBSection(HDC hdc,BITMAPINFO *lpbmi,UINT usage,void **ppvBits,HANDLE hSection,
                        DWORD offset)

{
  HBITMAP pHVar1;
  
                    // WARNING: Could not recover jumptable at 0x004048d6. Too many branches
                    // WARNING: Treating indirect jump as call
  pHVar1 = CreateDIBSection(hdc,lpbmi,usage,ppvBits,hSection,offset);
  return pHVar1;
}



HDC CreateCompatibleDC(HDC hdc)

{
  HDC pHVar1;
  
                    // WARNING: Could not recover jumptable at 0x004048dc. Too many branches
                    // WARNING: Treating indirect jump as call
  pHVar1 = CreateCompatibleDC(hdc);
  return pHVar1;
}



HBITMAP CreateCompatibleBitmap(HDC hdc,int cx,int cy)

{
  HBITMAP pHVar1;
  
                    // WARNING: Could not recover jumptable at 0x004048e2. Too many branches
                    // WARNING: Treating indirect jump as call
  pHVar1 = CreateCompatibleBitmap(hdc,cx,cy);
  return pHVar1;
}



BOOL BitBlt(HDC hdc,int x,int y,int cx,int cy,HDC hdcSrc,int x1,int y1,DWORD rop)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x004048e8. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = BitBlt(hdc,x,y,cx,cy,hdcSrc,x1,y1,rop);
  return BVar1;
}


