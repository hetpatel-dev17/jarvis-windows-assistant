"""Conversational navigation commands. Page contents cannot authorize actions."""
import re
from urllib.parse import urlparse,urljoin,quote_plus

SITES={
 'netflix':('Netflix','https://www.netflix.com/'),
 'amazon':('Amazon','https://www.amazon.in/'),
 'flipkart':('Flipkart','https://www.flipkart.com/'),
 'claude':('Claude','https://claude.ai/'),'claudia':('Claude','https://claude.ai/'),
 'google ai studio':('Google AI Studio','https://aistudio.google.com/'),
 'google studio':('Google AI Studio','https://aistudio.google.com/'),
 'google studios':('Google AI Studio','https://aistudio.google.com/'),
 'ai studio':('Google AI Studio','https://aistudio.google.com/'),
 'google photos':('Google Photos','https://photos.google.com/'),
 'google drive':('Google Drive','https://drive.google.com/'),
 'google':('Google','https://www.google.com/'),
 'youtube':('YouTube','https://www.youtube.com/'),
 'chatgpt':('ChatGPT','https://chatgpt.com/'),
 'whatsapp':('WhatsApp','https://web.whatsapp.com/'),
 'gmail':('Gmail','https://mail.google.com/'),
 'google calendar':('Google Calendar','https://calendar.google.com/'),
 'github':('GitHub','https://github.com/'),
 'perplexity':('Perplexity','https://www.perplexity.ai/')}


def parse(text,area='browser'):
    t=re.sub(r'^(?:(?:hey |hello )?jarvis[, ]+|please |can you |could you |would you |i want you to |i need you to )+','',text.strip(),flags=re.I)
    t=re.sub(r'[, ]*please[.!?]*$','',t,flags=re.I).strip().rstrip('.!?')
    lower=t.casefold()
    ordinal=re.fullmatch(r'(play|open)(?: the)? (first|second|third|fourth|fifth|\d+)(?: (?:video|result|one))',lower)
    if ordinal:
        index={'first':1,'second':2,'third':3,'fourth':4,'fifth':5}.get(ordinal.group(2))
        if index is None:index=int(ordinal.group(2))
        if index!=1:return 'browser_control',{'action':'result','index':index,'play':ordinal.group(1)=='play'}
    first=re.fullmatch(r'(?:start (?:playing )?|play |open |put on )(?:the )?(?:first|number one|number 1|1st)(?: (?:one|video|videos|result|song|track))?(?: on youtube)?(?: s)?',lower)
    if first:
        if area=='files' and lower.startswith('open') and not re.search(r'video|song|track|youtube',lower):
            return 'windows_operator',{'action':'open_match','target':'1'}
        return 'browser_control',{'action':'first','play':not lower.startswith('open')}
    if lower in ('play it','play this','play that','start it','start playing','play the video','start the video','resume it'):
        return 'browser_control',{'action':'play'}
    if lower in ('open it','open that','open this','open that one') and area=='browser':
        return 'browser_control',{'action':'reference'}
    found=re.fullmatch(r'(?:scroll|go|move)(?: a (?:little|bit))? (up|down)(?: a (?:little|bit))?(?: more)?|(?:scroll |a little |a bit )more(?: down)?',lower)
    if found:return 'browser_control',{'action':'scroll','direction':found.group(1) or 'down'}
    if lower in ('go back','back to the previous page','previous page') and area=='browser':return 'browser_control',{'action':'back'}
    found=re.fullmatch(r'(?:open|go to|visit|launch|take me to|bring up)(?: the)? (.+?)(?: website| site)?',t,re.I)
    if found:
        name=found.group(1).strip();key=re.sub(r'\byou tube\b','youtube',name.casefold())
        if key in SITES:return 'browser_control',{'action':'open','target':key}
        if re.fullmatch(r'(?:https?://)?(?:[a-z0-9-]+\.)+[a-z]{2,}(?:/[^\s]*)?',name,re.I):return 'browser_control',{'action':'open','target':name}
    found=re.fullmatch(r'(?:search(?: for)?|find|look for|look up|show me|play) (.+?) (?:on|in|from) (you\s*tube|google|bing)((?:[ ,]+(?:and|then|now)\b.*)?)',t,re.I)
    if not found:
        alt=re.fullmatch(r'(?:search|find|look up) (?:on |in )?(you\s*tube|google|bing)(?: for)? (.+)',t,re.I)
        if alt:
            site=re.sub(r'\s+','',alt.group(1).casefold());query=alt.group(2)
            return 'browser_control',{'action':'search','target':site,'query':query}
    else:
        query=found.group(1).strip();site=re.sub(r'\s+','',found.group(2).casefold())
        play=lower.startswith('play ') or bool(re.search(r'\bplay\b',found.group(3),re.I))
        return 'browser_control',{'action':'search','target':site,'query':query,'play':play}
    found=re.fullmatch(r'(?:search(?: for)?|look for|look up) (.+?)(?: (?:on|in) (?:this site|this website|this page|it|there|that site|the website)| here)',t,re.I)
    if found:
        if area=='files':return 'windows_operator',{'action':'search','query':found.group(1),'scope':'here'}
        return 'browser_control',{'action':'search','query':found.group(1)}
    found=re.fullmatch(r'(?:search(?: for)?|find|look for|look up) (.+?) (?:on|in) (.+)',t,re.I)
    if found and found.group(2).casefold() in SITES:
        return 'browser_control',{'action':'search','target':found.group(2).casefold(),'query':found.group(1)}
    return None


def current_page(browser):
    page=browser.ensure()
    # Respect a manually selected tab when exactly one controlled tab is visible.
    visible=[]
    for candidate in browser.context.pages:
        try:
            if not candidate.is_closed() and candidate.evaluate('document.visibilityState')=='visible':visible.append(candidate)
        except Exception:continue
    if len(visible)==1:page=visible[0]
    browser.page=page
    return page


def control(browser,action,target='',query='',direction='down',play=False,index=1,check_url=lambda u:u,cancelled=lambda:False):
    import media_controls as media
    from site_workflows import site_page,youtube_search
    if cancelled():raise RuntimeError('Stopped by you.')
    if action=='search' and (not query.strip() or len(query)>500):raise ValueError('Give a short search phrase.')
    if action=='open':
        name,url=SITES.get(target.casefold(),('the website',target if target.startswith(('http://','https://')) else 'https://'+target))
        url=check_url(url);page=site_page(browser,urlparse(url).hostname,url)
        browser.followup='site'
        return {'status':'opened','url':page.url,'message':f'Opened {name}.'}
    if action=='search' and target=='youtube':
        if play:return media.control(browser,'search_play',query=query,cancelled=cancelled)
        info=youtube_search(browser,query,cancelled)
        if info['status']=='results_ready':
            browser.followup='results'
            media.load_history(browser)
            browser.media_queue=list(dict.fromkeys(v['url'] for v in info.get('videos',[]) if media.video_id(v['url'])))
            media.save_history(browser)
            return {'status':'results_ready','url':info['url'],'message':f'YouTube results are ready for {query}.'}
        return info
    if action=='search' and target in ('google','bing'):
        host='www.google.com' if target=='google' else 'www.bing.com'
        url='https://'+host+'/search?q='+quote_plus(query)
        page=site_page(browser,host,url);page.goto(check_url(url),wait_until='domcontentloaded',timeout=45000)
        results=page.locator('#search a:has(h3),#rso a:has(h3),#b_results .b_algo h2 a')
        try:results.first.wait_for(state='attached',timeout=10000)
        except Exception:
            browser.followup=''
            return {'status':'needs_attention','message':'Search results did not load. Check the browser for sign-in or verification.'}
        browser.followup='results'
        return {'status':'results_ready','url':page.url,'message':f'Search results are open for {query}. You can say open the first one.'}
    if action=='search' and target in SITES:
        _,url=SITES[target];page=site_page(browser,urlparse(url).hostname,url)
    else:page=current_page(browser)
    host=urlparse(page.url).hostname
    if action=='result':
        if not 1<=index<=20:raise ValueError('Choose a result from 1 to 20.')
        if host=='www.youtube.com' and '/results' in page.url:
            links=page.locator('ytd-video-renderer a#video-title[href*="/watch"],yt-lockup-view-model a[href^="/watch"]')
            hrefs=links.evaluate_all('es=>[...new Set(es.filter(e=>e.getClientRects().length).map(e=>e.href))]')
            if len(hrefs)<index:return {'status':'needs_attention','message':'That numbered video is not visible in these results.'}
            url=check_url(hrefs[index-1]);media.record(browser,page.url)
            info=media.open_video(page,url,cancelled);media.record(browser,page.url)
            return {'status':'playing','player':info,'message':f'Playing video {index}.'}
        return {'status':'needs_attention','message':'Numbered video selection currently needs YouTube search results.'}
    if action in ('first','reference','play','search') and (host=='accounts.google.com' or re.search(r'/(?:login|signin)(?:[/?]|$)',page.url)):
        return {'status':'needs_attention','message':'This site needs sign-in. Complete it in the normal sign-in browser, then try again.'}
    if action=='reference':
        if getattr(browser,'followup','')!='results':return {'status':'needs_attention','message':'Give me a few words from the item you want to open.'}
        action='first'
    if action=='scroll':
        page.mouse.wheel(0,-650 if direction=='up' else 650);page.wait_for_timeout(300)
        return {'status':'scrolled','message':f'Scrolled {direction}.'}
    if action=='back':
        page.go_back(wait_until='domcontentloaded',timeout=30000)
        return {'status':'opened','message':'Returned to the previous page.'}
    if action in ('first','play') and host=='www.youtube.com':
        return media.control(browser,'play' if '/watch?' in page.url else 'play_first',cancelled=cancelled)
    if action=='play':
        video=page.locator('video').first
        if video.count():
            video.evaluate('(v)=>v.play()');page.wait_for_timeout(300)
            if not video.evaluate('(v)=>v.paused'):return {'status':'playing','message':'Playback started.'}
        return {'status':'needs_attention','message':'There is no ready video on this page. Tell me what to search for.'}
    if action=='first':
        selectors='#search a:has(h3),#rso a:has(h3),#b_results .b_algo h2 a,[data-testid="result-title-a"]'
        links=page.locator(selectors)
        if not links.count() and host in ('www.google.com','www.bing.com'):
            return {'status':'needs_attention','message':'Search results are not ready. Check the browser for verification.'}
        if not links.count():links=page.locator('main a[href],[role="main"] a[href]')
        hrefs=links.evaluate_all('es=>es.filter(e=>e.getClientRects().length).map(e=>e.href).filter(u=>/^https?:/.test(u))')
        if not hrefs:return {'status':'needs_attention','message':'I cannot identify a result link here. Give me a few words from its title.'}
        target=check_url(urljoin(page.url,hrefs[0]));page.goto(target,wait_until='domcontentloaded',timeout=45000)
        return {'status':'opened','url':page.url,'message':'Opened the first result.'}
    if action=='search':
        fields=page.get_by_role('searchbox').or_(page.get_by_role('combobox',name=re.compile('search',re.I))).or_(page.locator('input[placeholder*="Search" i],input[aria-label*="Search" i]')).filter(visible=True)
        if not fields.count():
            buttons=page.get_by_role('button',name=re.compile(r'^search(?: chats| photos| files| apps)?$',re.I)).filter(visible=True)
            if buttons.count()==1:buttons.first.click();page.wait_for_timeout(300)
        if not fields.count():return {'status':'needs_attention','message':'This page has no ready search box. Check for sign-in or a search menu.'}
        field=fields.first
        if field.get_attribute('type')=='password':raise ValueError('Please handle sign-in yourself.')
        field.fill(query);field.press('Enter');page.wait_for_timeout(700)
        browser.followup='results'
        return {'status':'searched','message':f'Searched this site for {query}.'}
    raise ValueError('Unknown browser control.')
