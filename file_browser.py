"""A small, voice-navigable picker for the user's document folders."""
from pathlib import Path
import ctypes
from ctypes import wintypes
import threading
import uuid
import re
import json
import os


def known_folder(value,fallback):
    class GUID(ctypes.Structure):
        _fields_=[('a',wintypes.DWORD),('b',wintypes.WORD),('c',wintypes.WORD),('d',ctypes.c_ubyte*8)]
    guid=GUID.from_buffer_copy(uuid.UUID(value).bytes_le)
    pointer=ctypes.c_void_p()
    result=ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(guid),0,None,ctypes.byref(pointer))
    if result!=0:
        return Path.home()/fallback
    try:
        return Path(ctypes.wstring_at(pointer))
    finally:
        ctypes.windll.ole32.CoTaskMemFree(pointer)


class FileBrowser:
    def __init__(self,roots=None):
        self.state_path=None if roots else Path(os.environ['LOCALAPPDATA'])/'OpenJarvis/file-picker.json'
        self.roots=roots or {
            'Desktop':known_folder('B4BFCC3A-DB2C-424C-B029-7FE99A87C641','Desktop'),
            'Downloads':known_folder('374DE290-123F-4565-9164-39C4925E467B','Downloads'),
            'Documents':known_folder('FDD39AD0-238F-46AF-ADB4-6C85480369C7','Documents')}
        self.roots={name:Path(path).resolve() for name,path in self.roots.items() if Path(path).exists()}
        self.cwd=next(iter(self.roots.values()))
        self.selected=None
        self.visible=False
        self.revision=0
        self.lock=threading.RLock()
        if self.state_path:
            try:
                saved=json.loads(self.state_path.read_text())
                folder=self.validate(saved['directory'])
                if folder.is_dir():
                    self.cwd=folder;self.visible=True
                if saved.get('selected'):
                    chosen=self.validate(saved['selected'])
                    if chosen.is_file():self.selected=chosen
            except (OSError,ValueError,KeyError):
                pass

    def save(self):
        if self.state_path:
            self.state_path.parent.mkdir(parents=True,exist_ok=True)
            self.state_path.write_text(json.dumps({'directory':str(self.cwd),'selected':str(self.selected) if self.selected else None}),encoding='utf-8')

    def validate(self,path):
        path=Path(path).expanduser().resolve(strict=True)
        if not any(path.is_relative_to(root) for root in self.roots.values()):
            raise ValueError('Choose a file in Desktop, Downloads, or Documents.')
        if path.name.startswith('.') or re.search(r'api[ _-]?key|credentials|password|secret|token',path.name,re.I):
            raise ValueError('That looks like a private settings or key file. It is not available for upload.')
        if path.suffix.lower() in ('.exe','.dll','.lnk','.bat','.cmd','.ps1','.pem','.key'):
            raise ValueError('Choose a document, image, or other supported attachment.')
        return path

    def listing(self):
        with self.lock:
            entries=[]
            for path in sorted(self.cwd.iterdir(),key=lambda p:(not p.is_dir(),p.name.casefold())):
                try:
                    path=self.validate(path)
                    entries.append({'name':path.name,'folder':path.is_dir(),'bytes':path.stat().st_size if path.is_file() else None})
                except (OSError,ValueError):
                    continue
                if len(entries)>=200:
                    break
            return {'visible':self.visible,'revision':self.revision,'directory':str(self.cwd),'roots':list(self.roots),
                    'entries':entries,'selected':str(self.selected) if self.selected else None,
                    'message':f'Opened {self.cwd.name}. {len(entries)} items are shown.'}

    def navigate(self,target):
        with self.lock:
            root=next((path for name,path in self.roots.items() if name.casefold()==target.strip().casefold()),None)
            if root:
                path=root
            elif target in ('..','back','up'):
                path=self.cwd.parent
            else:
                supplied=Path(target)
                if supplied.is_absolute():
                    path=supplied
                else:
                    matches=[p for p in self.cwd.iterdir() if p.name.casefold()==target.strip().casefold()]
                    if len(matches)!=1:
                        raise ValueError('That exact folder was not found. Check the file list in Jarvis.')
                    path=matches[0]
            path=self.validate(path)
            if not path.is_dir():
                return self.select(str(path))
            self.cwd=path;self.selected=None;self.visible=True;self.revision+=1
            self.save()
            return self.listing()

    def select(self,target):
        with self.lock:
            supplied=Path(target)
            if supplied.is_absolute():
                path=supplied
            else:
                clean=lambda s:re.sub(r'[^a-z0-9]','',s.casefold())
                matches=[p for p in self.cwd.iterdir() if p.is_file() and (p.name.casefold()==target.strip().casefold() or clean(p.stem)==clean(target))]
                if not matches and clean(target) in ('pdf','thepdf','pdffile'):
                    matches=[p for p in self.cwd.iterdir() if p.suffix.lower()=='.pdf']
                if len(matches)!=1:
                    raise ValueError('That exact file was not found. Include its extension if needed.')
                path=matches[0]
            path=self.validate(path)
            if not path.is_file():
                raise ValueError('That is a folder. Open it and choose a file inside.')
            if path.stat().st_size>25*1024*1024:
                raise ValueError('Jarvis currently supports attachments up to 25 MB.')
            self.cwd=path.parent;self.selected=path;self.visible=True;self.revision+=1
            self.save()
            return {'status':'selected','path':str(path),'name':path.name,'bytes':path.stat().st_size,'message':f'Selected {path.name}. It has not been uploaded.'}

    def attachment(self,path=None):
        with self.lock:
            if path:
                self.select(path)
            if self.selected is None:
                raise ValueError('First choose a file in the Jarvis file picker.')
            return self.validate(self.selected)
