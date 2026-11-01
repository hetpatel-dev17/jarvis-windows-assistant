import math
import time
from urllib.parse import urlparse,urljoin,parse_qs
from pathlib import Path
import os,json
from site_workflows import youtube_search,site_page,visible_first


def state(page):
    video=player_video(page)
    result=video.evaluate('(v)=>({paused:v.paused,time:v.currentTime,duration:Number.isFinite(v.duration)?v.duration:null,volume:Math.round(v.volume*100),muted:v.muted,ready:v.readyState})')
    result['playing_ad']=page.locator('#movie_player.ad-showing').count()>0
    return result


def player_video(page):
    main=page.locator('#movie_player video.html5-main-video, #movie_player video').first
    return main if main.count() else page.locator('video').first


def sound(page,action,level=None):
    previous=state(page)
    target=max(0,min(100,int(level))) if action=='set_volume' and level is not None else max(0,min(100,previous['volume']+(10 if action=='volume_up' else -10)))
    muted=action=='mute'
    if action in ('mute','unmute'):
        target=previous['volume']
        # A zero-volume player is still silent after unmute.
        if action=='unmute' and target==0:target=50
    player_video(page).evaluate('''(v,p)=>{
        const player=document.querySelector('#movie_player');
        if(player && typeof player.setVolume==='function') {
            player.setVolume(p.level);
            if(p.muted && typeof player.mute==='function') player.mute();
            if(!p.muted && typeof player.unMute==='function') player.unMute();
        }
        v.volume=p.level/100;v.muted=p.muted;
    }''',{'level':target,'muted':muted})
    # Verify after YouTube has had a chance to update its player state.
    page.wait_for_timeout(350)
    info=state(page)
    if abs(info['volume']-target)>1 or info['muted']!=muted:
        raise RuntimeError('YouTube did not keep the requested volume. Check the player and try again.')
    return info


def open_video(page,target,cancelled=lambda:False):
    page.goto(target,wait_until='commit',timeout=45000)
    expected=video_id(target)
    deadline=time.monotonic()+25
    while time.monotonic()<deadline:
        if cancelled():raise RuntimeError('Stopped by you.')
        ready=page.evaluate('''expected=>{
            const p=document.querySelector('#movie_player');
            const v=document.querySelector('#movie_player video')||document.querySelector('video');
            if(!v)return false;
            if(p && typeof p.getVideoData==='function')return p.getVideoData()?.video_id===expected;
            return new URL(location.href).searchParams.get('v')===expected;
        }''',expected)
        if ready:return play(page)
        page.wait_for_timeout(250)
    raise RuntimeError('The next video did not finish loading. Check YouTube for a prompt or playback error.')


def video_id(url):
    return parse_qs(urlparse(url).query).get('v',[''])[0]


def load_history(browser):
    if hasattr(browser,'media_history'):
        return
    browser.media_history=[];browser.media_index=-1;browser.media_queue=[]
    path=getattr(browser,'media_state_file',Path(os.environ['LOCALAPPDATA'])/'OpenJarvis/media-state.json')
    try:
        saved=json.loads(Path(path).read_text())
        browser.media_history=[u for u in saved.get('history',[]) if urlparse(u).hostname=='www.youtube.com' and video_id(u)]
        browser.media_index=min(int(saved.get('index',-1)),len(browser.media_history)-1)
        browser.media_queue=[u for u in saved.get('queue',[]) if urlparse(u).hostname=='www.youtube.com' and video_id(u)]
    except (OSError,ValueError,TypeError):
        pass


def save_history(browser):
    path=Path(getattr(browser,'media_state_file',Path(os.environ['LOCALAPPDATA'])/'OpenJarvis/media-state.json'))
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps({'history':browser.media_history,'index':browser.media_index,'queue':getattr(browser,'media_queue',[])}),encoding='utf-8')


def record(browser,url):
    load_history(browser)
    if '/watch?' not in url:
        return
    history=getattr(browser,'media_history',[])
    index=getattr(browser,'media_index',-1)
    if index>=0 and index<len(history) and video_id(history[index])==video_id(url):
        save_history(browser)
        return
    browser.media_history=history[:index+1]+[url]
    browser.media_index=len(browser.media_history)-1
    save_history(browser)


def play(page):
    video=player_video(page)
    video.wait_for(state='attached',timeout=25000)
    if video.evaluate('(v)=>v.paused'):
        button=visible_first(page.locator('.ytp-play-button'))
        if button:
            button.click()
        else:
            video.evaluate('(v)=>v.play()')
    deadline=time.monotonic()+12
    while time.monotonic()<deadline:
        info=state(page)
        if not info['paused'] and info['ready']>=2:
            return info
        page.wait_for_timeout(250)
    raise RuntimeError('The video has not started. Check the browser for an ad, sign-in prompt, or playback error.')


def control(browser,action,query='',seconds=10,level=None,cancelled=lambda:False):
    if cancelled():
        raise RuntimeError('Stopped by you.')
    load_history(browser)
    if action=='search_play':
        result=youtube_search(browser,query,cancelled)
        if result['status']!='results_ready':
            return result
        browser.media_queue=[]
        for video in result.get('videos',[]):
            if video_id(video['url']) and video_id(video['url']) not in [video_id(u) for u in browser.media_queue]:
                browser.media_queue.append(video['url'])
        save_history(browser)
        action='play_first'
    page=site_page(browser,'www.youtube.com','https://www.youtube.com/')
    if action=='play_first':
        links=page.locator('ytd-video-renderer a#video-title[href*="/watch"],yt-lockup-view-model a[href^="/watch"]')
        links.first.wait_for(state='attached',timeout=15000)
        href=links.first.get_attribute('href')
        target=urljoin('https://www.youtube.com',href or '')
        if urlparse(target).hostname!='www.youtube.com' or '/watch?' not in target:
            raise RuntimeError('A normal video result was not found.')
        record(browser,page.url)
        info=open_video(page,target,cancelled)
        record(browser,page.url)
        return {'status':'playing','message':'YouTube playback started. An ad is playing first.' if info['playing_ad'] else 'The first YouTube video is playing.','player':info}
    player_video(page).wait_for(state='attached',timeout=15000)
    if action=='play':
        info=play(page)
    elif action=='pause':
        player_video(page).evaluate('(v)=>v.pause()')
        info=state(page)
    elif action in ('forward','rewind'):
        if state(page)['playing_ad']:
            return {'status':'needs_attention','message':'An ad is playing. Try seeking after the video starts.'}
        amount=max(1,min(600,float(seconds)))*(1 if action=='forward' else -1)
        player_video(page).evaluate('(v,amount)=>{v.currentTime=Math.max(0,Math.min(Number.isFinite(v.duration)?v.duration:v.currentTime+Math.abs(amount),v.currentTime+amount))}',amount)
        info=state(page)
    elif action in ('set_volume','volume_up','volume_down','mute','unmute'):
        info=sound(page,action,level)
    elif action in ('next','previous'):
        record(browser,page.url)
        history=getattr(browser,'media_history',[])
        index=getattr(browser,'media_index',-1)
        target_index=index+(1 if action=='next' else -1)
        if 0<=target_index<len(history):
            info=open_video(page,history[target_index],cancelled)
            browser.media_index=target_index
        else:
            buttons=page.locator('.ytp-next-button' if action=='next' else '.ytp-prev-button')
            # Player controls can be hidden until the mouse moves. Their href is still usable.
            button=buttons.first if buttons.count() else None
            queue=getattr(browser,'media_queue',[])
            queue_index=next((i for i,u in enumerate(queue) if video_id(u)==video_id(page.url)),-1)
            if action=='next' and queue_index>=0 and queue_index+1<len(queue):
                info=open_video(page,queue[queue_index+1],cancelled)
            elif button is not None and button.get_attribute('aria-disabled')!='true' and button.get_attribute('disabled') is None:
                target=urljoin('https://www.youtube.com',button.get_attribute('href') or '')
                if urlparse(target).hostname=='www.youtube.com' and video_id(target) and video_id(target)!=video_id(page.url):
                    info=open_video(page,target,cancelled)
                else:
                    if not button.is_visible():
                        page.locator('#movie_player').hover()
                    button.wait_for(state='visible',timeout=5000)
                    before=video_id(page.url)
                    button.click()
                    page.wait_for_function('(old)=>new URL(location.href).searchParams.get("v")!==old',arg=before,timeout=15000)
                    info=open_video(page,page.url,cancelled)
            elif action=='next':
                recommendations=page.locator('ytd-watch-next-secondary-results-renderer a[href*="/watch"],yt-lockup-view-model a[href*="/watch"]')
                candidates=recommendations.evaluate_all('es=>es.map(e=>e.href)')
                target=next((u for u in candidates if urlparse(u).hostname=='www.youtube.com' and video_id(u) and video_id(u)!=video_id(page.url)),None)
                if target is None:raise RuntimeError('No next video has loaded. Search and play a result first.')
                info=open_video(page,target,cancelled)
            else:
                raise RuntimeError('There is no previous video in Jarvis history yet.')
        record(browser,page.url)
    else:
        raise ValueError('Unknown video control.')
    message={'pause':'Video paused.','play':'Video is playing.','next':'Playing the next video.','previous':'Playing the previous video.','forward':'Moved the video forward.','rewind':'Moved the video back.','mute':'YouTube is muted.','unmute':f'YouTube is unmuted. Volume is {info["volume"]} percent.'}.get(action,f'YouTube volume is {info["volume"]} percent.')
    return {'status':'ok','message':message,'player':info,'url':page.url}
