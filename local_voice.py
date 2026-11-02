"""Offline female Kokoro voices. Model files stay outside the repository."""
from pathlib import Path
import io
import os
import threading

VOICES=[{'id':'af_heart','name':'Heart — warm female (free, local)'},
        {'id':'af_bella','name':'Bella — bright female (free, local)'},
        {'id':'af_nicole','name':'Nicole — gentle female (free, local)'},
        {'id':'bf_emma','name':'Emma — British female (free, local)'}]
LOCK=threading.Lock()
ENGINE=None


def ready():
    root=Path(os.environ['LOCALAPPDATA'])/'OpenJarvis/models'
    return all((root/name).is_file() for name in ['kokoro-v1.0.int8.onnx','voices-v1.0.bin'])


def synthesize(text,voice='af_heart'):
    global ENGINE
    from kokoro_onnx import Kokoro
    import soundfile
    root=Path(os.environ['LOCALAPPDATA'])/'OpenJarvis/models'
    if voice not in {v['id'] for v in VOICES}:voice='af_heart'
    with LOCK:
        if ENGINE is None:ENGINE=Kokoro(str(root/'kokoro-v1.0.int8.onnx'),str(root/'voices-v1.0.bin'))
        samples,rate=ENGINE.create(text,voice=voice,speed=1.05,lang='en-gb' if voice.startswith('bf_') else 'en-us')
    output=io.BytesIO();soundfile.write(output,samples,rate,format='WAV',subtype='PCM_16')
    return output.getvalue()
