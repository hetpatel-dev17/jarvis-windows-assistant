"""Bounded local filename search and reviewed-result opening. No shell commands."""
from collections import deque
from difflib import SequenceMatcher
from pathlib import Path
import ctypes
import os
import re
import threading
import time
import uuid

from file_browser import known_folder

SKIP={'.git','.venv','venv','node_modules','__pycache__','appdata','windows',
      'program files','program files (x86)','programdata','$recycle.bin',
      'system volume information','.cache','.codex','site-packages'}
PRIVATE=re.compile(r'api[ _-]?key|credentials|password|secret|token',re.I)
SAFE_EXT=set('pdf txt md rtf doc docx odt xls xlsx ods csv ppt pptx odp png jpg jpeg webp gif bmp tif tiff svg ico mp3 wav flac m4a aac ogg wma mp4 mkv avi mov webm mpeg mpg m4v zip 7z rar tar gz json yaml yml toml log'.split())


def words(text):
    return re.findall(r'[^\W_]+',str(text).casefold(),re.UNICODE)


def score(query,name):
    wanted=words(query);actual=words(name)
    if not wanted:return 0
    q=' '.join(wanted);n=' '.join(actual)
    if q==n:return 100
    if q in n:return 95
    if all(any(w in a for a in actual) for w in wanted):return 90
    ratios=[max((SequenceMatcher(None,w,a).ratio() for a in actual),default=0) for w in wanted]
    return round(sum(ratios)/len(ratios)*80) if min(ratios,default=0)>=.72 else 0


class WindowsOperator:
    def __init__(self,roots=None,opener=None):
        self.lock=threading.RLock()
        self.opener=opener or os.startfile
        self.roots=roots or self.default_roots()
        self.roots={k:Path(v).resolve() for k,v in self.roots.items() if Path(v).is_dir()}
        self.cwd=next(iter(self.roots.values()))
        self.revision=0;self.matches=[];self.message='';self.visible=False
        self.partial=False;self.scanned=0;self.query=''

    @staticmethod
    def default_roots():
        roots={
          'Desktop':known_folder('B4BFCC3A-DB2C-424C-B029-7FE99A87C641','Desktop'),
          'Downloads':known_folder('374DE290-123F-4565-9164-39C4925E467B','Downloads'),
          'Documents':known_folder('FDD39AD0-238F-46AF-ADB4-6C85480369C7','Documents'),
          'Pictures':known_folder('33E28130-4E1E-4676-835A-98395C3BC3BB','Pictures'),
          'Music':known_folder('4BD8D571-6D19-48D3-BE97-422220080E43','Music'),
          'Videos':known_folder('18989B1D-99B5-455B-841C-AB7C74E4DDFC','Videos'),
          'Home':Path.home()}
        mask=ctypes.windll.kernel32.GetLogicalDrives()
        for i in range(26):
            drive=f'{chr(65+i)}:\\'
            if mask&(1<<i) and ctypes.windll.kernel32.GetDriveTypeW(drive) in (2,3):
                roots[drive[:2]]=Path(drive)
        return roots

    def validate(self,path):
        raw=Path(path).expanduser()
        if str(raw).startswith('\\\\'):
            raise ValueError('Network paths are not enabled. Choose a local drive.')
        # Do not follow shortcuts, junctions or symlinks into another location.
        if any(p.is_symlink() or getattr(p,'is_junction',lambda:False)() for p in (raw,*raw.parents)):
            raise ValueError('That path is a link. Please choose its original folder.')
        p=raw.resolve(strict=True)
        if not any(p.is_relative_to(root) for root in self.roots.values()):
            raise ValueError('Choose a local drive or one of your personal folders.')
        if any(part.startswith('.') or PRIVATE.search(part) for part in p.parts[1:]):
            raise ValueError('That is a private settings or key location.')
        return p

    def location(self,target):
        target=target.strip().strip('"')
        if target.casefold() in ('here','this folder','current folder'):return self.cwd
        root=next((p for k,p in self.roots.items() if k.casefold()==target.casefold().rstrip('\\/')),None)
        if root:return root
        if target in ('..','back','up'):return self.validate(self.cwd.parent)
        supplied=Path(target)
        return self.validate(supplied if supplied.is_absolute() else self.cwd/supplied)

    def snapshot(self):
        with self.lock:
            return {'visible':self.visible,'revision':self.revision,'directory':str(self.cwd),
                    'roots':list(self.roots),'matches':list(self.matches),'message':self.message,
                    'partial':self.partial,'scanned':self.scanned,'query':self.query}

    def search(self,query,scope='here',cancelled=lambda:False,budget=6,max_entries=60000):
        if not words(query):raise ValueError('Give a few words from the file or folder name.')
        everywhere=scope.casefold() in ('computer','everywhere','all drives','my computer','windows')
        bases=list(dict.fromkeys(self.roots.values())) if everywhere else [self.location(scope)]
        if not all(p.is_dir() for p in bases):raise ValueError('Choose a folder to search in.')
        deadline=time.monotonic()+budget;queue=deque(bases);seen=set();found=[];count=0;partial=False;skipped=0
        while queue:
            if cancelled():raise RuntimeError('Stopped the file search.')
            if time.monotonic()>=deadline or count>=max_entries:partial=True;break
            folder=queue.popleft()
            key=os.path.normcase(str(folder))
            if key in seen:continue
            seen.add(key)
            try:
                with os.scandir(folder) as entries:
                    for entry in entries:
                        if cancelled():raise RuntimeError('Stopped the file search.')
                        if time.monotonic()>=deadline or count>=max_entries:partial=True;break
                        count+=1
                        if entry.name.startswith('.') or PRIVATE.search(entry.name):continue
                        try:
                            p=Path(entry.path)
                            if entry.is_symlink() or getattr(p,'is_junction',lambda:False)():continue
                            is_dir=entry.is_dir(follow_symlinks=False)
                            if is_dir and entry.name.casefold() in SKIP:continue
                            rank=score(query,entry.name)
                            if rank>=58:
                                checked=self.validate(p)
                                found.append({'id':uuid.uuid4().hex,'name':entry.name,'path':str(checked),'folder':is_dir,'score':rank})
                            if is_dir:queue.append(p)
                        except (OSError,ValueError):skipped+=1
            except (OSError,PermissionError):skipped+=1
        # Duplicate traversal roots can overlap; only show each real path once.
        unique={os.path.normcase(m['path']):m for m in found}
        matches=sorted(unique.values(),key=lambda m:(-m['score'],m['name'].casefold(),m['path'].casefold()))[:20]
        for i,m in enumerate(matches,1):m['number']=i
        with self.lock:
            if not everywhere:self.cwd=bases[0]
            self.matches=matches;self.revision+=1;self.visible=True;self.partial=partial;self.scanned=count;self.query=query
            message=f'I found {len(matches)} matching items.' if matches else 'I did not find a matching name in the folders checked.'
            if matches:message+=' '+ ' '.join(f'{m["number"]}. {m["name"]}.' for m in matches[:5])+' Say open match and its number.'
            if partial:message+=' This was a partial search. Choose a smaller folder to search more deeply.'
            if skipped:message+=' Some locations could not be checked.'
            if everywhere:message+=' System folders, private settings, and links were excluded.'
            self.message=message
            return {'status':'matches_ready',**self.snapshot()}

    def open_path(self,path):
        p=self.validate(path)
        if not p.is_dir() and p.suffix.casefold().lstrip('.') not in SAFE_EXT:
            raise ValueError('This file type is not enabled for opening. Documents, pictures, music, videos, and archives are supported.')
        self.opener(str(p))
        with self.lock:
            self.cwd=p if p.is_dir() else p.parent
            self.visible=True;self.revision+=1
            self.message=f'Asked Windows to open {p.name or str(p)}.'
        return {'status':'opened','path':str(p),'message':self.message}

    def control(self,action,query='',scope='here',target='',match_id='',cancelled=lambda:False):
        if cancelled():raise RuntimeError('Stopped by you.')
        if action=='status':return self.snapshot()
        if action=='search':return self.search(query,scope,cancelled)
        if action=='open_match':
            with self.lock:
                match=next((m for m in self.matches if m['id']==match_id or not match_id and str(m['number'])==target),None)
            if match is None:raise ValueError('That match is no longer in the latest search. Search again or choose a shown result.')
            return self.open_path(match['path'])
        if action=='open':
            try:return self.open_path(self.location(target))
            except FileNotFoundError:
                return self.search(target,scope,cancelled)
        raise ValueError('Unknown Windows file action.')
