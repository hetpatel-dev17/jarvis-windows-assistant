"""One Windows audio channel, with server-side event deduplication."""
from collections import OrderedDict
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import threading
import uuid
import winsound
import io
import wave
import time


class SingleVoice:
    def __init__(self,provider=None,play=None,data_dir=None):
        self.data=Path(data_dir or Path(os.environ['LOCALAPPDATA'])/'OpenJarvis')
        self.data.mkdir(parents=True,exist_ok=True)
        self.path=self.data/'voice-settings.json'
        self.lock=threading.RLock()
        self.pool=concurrent.futures.ThreadPoolExecutor(max_workers=1,thread_name_prefix='jarvis-voice')
        self.generation=0
        self.seen=OrderedDict()
        self.cache=OrderedDict()
        self.speaking=False
        self.error=''
        self.provider=provider or self._provider
        self.play=play or winsound.PlaySound
        self.settings={'enabled':True,'voice':'af_heart','provider':'local'}
        try:
            self.update(json.loads(self.path.read_text()),save=False)
        except (OSError,ValueError,TypeError):
            pass

    def update(self,data,save=True):
        with self.lock:
            previous=dict(self.settings)
            if 'provider' in data:
                if data['provider'] not in ('local','elevenlabs'):raise ValueError('Choose local voice or ElevenLabs.')
                self.settings['provider']=data['provider']
            elif 'voice' in data and str(data['voice']) not in ('af_heart','af_bella','af_nicole','bf_emma'):
                self.settings['provider']='elevenlabs'
            if 'enabled' in data:
                self.settings['enabled']=bool(data['enabled'])
            if 'voice' in data:
                voice=str(data['voice'])
                if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',voice):
                    raise ValueError('Invalid voice selection.')
                self.settings['voice']=voice
            if self.settings['provider']=='local' and self.settings['voice'] not in ('af_heart','af_bella','af_nicole','bf_emma'):
                self.settings['voice']='af_heart'
            if previous!=self.settings:self.stop()
            if save:
                self.path.write_text(json.dumps(self.settings),encoding='utf-8')
            if not self.settings['enabled']:
                self.stop()
            return dict(self.settings)

    def status(self):
        with self.lock:
            return {**self.settings,'speaking':self.speaking,'error':self.error}

    def stop(self):
        with self.lock:
            self.generation+=1
            self.speaking=False
            self.play(None,0)

    def submit(self,text,event_id,voice=None,force=False):
        with self.lock:
            if event_id in self.seen or not text.strip() or (not force and not self.settings['enabled']):
                return False
            self.seen[event_id]=True
            while len(self.seen)>256:
                self.seen.popitem(last=False)
            self.stop()
            generation=self.generation
            selected=voice or self.settings['voice']
            self.pool.submit(self._run,text[:12000],selected,generation)
            return True

    def _provider(self,text,voice):
        if self.settings['provider']=='local':
            from local_voice import synthesize
            return synthesize(text,voice)
        from key_store import load_key
        from openjarvis.speech.elevenlabs_tts import ElevenLabsTTSBackend
        return ElevenLabsTTSBackend(api_key=load_key()).synthesize(text,voice_id=voice,output_format='wav').audio

    def _run(self,text,voice,generation):
        # Chunking keeps a long answer sequential. There is only one worker.
        words=text.split()
        chunks=[]
        current=[]
        length=0
        for word in words:
            if current and length+len(word)>1800:
                chunks.append(' '.join(current));current=[];length=0
            current.append(word);length+=len(word)+1
        if current:
            chunks.append(' '.join(current))
        try:
            for chunk in chunks:
                with self.lock:
                    if generation!=self.generation:
                        return
                    self.speaking=True
                    self.error=''
                key=hashlib.sha256((self.settings['provider']+'\0'+voice+'\0'+chunk).encode()).hexdigest()
                audio=self.cache.get(key)
                if audio is None:
                    audio=self.provider(chunk,voice)
                    self.cache[key]=audio
                    while len(self.cache)>4:
                        self.cache.popitem(last=False)
                with self.lock:
                    if generation!=self.generation:
                        return
                wav=self.data/('voice-'+uuid.uuid4().hex+'.wav')
                try:
                    wav.write_bytes(audio)
                    with wave.open(io.BytesIO(audio),'rb') as reader:
                        duration=reader.getnframes()/reader.getframerate()
                    with self.lock:
                        if generation!=self.generation:
                            return
                        self.play(str(wav),winsound.SND_FILENAME|winsound.SND_ASYNC)
                    deadline=time.monotonic()+duration+.15
                    while time.monotonic()<deadline:
                        with self.lock:
                            if generation!=self.generation:
                                return
                        time.sleep(.03)
                finally:
                    try:
                        wav.unlink(missing_ok=True)
                    except OSError:
                        pass
        except Exception:
            with self.lock:
                if generation==self.generation:
                    self.error='Local voice could not play. Check the local voice models in Setup.' if self.settings['provider']=='local' else 'Voice could not play. Check ElevenLabs credits and voice access.'
        finally:
            with self.lock:
                if generation==self.generation:
                    self.speaking=False
