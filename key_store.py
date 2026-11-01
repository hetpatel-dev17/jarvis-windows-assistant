"""Read the Windows encrypted ElevenLabs key. Never log its contents."""
import ctypes
from ctypes import wintypes
import os
from pathlib import Path


def load_key():
    encrypted=(Path(os.environ['LOCALAPPDATA'])/'OpenJarvis'/'secrets'/'elevenlabs.dpapi').read_text().strip()
    raw=bytes.fromhex(encrypted)
    class Blob(ctypes.Structure):
        _fields_=[('size',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_ubyte))]
    buffer=ctypes.create_string_buffer(raw)
    source=Blob(len(raw),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_ubyte)))
    output=Blob()
    if not ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(source),None,None,None,None,0,ctypes.byref(output)):
        raise RuntimeError('Windows could not unlock your ElevenLabs key.')
    try:
        return ctypes.string_at(output.data,output.size).decode('utf-16-le')
    finally:
        ctypes.memset(output.data,0,output.size)
        ctypes.windll.kernel32.LocalFree(output.data)
