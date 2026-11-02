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
    state={'phase':'connecting','enabled':False,'approval':None,'last_reply':'','last_text':'','angle':0,'busy':False}
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
    hint=tk.Label(root,text='Say “Hey Jarvis”. Pause. Then speak your task.',font=('Segoe UI',10),bg='#090f20',fg='#b2c5e5',wraplength=410);hint.pack(pady=8)
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
    entry=tk.Entry(root,bg='#182640',fg='white',insertbackground='white',font=('Segoe UI',11));entry.pack(fill='x',padx=18,pady=5)
    def send(event=None):
        text=entry.get().strip()
        if text:act('chat',{'text':text});log('You: '+text);entry.delete(0,'end')
    entry.bind('<Return>',send)
    button(root,'Run typed task',send).pack(pady=(0,12))
    def poll():
        while not closed.is_set():
            try: events.put(('status',request('status')))
            except Exception as e: events.put(('error','Connection: '+str(e)))
            closed.wait(.4)
    def tick():
        while not events.empty():
            kind,value=events.get_nowait()
            if kind=='error':hint.configure(text=value);continue
            vocals=value.get('vocals',{});state['enabled']=vocals.get('enabled',False)
            previous=state['phase']
            state['phase']='speaking' if value.get('voice',{}).get('speaking') else 'approval' if value.get('approval') else 'working' if value['status']=='running' else vocals.get('phase','off')
            phase.configure(text=state['phase'].replace('_',' ').capitalize())
            hint.configure(text=vocals.get('error') or value.get('voice',{}).get('error') or ('Say “Hey Jarvis”. Pause. Then speak your task.' if state['enabled'] else 'Microphone is off. Enable listening when ready.'))
            mic.configure(text='Pause listening' if state['enabled'] else 'Enable listening')
            state['approval']=value.get('approval')
            if state['approval']:
                review_text.configure(text=state['approval']['description']);review.pack(before=history,fill='x',padx=18)
            else:review.pack_forget()
            if state['phase'] in ('recording your command','approval') and previous!=state['phase']:
                root.deiconify();root.lift()
            text=vocals.get('last_text','')
            if text and text!=state['last_text']:log('You: '+text);state['last_text']=text
            if value.get('id') and value['id']!=state['last_reply'] and value['status'] in ('done','error'):
                state['last_reply']=value['id'];log('Jarvis: '+(value.get('reply') or value.get('error','')))
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
        try:request('vocals/stop',{})
        except Exception:pass
        root.destroy();singleton.close()
    root.protocol('WM_DELETE_WINDOW',close)
    threading.Thread(target=poll,daemon=True).start();tick()
    # Starting this explicitly named voice app enables the visible microphone.
    act('vocals/start')
    if '--smoke' in __import__('sys').argv:root.after(2500,close)
    root.mainloop()


if __name__=='__main__':main()
