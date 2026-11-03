"""Small native Windows voice console. The existing local service owns all audio."""
import json
import math
import os
import queue
import socket
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import scrolledtext

import httpx
from windows_dictation import WindowsTyping, WindowsEditor, interpret
from live_commands import next_command

BASE='http://127.0.0.1:8766'


def main():
    singleton=socket.socket()
    try: singleton.bind(('127.0.0.1',8768))
    except OSError: return
    token=(Path(os.environ['LOCALAPPDATA'])/'OpenJarvis/local-token.txt').read_text().strip()
    headers={'x-jarvis-token':token}
    events=queue.Queue(); closed=threading.Event()
    root=tk.Tk();root.title('Jarvis vocals');root.geometry('450x680');root.minsize(410,580)
    root.configure(bg='#090f20')
    state={'phase':'connecting','enabled':False,'approval':None,'last_reply':'','last_text':'','angle':0,'busy':False,
           'awake':False,'wake_sequence':None,'pending':False,'waiting_id':None,'resume_at':None,
           'draft':'','changed':0,'consumed':None,'dictation':False,'blocked':False,'submitted_prefix':''}
    def request(path,body=None):
        with httpx.Client(timeout=8,trust_env=False) as client:
            response=client.get(BASE+'/api/'+path,headers=headers) if body is None else client.post(BASE+'/api/'+path,headers=headers,json=body)
            if response.is_error:
                try: detail=response.json().get('detail','The service could not finish this action.')
                except ValueError: detail='The service could not finish this action.'
                raise RuntimeError(detail)
            return response.json()
    def act(path,body=None):
        def work():
            try: request(path,{} if body is None else body)
            except Exception as e: events.put(('error',str(e)))
        threading.Thread(target=work,daemon=True).start()
    tk.Label(root,text='J A R V I S',font=('Segoe UI',24,'bold'),bg='#090f20',fg='#e2eeff').pack(pady=(20,0))
    tk.Label(root,text='YOUR VOICE. YOUR WORKFLOW.',font=('Segoe UI',9),bg='#090f20',fg='#718bb7').pack()
    canvas=tk.Canvas(root,width=400,height=195,bg='#090f20',highlightthickness=0);canvas.pack()
    phase=tk.Label(root,text='Connecting…',font=('Segoe UI',14),bg='#090f20',fg='#66e1ef');phase.pack()
    hint=tk.Label(root,text='Say “Hey Jarvis”. Clear browser and media commands run automatically.',font=('Segoe UI',10),bg='#090f20',fg='#b2c5e5',wraplength=410);hint.pack(pady=8)
    controls=tk.Frame(root,bg='#090f20');controls.pack(pady=5)
    def button(parent,text,command,color='#17324e'):
        return tk.Button(parent,text=text,command=command,bg=color,fg='white',activebackground='#285378',relief='flat',padx=12,pady=7,font=('Segoe UI',10))
    mic=button(controls,'Enable listening',lambda:act('vocals/stop' if state['enabled'] else 'vocals/start'));mic.pack(side='left',padx=4)
    button(controls,'Stop task / voice',lambda:act('stop')).pack(side='left',padx=4)
    review=tk.Frame(root,bg='#17233b')
    review_text=tk.Label(review,bg='#17233b',fg='white',wraplength=405,justify='left');review_text.pack(padx=8,pady=5)
    def approve(value):
        if state['approval']:act('approve',{'id':state['approval']['id'],'accept':value})
    button(review,'Approve',lambda:approve(True)).pack(side='left',padx=8,pady=5)
    button(review,'Decline',lambda:approve(False)).pack(side='left',padx=8,pady=5)
    history=scrolledtext.ScrolledText(root,height=9,bg='#0e192e',fg='#d3e4ff',font=('Segoe UI',10),relief='flat',wrap='word',state='disabled');history.pack(fill='both',expand=True,padx=18,pady=8)
    def log(text):
        history.configure(state='normal');history.insert('end',text+'\n\n');history.see('end');history.configure(state='disabled')
    entry=WindowsEditor(root);entry.pack(fill='x',padx=18,pady=5)
    typing=WindowsTyping(root,entry)
    def dismiss():
        if state['dictation']:
            try:typing.dismiss()
            except RuntimeError:pass
        state['dictation']=False
    def begin_dictation():
        if state['busy'] and not state['approval']:return
        state['blocked']=False
        entry.configure(state='normal')
        try:
            typing.start();state['dictation']=True
            hint.configure(text='Wait for Windows “Listening”. Speak a browser or media command. Searches need sentence punctuation.')
        except Exception as e:
            hint.configure(text=str(e));log(str(e))
    def sleep_session():
        dismiss();state['awake']=False;state['resume_at']=None
        entry.delete(0,'end');entry.configure(state='readonly');root.focus_set();act('vocals/sleep')
        hint.configure(text='Sleeping. Say “Hey Jarvis” to begin again.')
    def send(event=None,automatic=None):
        text=entry.get().strip()
        action,parsed=automatic[:2] if automatic else interpret(text)
        if action=='sleep':sleep_session();return
        if action=='submit':text=parsed
        if not text or state['pending'] or (state['busy'] and not state['approval']):return
        state['submitted_prefix']=entry.get()[:automatic[2]] if automatic else entry.get()
        state['pending']=True;state['consumed']=entry.get();dismiss();entry.configure(state='readonly')
        log('You: '+text)
        def dispatch():
            try:events.put(('submitted',request('vocals/command',{'text':text})))
            except Exception as e:events.put(('submit_error',str(e)))
        threading.Thread(target=dispatch,daemon=True).start()
    entry.bind('<Return>',send)
    button(root,'Run typed task',send).pack(pady=(0,12))
    buttons=tk.Frame(root,bg='#090f20');buttons.pack(pady=(0,10))
    button(buttons,'Windows typing / resume',lambda:(act('vocals/activate') if not state['awake'] else begin_dictation())).pack(side='left',padx=3)
    button(buttons,'Go to sleep',sleep_session).pack(side='left',padx=3)
    def poll():
        while not closed.is_set():
            try: events.put(('status',request('status')))
            except Exception as e: events.put(('error','Connection: '+str(e)))
            closed.wait(.4)
    def tick():
        while not events.empty():
            kind,value=events.get_nowait()
            if kind=='error':hint.configure(text=value);continue
            if kind=='submit_error':
                state['pending']=False;state['blocked']=True;state['resume_at']=None
                entry.configure(state='normal');log('Not repeated. Check the task before resuming: '+value);hint.configure(text=value);continue
            if kind=='submitted':
                state['pending']=False;state['waiting_id']=value.get('id');entry.configure(state='normal')
                current=entry.get();prefix=state['submitted_prefix']
                if current.startswith(prefix):entry.set_text(current[len(prefix):].lstrip())
                else:state['blocked']=True;log('Windows revised the submitted text. Draft kept. Check it before resuming.')
                state['resume_at']=time.monotonic()+2;continue
            vocals=value.get('vocals',{});state['enabled']=vocals.get('enabled',False)
            state['awake']=vocals.get('awake',False);state['busy']=value['status']=='running'
            sequence=vocals.get('wake_sequence',0)
            if state['wake_sequence'] is None:state['wake_sequence']=sequence
            elif sequence!=state['wake_sequence']:
                state['wake_sequence']=sequence
                if state['awake']:root.after(200,begin_dictation)
            previous=state['phase']
            state['phase']='speaking' if value.get('voice',{}).get('speaking') else 'approval' if value.get('approval') else 'working' if value['status']=='running' else vocals.get('phase','off')
            phase.configure(text=state['phase'].replace('_',' ').capitalize())
            if vocals.get('error') or value.get('voice',{}).get('error'):hint.configure(text=vocals.get('error') or value['voice']['error'])
            mic.configure(text='Pause listening' if state['enabled'] else 'Enable listening')
            state['approval']=value.get('approval')
            speaking=value.get('voice',{}).get('speaking',False)
            if speaking or (state['busy'] and not state['approval']):
                dismiss();entry.configure(state='readonly');state['resume_at']=time.monotonic()+2
            elif not state['pending']:
                entry.configure(state='normal' if state['awake'] else 'readonly')
                if state['awake'] and not state['blocked'] and state['resume_at'] and time.monotonic()>state['resume_at']:
                    state['resume_at']=None
                    if not state['waiting_id'] or value['id']==state['waiting_id']:
                        state['waiting_id']=None;begin_dictation()
            if state['approval']:
                review_text.configure(text=state['approval']['description']);review.pack(before=history,fill='x',padx=18)
            else:review.pack_forget()
            if state['phase'] in ('recording your command','approval') and previous!=state['phase']:
                root.deiconify();root.lift()
            text=vocals.get('last_text','')
            if text and text!=state['last_text']:log('You: '+text);state['last_text']=text
            if value.get('id') and value['id']!=state['last_reply'] and value['status'] in ('done','error'):
                state['last_reply']=value['id'];log('Jarvis: '+(value.get('reply') or value.get('error','')))
                if value['status']=='error':
                    state['blocked']=True;state['resume_at']=None
                    log('Sequence paused. Later commands stay in the draft. Check the failed step before resuming.')
        draft=entry.get()
        if draft!=state['draft']:state['draft']=draft;state['changed']=time.monotonic()
        if state['awake'] and not state['blocked'] and not state['pending'] and draft!=state['consumed'] and time.monotonic()-state['changed']>1:
            complete=next_command(draft)
            if complete and not state['busy'] and not state['waiting_id'] and state['phase']!='speaking':
                state['consumed']=draft;send(automatic=complete)
            elif complete and complete[0]=='sleep':sleep_session()
        canvas.delete('all');state['angle']+=.05
        active=state['phase'] not in ('off','listening','connecting')
        color='#b5a1ff' if state['phase']=='speaking' else '#58e8ef' if active else '#376585'
        radius=59+(math.sin(state['angle']*3)*7 if active else math.sin(state['angle'])*2)
        for i in range(3):
            r=radius+i*9;canvas.create_oval(200-r,98-r,200+r,98+r,outline=color,width=2 if i==0 else 1)
        for i in range(30):
            angle=state['angle']+i*math.tau/30;r=radius+23+math.sin(angle*4)*5
            x=200+math.cos(angle)*r;y=98+math.sin(angle)*r
            canvas.create_oval(x-2,y-2,x+2,y+2,fill=color,outline='')
        canvas.create_text(200,98,text='J',fill='#ebf7ff',font=('Segoe UI',38,'bold'))
        root.after(40,tick)
    def close():
        closed.set()
        dismiss()
        try:request('vocals/stop',{})
        except Exception:pass
        root.destroy();singleton.close()
    root.protocol('WM_DELETE_WINDOW',close)
    threading.Thread(target=poll,daemon=True).start();tick()
    # Starting this explicitly named voice app enables the visible microphone.
    if not any(flag in __import__('sys').argv for flag in ('--smoke','--paused')):act('vocals/start')
    if '--smoke' in __import__('sys').argv:root.after(2500,close)
    root.mainloop()


if __name__=='__main__':main()
