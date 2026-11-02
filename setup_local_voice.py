"""Download and verify the existing optional offline speech models."""
from pathlib import Path
import hashlib,os

ASSETS=[
 ('kokoro-v1.0.int8.onnx','6e742170d309016e5891a994e1ce1559c702a2ccd0075e67ef7157974f6406cb'),
 ('voices-v1.0.bin','bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d')]


def install():
    import httpx
    root=Path(os.environ['LOCALAPPDATA'])/'OpenJarvis/models';root.mkdir(parents=True,exist_ok=True)
    for name,digest in ASSETS:
        target=root/name
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()==digest:continue
        temp=target.with_suffix(target.suffix+'.part')
        with httpx.stream('GET','https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/'+name,follow_redirects=True,timeout=120) as response:
            response.raise_for_status()
            with temp.open('wb') as output:
                for chunk in response.iter_bytes():output.write(chunk)
        if hashlib.sha256(temp.read_bytes()).hexdigest()!=digest:raise RuntimeError('Voice model download checksum failed.')
        temp.replace(target)

if __name__=='__main__':install()
