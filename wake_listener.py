"""Opt-in offline wake phrases, followed by local Whisper command capture."""
from collections import deque
from pathlib import Path
import io,json,os,queue,re,threading,time,wave

PHRASES=['hey jarvis','hello jarvis','open jarvis','jarvis','jarvis what is up','jarvis whats up','[unk]']
PREFIX=re.compile(r'^\s*(?:(?:hey|hello|open|hi)[,\s]+)?(?:jarvis|jervis|jarves|jarvice)\b[\s,.!?;:]*',re.I)


def strip_wake(text):
    return PREFIX.sub('',text.strip(),count=1).strip()


def greeting(text):
    t=text.casefold()
    if 'what' in t and 'up' in t:return "Hey! What's up? What are we working on today?"
    if 'hello' in t:return "Hello! I'm here. What would you like to do?"
    return "Hey! I'm listening. What can I help you with?"


def is_greeting(text):
    return re.sub(r'[^a-z ]','',text.casefold()).strip() in ('','hi','hello','hey','whats up','what is up')


class WakeListener:
    def __init__(self,on_command,transcribe,voice,log=None,data_dir=None,busy=lambda:False):
        self.data=Path(data_dir or Path(os.environ['LOCALAPPDATA'])/'OpenJarvis')
        self.path=self.data/'wake-settings.json';self.on_command=on_command
        self.transcribe=transcribe;self.voice=voice;self.log=log
        self.busy=busy
        self.mode='windows';self.awake=False;self.wake_sequence=0
        self.enabled=False;self.phase='off';self.error='';self.thread=None;self.stop_event=threading.Event()
        self.lock=threading.RLock();self.last_text=''
        try:self.requested=bool(json.loads(self.path.read_text()).get('enabled',False))
        except (OSError,ValueError):self.requested=False
    def status(self):
        with self.lock:return {'enabled':self.enabled,'phase':self.phase,'error':self.error,'last_text':self.last_text,'phrases':PHRASES[:-1],'mode':self.mode,'awake':self.awake,'wake_sequence':self.wake_sequence}
    def sleep(self):
        with self.lock:self.awake=False;self.phase='listening' if self.enabled else 'off'
        return self.status()
    def activate(self):
        with self.lock:
            self.awake=True;self.wake_sequence+=1;self.phase='windows dictation'
        return self.status()
    def save(self):
        self.data.mkdir(parents=True,exist_ok=True)
        self.path.write_text(json.dumps({'enabled':self.enabled}),encoding='utf-8')
    def start(self):
        with self.lock:
            if self.thread and self.thread.is_alive():
                if self.stop_event.is_set():raise ValueError('The microphone is stopping. Try again in a moment.')
                return self.status()
            if not (self.data/'models/vosk-model-small-en-us-0.15').is_dir():raise ValueError('The wake model is missing. Run Setup first.')
            self.enabled=True;self.error='';self.phase='starting';self.stop_event=threading.Event();self.save()
            self.thread=threading.Thread(target=self._run,args=(self.stop_event,),daemon=True,name='jarvis-wake')
            self.thread.start();return self.status()
    def stop(self):
        self.stop_event.set()
        with self.lock:self.enabled=False;self.awake=False;self.phase='off';self.save()
        if self.thread and self.thread is not threading.current_thread():self.thread.join(timeout=1)
        return self.status()
    def _run(self,stop):
        try:
            import numpy as np
            import sounddevice as sd
            from vosk import Model,KaldiRecognizer,SetLogLevel
            SetLogLevel(-1)
            model=Model(str(self.data/'models/vosk-model-small-en-us-0.15'))
            detector=KaldiRecognizer(model,16000,json.dumps(PHRASES))
            packets=queue.Queue(maxsize=40)
            def callback(data,frames,timing,status):
                try:packets.put_nowait(bytes(data))
                except queue.Full:pass
            pre=deque(maxlen=20);recording=[];started=0;last_voice=0;follow_until=0;cooldown=0;noise=60;verify_wake=True
            with sd.RawInputStream(samplerate=16000,blocksize=1600,dtype='int16',channels=1,callback=callback):
                self.phase='listening'
                if self.log:self.log.record('microphone','Offline wake listening enabled.')
                while not stop.is_set():
                    try:chunk=packets.get(timeout=.2)
                    except queue.Empty:continue
                    now=time.monotonic()
                    if self.mode=='windows':
                        if self.awake:
                            detector.Reset();self.phase='windows dictation';continue
                        if self.voice.status()['speaking'] or self.busy():
                            detector.Reset();continue
                        if detector.AcceptWaveform(chunk):
                            heard=json.loads(detector.Result()).get('text','').strip()
                            if heard in ('hey jarvis','hello jarvis','open jarvis','jarvis'):
                                self.last_text=heard;self.activate();detector.Reset()
                        continue
                    if self.voice.status()['speaking'] or self.busy():
                        pre.clear();recording=[];detector.Reset();cooldown=now+.65
                        if follow_until:follow_until=now+12
                        self.phase='speaking' if self.voice.status()['speaking'] else 'working';continue
                    if now<cooldown:continue
                    energy=float(np.sqrt(np.mean(np.frombuffer(chunk,dtype=np.int16).astype(np.float32)**2)))
                    threshold=max(140,noise*2.7)
                    if not recording and not follow_until and energy<threshold:noise=.98*noise+.02*energy
                    if recording:
                        recording.append(chunk)
                        if energy>threshold:last_voice=now
                        if (now-last_voice>.8 and now-started>.55) or now-started>15:
                            audio=b''.join(recording);recording=[];self.phase='understanding'
                            output=io.BytesIO()
                            with wave.open(output,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(audio)
                            text=self.transcribe(output.getvalue(),'wav').strip()
                            if stop.is_set():break
                            # A false keyword detection cannot turn unrelated room speech into a command.
                            if verify_wake and not PREFIX.match(text):
                                pre.clear();detector.Reset();self.phase='listening';continue
                            self.last_text=text
                            command=strip_wake(text)
                            if command and not is_greeting(command):
                                try:
                                    self.on_command(command);self.error=''
                                except Exception as error:
                                    self.error='That command could not start. '+str(error)[:160]
                                follow_until=0;self.phase='listening'
                            else:
                                self.voice.submit(greeting(text),'wake:'+str(time.monotonic_ns()));follow_until=time.monotonic()+12;self.phase='waiting for your command'
                            pre.clear();detector.Reset();cooldown=time.monotonic()+.25
                            # Drop stale audio collected during transcription and dispatch.
                            while not packets.empty():
                                try:packets.get_nowait()
                                except queue.Empty:break
                        continue
                    if follow_until:
                        if now>follow_until:follow_until=0;self.phase='listening'
                        elif energy>threshold:
                            recording=list(pre)+[chunk];started=last_voice=now;follow_until=0;verify_wake=False;self.phase='recording your command'
                        pre.append(chunk);continue
                    pre.append(chunk)
                    final=detector.AcceptWaveform(chunk)
                    heard=json.loads(detector.Result() if final else detector.PartialResult()).get('text' if final else 'partial','')
                    if re.search(r'\bjarvis\b',heard):
                        recording=list(pre);started=last_voice=now;verify_wake=True;self.phase='recording your command';detector.Reset()
                    else:self.phase='listening'
        except Exception as error:
            self.error='Voice listening stopped: '+str(error)[:200]
            if self.log:self.log.record('microphone',type(error).__name__+': '+str(error),status='error')
            self.enabled=False;self.save();self.phase='error'
        finally:
            if stop.is_set():self.phase='off'
