"""Archived Browser Use/Ollama trial. The command-line entry point is paused.

Do not rerun this trial or bypass the recorded Windows block.
The public result contains only observations about a generated local demo page.
"""
from pathlib import Path
import argparse,asyncio,json,os,tempfile,threading,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer

os.environ['ANONYMIZED_TELEMETRY']='false'
os.environ['BROWSER_USE_TELEMETRY']='false'
os.environ['DO_NOT_TRACK']='1'

PAGE=b'''<!doctype html><meta charset="utf-8"><title>Parts demo</title>
<button onclick="document.querySelector('#catalog').hidden=false">Browse parts</button>
<section id="catalog" hidden><label>Search parts <input aria-label="Search parts" oninput="document.querySelector('#blue').hidden=!this.value.toLowerCase().includes('blue')"></label>
<button id="blue" hidden onclick="document.querySelector('#detail').hidden=false">Blue sensor</button></section>
<section id="detail" hidden><h1>Blue sensor</h1><p>SKU: DEMO-482</p></section>'''


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(PAGE)
    def log_message(self,*args):pass


async def run(model,report):
    started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='jarvis-browser-pilot-') as folder:
        temp=Path(folder)
        os.environ['BROWSER_USE_CONFIG_DIR']=str(temp/'config')
        os.environ['XDG_CONFIG_HOME']=str(temp/'config')
        from browser_use import Agent,Browser,ChatOllama,Tools
        from browser_use.browser import BrowserProfile
        chrome=next((p for p in [Path(r'C:\Program Files\Google\Chrome\Application\chrome.exe'),Path(r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe')] if p.exists()),None)
        if chrome is None:raise RuntimeError('Chrome or Edge is required for this Windows pilot.')
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        url=f'http://127.0.0.1:{server.server_port}/'
        profile=BrowserProfile(executable_path=str(chrome),headless=True,user_data_dir=str(temp/'profile'),allowed_domains=['127.0.0.1'],accept_downloads=False,auto_download_pdfs=False,downloads_path=str(temp/'downloads'))
        browser=Browser(browser_profile=profile)
        all_actions=list(Tools().registry.registry.actions)
        allowed={'navigate','click','input','scroll','done','wait','go_back'}
        tools=Tools(exclude_actions=[name for name in all_actions if name not in allowed])
        llm=ChatOllama(model=model,host='http://127.0.0.1:11434',timeout=45,ollama_options={'temperature':0,'num_ctx':8192,'num_predict':900})
        agent=Agent(task=f'Open {url}. Find the blue sensor in the parts catalog. Open its details and report its SKU. Do not guess. Use only this local demo.',llm=llm,browser_session=browser,tools=tools,use_vision=False,use_judge=False,use_thinking=False,flash_mode=True,enable_planning=False,max_actions_per_step=3,max_failures=1,llm_timeout=45,step_timeout=60,final_response_after_failure=False,file_system_path=str(temp/'agent-files'),calculate_cost=False)
        result={'framework':'browser-use 0.13.14','model':model,'isolated':True,'saved_accounts_used':False,'allowed_actions':sorted(allowed),'success':False}
        try:
            history=await asyncio.wait_for(agent.run(max_steps=6),timeout=150)
            final=history.final_result() or ''
            cdp=await browser.get_or_create_cdp_session()
            observed=await cdp.cdp_client.send.Runtime.evaluate(params={'expression':'!!document.querySelector("#detail") && !document.querySelector("#detail").hidden','returnByValue':True},session_id=cdp.session_id)
            opened=observed.get('result',{}).get('value') is True
            result.update(success=bool(history.is_successful() and 'DEMO-482' in final and opened),detail_open=opened,final_result=final[:1000],steps=len(history.history))
        except Exception as error:result.update(error=type(error).__name__+': '+str(error)[:700])
        finally:
            await browser.kill();server.shutdown();server.server_close()
        result['elapsed_seconds']=round(time.monotonic()-started,1)
        report.parent.mkdir(parents=True,exist_ok=True);report.write_text(json.dumps(result,indent=2),encoding='utf-8')
        print('PILOT_RESULT '+json.dumps(result),flush=True)


if __name__=='__main__':
    raise SystemExit('This candidate trial is paused. Read references/tool-evaluation.md. Do not rerun or bypass the Windows security block.')
