from pathlib import Path
from urllib.parse import urlparse,parse_qs
import sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import command_routes as routes,media_controls as media
from playwright.sync_api import sync_playwright

cases={
 'mute':('youtube_control','mute',None),
 'unmute YouTube':('youtube_control','unmute',None),
 'Volume plus':('youtube_control','volume_up',None),
 'Lower volume':('youtube_control','volume_down',None),
 'Volume max':('youtube_control','set_volume',100),
 'Full volume please':('youtube_control','set_volume',100),
 'Set YouTube volume to 30 percent':('youtube_control','set_volume',30),
 'Volume minimum':('youtube_control','set_volume',0),
 'Mute the computer':('desktop_control','mute',None),
 'Computer volume up':('desktop_control','volume_up',None),
 'Set system volume to 50 percent':('desktop_control','set_volume',50),
 'Play the next video on YouTube':('youtube_control','next',None),
 'YouTube previous video':('youtube_control','previous',None),
 'Skip this video':('youtube_control','next',None),
}
for text,(tool,action,level) in cases.items():
    actual=routes.parse(text)
    assert actual and actual[0]==tool and actual[1]['action']==action,(text,actual)
    if level is not None:assert actual[1]['level']==level
assert routes.parse('Ask ChatGPT: mute the computer')[0]=='chatgpt'
assert routes.parse('Explain maximum volume') is None
print('PASS: Natural video, mute, maximum, and explicit computer phrases route correctly.',flush=True)

with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp, sync_playwright() as pw:
    try:chrome=pw.chromium.launch(channel='chrome',headless=True)
    except Exception:chrome=pw.chromium.launch(headless=True)
    context=chrome.new_context()
    def serve(route):
        vid=parse_qs(urlparse(route.request.url).query).get('v',['first000001'])[0]
        html='''<video id="preview" style="display:none"></video><div id="movie_player"><video class="html5-main-video"></video><button class="ytp-play-button" onclick="v._paused=false">Play</button><a style="display:none" class="ytp-next-button" href="/watch?v=next0000001">Next</a></div><script>
        const v=document.querySelector('#movie_player video'),p=document.querySelector('#movie_player');
        v._paused=true;Object.defineProperty(v,'paused',{get:()=>v._paused});Object.defineProperty(v,'readyState',{get:()=>4});
        Object.defineProperty(v,'duration',{get:()=>120});v.pause=()=>v._paused=true;
        p.setVolume=n=>{v.volume=n/100;window.volumeCalls=(window.volumeCalls||0)+1};p.mute=()=>v.muted=true;p.unMute=()=>v.muted=false;
        window.loadedId='old00000000';p.getVideoData=()=>({video_id:window.loadedId});
        setTimeout(()=>window.loadedId='VIDEO_ID',600);
        </script>'''.replace('VIDEO_ID',vid)
        route.fulfill(status=200,content_type='text/html',body=html)
    context.route('**/*',serve)
    page=context.new_page();page.goto('https://www.youtube.com/watch?v=first000001')
    class Fixture:
        def __init__(self):self.context=context;self.page=page;self.media_state_file=Path(tmp)/'media.json'
        def ensure(self):return self.page
    b=Fixture()
    for action,level,expected,muted in [
        ('set_volume',30,30,False),('volume_up',None,40,False),('volume_down',None,30,False),
        ('mute',None,30,True),('unmute',None,30,False),('set_volume',100,100,False),
        ('set_volume',0,0,False),('unmute',None,50,False),('set_volume',150,100,False),
    ]:
        result=media.control(b,action,level=level)
        assert result['player']['volume']==expected and result['player']['muted']==muted,(action,result)
    assert page.locator('#preview').evaluate('(v)=>v.volume')==1
    assert page.evaluate('window.volumeCalls')==9
    print('PASS: Actual main player, native player volume API, mute/unmute, zero-volume recovery, and bounds.',flush=True)
    media.record(b,page.url)
    media.record(b,page.url+'&t=20')
    assert len(b.media_history)==1,'Same video with a different timestamp duplicated history'
    start=time.monotonic();media.control(b,'next')
    assert time.monotonic()-start>=.5,'Claimed success before the requested video loaded'
    assert media.video_id(page.url)=='next0000001'
    media.control(b,'previous');assert media.video_id(page.url)=='first000001'
    media.control(b,'next');assert media.video_id(page.url)=='next0000001'
    print('PASS: Hidden next control, delayed new-player load, previous, forward history, and timestamp identity.',flush=True)
    chrome.close()
