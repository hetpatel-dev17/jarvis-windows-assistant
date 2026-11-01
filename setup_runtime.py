"""Download only the local Whisper model; no account data is included."""
from pathlib import Path
import os

if __name__=='__main__':
    from huggingface_hub import snapshot_download
    folder=Path(os.environ['LOCALAPPDATA'])/'OpenJarvis/models/whisper-base'
    snapshot_download(repo_id='Systran/faster-whisper-base',local_dir=str(folder))
