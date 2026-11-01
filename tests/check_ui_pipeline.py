"""Exercise recording -> transcription -> command -> search -> chosen match.

All HTTP APIs and the Windows opener are fixtures. No account access or uploads.
"""
from pathlib import Path
from urllib.parse import urlparse
import json,sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import command_routes
from windows_operator import WindowsOperator
from playwright.sync_api import sync_playwright,expect

root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp,sync_playwright() as pw:
    folder=Path(tmp);(folder/'Project Roadmap.pdf').write_bytes(b'fixture')
    opened=[];operator=WindowsOperator({'Desktop':folder},opened.append)
    calls=[];state={'id':'','status':'idle','reply':'','error':'','steps':[],'approval':None,'browser_mode':'control','files_revision':0,'voice':{'speaking':False,'error':''}}
    def fake(route):
        path=urlparse(route.request.url).path
        if path=='/':return route.fulfill(content_type='text/html',body=(root/'index.html').read_text(encoding='utf-8'))
        if path=='/ui.js':return route.fulfill(content_type='text/javascript',body=(root/'ui.js').read_text(encoding='utf-8'))
        data=route.request.post_data_json if route.request.method=='POST' and path!='/api/transcribe' else None
        calls.append((path,data))
        if path=='/api/status':body={**state,'windows_revision':operator.revision}
        elif path=='/api/windows':
            body=operator.control(**data) if data else operator.snapshot()
        elif path=='/api/chat':
            command=command_routes.parse(data['text']);assert command[0]=='windows_operator',command
            result=operator.control(**command[1]);state.update(id=str(len(calls)),status='done',reply=result['message'])
            body={'id':state['id']}
        elif path=='/api/transcribe':body={'text':'Find roadmap on Desktop'}
        elif path=='/api/voices':body=[{'id':'fixture','name':'Fixture'}]
        elif path=='/api/voice/settings':body={'enabled':False,'voice':'fixture'}
        elif path=='/api/files':body={'visible':False,'directory':'Fixture','roots':[],'entries':[],'selected':None,'revision':0}
        else:body={'ok':True}
        route.fulfill(content_type='application/json',body=json.dumps(body))
    try:browser=pw.chromium.launch(channel='chrome',headless=True)
    except Exception:browser=pw.chromium.launch(headless=True)
    context=browser.new_context();context.route('**/*',fake)
    pages=[context.new_page(),context.new_page()]
    for page in pages:page.goto('http://127.0.0.1:8766/#fixture-token',wait_until='networkidle')
    page=pages[0]
    page.evaluate('''()=>{
        navigator.mediaDevices.getUserMedia=async()=>({getTracks:()=>[{stop(){}}]});
        window.MediaRecorder=class {
            constructor(){this.state='inactive';this.mimeType='audio/webm'}
            start(){this.state='recording'}
            stop(){this.state='inactive';this.ondataavailable({data:new Blob(['fixture'],{type:this.mimeType})});this.onstop()}
        };
    }''')
    page.locator('#record').click();expect(page.locator('#record')).to_have_class('recording')
    page.locator('#record').click()
    expect(page.locator('#windowsMatches button')).to_have_count(1,timeout=10000)
    assert any(p=='/api/chat' and d['text']=='Find roadmap on Desktop' for p,d in calls)
    assert opened==[]
    page.evaluate("executeSpoken('Open match one')")
    assert len(opened)==1 and Path(opened[0]).name=='Project Roadmap.pdf'
    count=len([p for p,d in calls if p=='/api/chat'])
    page.locator('#autoRunVoice').uncheck()
    page.locator('#record').click();expect(page.locator('#record')).to_have_class('recording');page.locator('#record').click()
    expect(page.locator('#micHint')).to_have_text('Check the words. Press Run task to continue.')
    assert page.locator('#prompt').input_value()=='Find roadmap on Desktop'
    assert len([p for p,d in calls if p=='/api/chat'])==count
    assert not any(p=='/api/speak' for p,d in calls),'Tabs replayed speech'
    assert len(context.pages)==2
    browser.close()
print('PASS: Recorded command -> transcript -> automatic filename search -> numbered result -> chosen open.')
print('PASS: Review mode leaves the transcript unsent. Two tabs never replay speech.')
