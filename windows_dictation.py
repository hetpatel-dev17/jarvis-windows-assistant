"""Windows voice-typing handoff and explicit spoken submission markers.

No speech recognition implementation here. Windows owns dictation. OS hotkeys
are invoked by the running product only with its own editor foreground.
"""
import re


class WindowsEditor:
    """Use the standard Windows EDIT control, rather than a Tk-only entry.

    Windows voice typing needs a Windows-compatible focused editing surface.
    The parent Tk frame owns the child lifetime and layout.
    """
    def __init__(self, root, **unused):
        import ctypes
        from ctypes import wintypes as w
        import tkinter as tk
        self.ctypes=ctypes;self.w=w;self.user=ctypes.WinDLL('user32',use_last_error=True)
        self.root=root;self.frame=tk.Frame(root,bg='#182640',height=36)
        self.frame.pack_propagate(False);self.frame.update_idletasks()
        self.user.CreateWindowExW.argtypes=[w.DWORD,w.LPCWSTR,w.LPCWSTR,w.DWORD,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,w.HWND,w.HMENU,w.HINSTANCE,ctypes.c_void_p]
        self.user.CreateWindowExW.restype=w.HWND
        self.user.SendMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM];self.user.SendMessageW.restype=ctypes.c_ssize_t
        self.user.SetWindowTextW.argtypes=[w.HWND,w.LPCWSTR]
        self.user.GetWindowTextLengthW.argtypes=[w.HWND]
        self.user.GetWindowTextW.argtypes=[w.HWND,w.LPWSTR,ctypes.c_int]
        self.user.SetFocus.argtypes=[w.HWND];self.user.SetFocus.restype=w.HWND
        self.user.MoveWindow.argtypes=[w.HWND,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,w.BOOL]
        self.hwnd=self.user.CreateWindowExW(0,'EDIT','',0x50000000|0x00800000|0x80,0,0,400,36,self.frame.winfo_id(),None,None,None)
        if not self.hwnd:raise OSError(ctypes.get_last_error(),'Windows text box could not be created.')
        gdi=ctypes.WinDLL('gdi32');gdi.GetStockObject.restype=w.HANDLE
        self.user.SendMessageW(self.hwnd,0x30,gdi.GetStockObject(17),1)
        self.frame.bind('<Configure>',lambda e:self.user.MoveWindow(self.hwnd,0,0,e.width,e.height,True))
        self.callback_type=ctypes.WINFUNCTYPE(ctypes.c_ssize_t,w.HWND,w.UINT,w.WPARAM,w.LPARAM)
        self.user.SetWindowLongPtrW.argtypes=[w.HWND,ctypes.c_int,ctypes.c_void_p];self.user.SetWindowLongPtrW.restype=ctypes.c_void_p
        self.user.CallWindowProcW.argtypes=[ctypes.c_void_p,w.HWND,w.UINT,w.WPARAM,w.LPARAM];self.user.CallWindowProcW.restype=ctypes.c_ssize_t
        self.enter=None
        def procedure(hwnd,message,wp,lp):
            if message==0x100 and wp==13 and self.enter:
                self.root.after(0,self.enter);return 0
            return self.user.CallWindowProcW(self.original,hwnd,message,wp,lp)
        self.procedure=self.callback_type(procedure)
        self.original=self.user.SetWindowLongPtrW(self.hwnd,-4,ctypes.cast(self.procedure,ctypes.c_void_p))
    def pack(self,**options):self.frame.pack(**options)
    def get(self):
        count=self.user.GetWindowTextLengthW(self.hwnd)
        buffer=self.ctypes.create_unicode_buffer(count+1)
        self.user.GetWindowTextW(self.hwnd,buffer,count+1)
        return buffer.value
    def delete(self,*unused):self.user.SetWindowTextW(self.hwnd,'')
    def configure(self,state='normal',**unused):self.user.SendMessageW(self.hwnd,0xcf,state=='readonly',0)
    def focus_set(self):self.user.SetFocus(self.hwnd)
    def bind(self,event,callback):
        if event=='<Return>':self.enter=callback


def interpret(text):
    text=text.strip()
    clean=re.sub(r'[^a-z ]','',text.casefold()).strip()
    if clean in ('go to sleep','jarvis go to sleep','sleep jarvis'):
        return 'sleep',''
    match=re.search(r'(?:[\s,.!?]+|^)run task[\s,.!?]*$',text,re.I)
    if match:
        command=text[:match.start()].strip(' \t\r\n,.!?')
        if command:return 'submit',command
    return 'draft',text


class WindowsTyping:
    def __init__(self, root, editor):
        self.root=root;self.editor=editor

    def _key_sequence(self, sequence):
        import ctypes
        from ctypes import wintypes as w
        user=ctypes.WinDLL('user32',use_last_error=True)
        user.GetForegroundWindow.restype=w.HWND
        user.GetAncestor.argtypes=[w.HWND,w.UINT];user.GetAncestor.restype=w.HWND
        target=user.GetAncestor(self.root.winfo_id(),2)
        if user.GetForegroundWindow()!=target:
            raise RuntimeError('Click the Jarvis text box first. Windows blocked background activation.')
        class KEYBOARD(ctypes.Structure):
            _fields_=[('vk',w.WORD),('scan',w.WORD),('flags',w.DWORD),('time',w.DWORD),('extra',ctypes.c_size_t)]
        class MOUSE(ctypes.Structure):
            _fields_=[('dx',w.LONG),('dy',w.LONG),('data',w.DWORD),('flags',w.DWORD),('time',w.DWORD),('extra',ctypes.c_size_t)]
        class PAYLOAD(ctypes.Union):
            _fields_=[('ki',KEYBOARD),('mi',MOUSE)]
        class INPUT(ctypes.Structure):
            _fields_=[('type',w.DWORD),('payload',PAYLOAD)]
        inputs=(INPUT*len(sequence))()
        for item,(key,up) in zip(inputs,sequence):
            item.type=1;item.payload.ki=KEYBOARD(key,0,2 if up else 0,0,0)
        user.SendInput.argtypes=[w.UINT,ctypes.POINTER(INPUT),ctypes.c_int];user.SendInput.restype=w.UINT
        if user.SendInput(len(inputs),inputs,ctypes.sizeof(INPUT))!=len(inputs):
            raise RuntimeError('Windows did not accept the voice-typing shortcut. Press Windows + H in the Jarvis text box.')

    def start(self):
        self.root.deiconify();self.root.lift();self.editor.focus_set();self.root.update_idletasks()
        self._key_sequence([(0x5b,False),(0x48,False),(0x48,True),(0x5b,True)])

    def dismiss(self):
        # Escape is best effort. Never toggle Win+H to stop: Windows may already
        # have stopped, and toggling then could turn capture back on.
        self._key_sequence([(0x1b,False),(0x1b,True)])
