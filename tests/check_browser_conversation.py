"""Fixtures for short cross-task browser follow-ups. No real account access."""
from pathlib import Path
import sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
import browser_commands as commands

SEARCH='<ytd-video-renderer><a id="video-title" href="/watch?v=first000001">Music fixture</a></ytd-video-renderer>'
VIDEO='''<div id="movie_player"><video class="html5-main-video"></video><button class="ytp-play-button" onclick="v._paused=false">Play</button></div><script>let v=document.querySelector('video');v._paused=true;Object.defineProperty(v,'paused',{get:()=>v._paused});Object.defineProperty(v,'readyState',{get:()=>4});Object.defineProperty(v,'duration',{get:()=>120});v.play=()=>{v._paused=false;return Promise.resolve()};</script>'''
GOOGLE='<div id="search"><a href="https://example.org/result"><h3>Fixture result</h3></a></div><div style="height:4000px"></div>'
SITE='<main><h1>Site fixture</h1><input aria-label="Search your photos" onkeydown="if(event.key===\'Enter\')document.body.dataset.searched=this.value"><button onclick="window.unsafeClicked=true">Send message</button></main>'
with tempfile.TemporaryDirectory() as tmp,sync_playwright() as pw:
    try:chrome=pw.chromium.launch(channel='chrome',headless=True)
    except Exception:chrome=pw.chromium.launch(headless=True)
    context=chrome.new_context()
    def serve(route):
        url=route.request.url
        body=SEARCH if 'youtube.com/results' in url else VIDEO if 'youtube.com/watch' in url else GOOGLE if 'google.com/search' in url else SITE
        route.fulfill(content_type='text/html; charset=utf-8',body=body)
    context.route('**/*',serve)
    page=context.new_page();page.goto('https://www.youtube.com/')
    class Fixture:
        def __init__(self):self.context=context;self.page=page;self.media_state_file=Path(tmp)/'media.json'
        def ensure(self):return self.page
    b=Fixture()
    info=commands.control(b,'search',target='youtube',query='music')
    assert info['message']=='YouTube results are ready for music.'
    assert 'https://' not in info['message']
    info=commands.control(b,**commands.parse('Play the first one')[1]);assert not info['player']['paused']
    info=commands.control(b,**commands.parse('Play it')[1]);assert not info['player']['paused']
    print('PASS: Search, then play the first one, then play it: no model clarification or approval round-trip.')
    for name in ['claude','google ai studio','google photos']:
        info=commands.control(b,'open',target=name);assert info['status']=='opened'
    commands.control(b,'search',query='holiday')
    assert b.page.locator('body').get_attribute('data-searched')=='holiday'
    assert not b.page.evaluate('window.unsafeClicked||false')
    print('PASS: Named sites open; an explicit search uses the search field, not a message button.')
    commands.control(b,'search',target='google',query='fixture')
    commands.control(b,'scroll',direction='down');assert b.page.evaluate('scrollY')>0
    commands.control(b,'reference');assert b.page.url=='https://example.org/result'
    print('PASS: Search, scroll down, then open it follows the first result without reading URLs aloud.')
    def block(url):raise ValueError('Blocked local URL')
    try:commands.control(b,'open',target='http://127.0.0.1:1234/',check_url=block);raise AssertionError('URL validation was skipped')
    except ValueError:pass
    chrome.close()
