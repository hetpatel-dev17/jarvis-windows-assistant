"""Install the pinned Apache-2.0 Vosk small English wake model."""
from pathlib import Path
import hashlib
import os
import zipfile
import httpx

def install():
    root=Path(os.environ['LOCALAPPDATA'])/'OpenJarvis/models'
    root.mkdir(parents=True,exist_ok=True)
    name='vosk-model-small-en-us-0.15'
    digest='30f26242c4eb449f948e42cb302dd7a686cb29a3423a8367f99ff41780942498'
    target=root/(name+'.zip')
    if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest()!=digest:
        temporary=target.with_suffix('.part')
        try:
            with httpx.stream('GET','https://alphacephei.com/vosk/models/'+name+'.zip',follow_redirects=True,timeout=60) as response:
                response.raise_for_status()
                with temporary.open('wb') as output:
                    for chunk in response.iter_bytes():output.write(chunk)
            if hashlib.sha256(temporary.read_bytes()).hexdigest()!=digest:raise RuntimeError('Wake model checksum failed.')
            temporary.replace(target)
        finally:temporary.unlink(missing_ok=True)
    with zipfile.ZipFile(target) as archive:
        if any(not (root/item.filename).resolve().is_relative_to(root.resolve()) for item in archive.infolist()):raise ValueError('Invalid model archive paths.')
        archive.extractall(root)
    print('Offline wake model is ready.')

if __name__=='__main__':install()
