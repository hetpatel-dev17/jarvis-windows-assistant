"""Focused website workflows. Message submission always passes approval."""
import re
import time
from urllib.parse import urlparse, urlencode


def site_page(browser,host,url):
    browser.ensure()
    if not hasattr(browser,'site_tabs'):
        browser.site_tabs={}
    current=getattr(browser,'page',None)
    remembered=browser.site_tabs.get(host)
    if current and not current.is_closed() and urlparse(current.url).hostname==host:
        page=current
    elif remembered and not remembered.is_closed() and urlparse(remembered.url).hostname==host:
        page=remembered
    else:
        page=next((p for p in browser.context.pages if not p.is_closed() and urlparse(p.url).hostname==host),None)
    if page is None:
        page=browser.context.new_page()
        page.goto(url,wait_until='commit',timeout=45000)
    browser.page=page
    browser.site_tabs[host]=page
    page.bring_to_front()
    return page


def youtube_search(browser,query,cancelled=lambda:False):
    query=query.strip()
    if not query or len(query)>500:
        raise ValueError('Please give a short YouTube search phrase.')
    if cancelled():
        raise RuntimeError('Stopped by you.')
    target='https://www.youtube.com/results?'+urlencode({'search_query':query})
    page=site_page(browser,'www.youtube.com',target)
    if page.url!=target:
        page.goto(target,wait_until='commit',timeout=45000)
    selector='ytd-video-renderer,ytd-channel-renderer,ytd-playlist-renderer,yt-lockup-view-model,ytd-reel-item-renderer'
    try:
        page.locator(selector).first.wait_for(state='visible',timeout=25000)
    except Exception:
        return {'status':'needs_attention','query':query,'url':page.url,
                'message':'YouTube results did not load. Check the browser for a consent or verification screen. No search success was assumed.'}
    videos=page.locator('ytd-video-renderer a#video-title,ytd-playlist-renderer a#video-title,yt-lockup-view-model a.yt-lockup-metadata-view-model__title').evaluate_all(
        'es=>es.slice(0,8).map(e=>({title:(e.innerText||e.getAttribute("title")||"").trim(),url:e.href})).filter(e=>e.title)')
    return {'status':'results_ready','query':query,'url':page.url,'videos':videos,
            'message':f'YouTube search results are open for {query}.'}


def youtube_query(text):
    """Recognize only a simple search request; leave multi-step tasks to the agent."""
    if re.search(r'\b(send|message|then|play|download)\b',text,re.I):
        return None
    patterns=[r'\b(?:search(?:\s+for)?|find|look\s+up)\s+(.+?)\s+(?:on|in)\s+you\s*tube[\s.!?]*(?:please)?[\s.!?]*$',
              r'\byou\s*tube[:,]?\s+(?:search(?:\s+for)?|find)\s+(.+?)[\s.!?]*$']
    for pattern in patterns:
        match=re.search(pattern,text,re.I)
        if match:
            return match.group(1).strip(' \"\'.,!?')
    return None


def whatsapp_request(text):
    if not re.search(r'whats\s*app',text,re.I):
        return None
    patterns=[r'\bsend\s+(?:a\s+)?whats\s*app\s+message\s+to\s+(.+?)\s+(?:saying|that\s+says|with\s+(?:the\s+)?text|:)\s*(.+)$',
              r'\bsend\s+(?:a\s+)?message\s+to\s+(.+?)\s+on\s+whats\s*app\s+(?:saying|:)\s*(.+)$',
              r'\bmessage\s+(.+?)\s+on\s+whats\s*app\s+(?:saying|:)\s*(.+)$']
    for pattern in patterns:
        match=re.search(pattern,text,re.I)
        if match:
            return {'recipient':match.group(1).strip(),'message':match.group(2).strip(),'send':True}
    return None


def visible_first(locator):
    for i in range(locator.count()):
        if locator.nth(i).is_visible():
            return locator.nth(i)
    return None


def normalized(text):
    return text.replace('\r\n','\n').replace('\u00a0',' ').strip()


def composer_text(composer):
    if composer.evaluate('(e)=>e.tagName==="INPUT"||e.tagName==="TEXTAREA"'):
        return normalized(composer.input_value())
    return normalized(composer.inner_text())


COMPOSER='footer [contenteditable="true"][role="textbox"],#main [contenteditable="true"][data-tab="10"],[contenteditable="true"][aria-label="Type a message"],textarea[aria-label="Type a message"],input[aria-label="Type a message"]'
HEADERS='#main header,main header,header[data-testid="conversation-header"]'
SEND='footer button[aria-label="Send"],#main button[aria-label="Send"],button:has([data-icon="send"]),button:has([data-icon="wds-ic-send-filled"]),[role="button"]:has([data-icon="send"])'


def header_identity(page):
    header=visible_first(page.locator(HEADERS))
    if header is None:
        raise RuntimeError('The chat header was not found. No message was sent.')
    titles=header.locator('span[title]').evaluate_all('es=>es.map(e=>e.getAttribute("title")).filter(Boolean)')
    identity=normalized(titles[0] if titles else header.inner_text())
    if not identity:
        raise RuntimeError('The recipient could not be checked. No message was sent.')
    return identity


OUTGOING_SELECTOR='#main .message-out,main .message-out,#main [data-id^="true_"],#main [data-testid="msg-container"]:has([data-icon="tail-out"])'
OUTGOING_MATCH_SCRIPT=r'''(containers,message)=>{
    const clean=s=>(s||'').replace(/[\u200e\u200f\u202a-\u202e\u2066-\u2069]/g,'').replace(/\s+/g,' ').trim();
    const expected=clean(message);
    return containers.filter(container=>{
      const candidates=[...container.querySelectorAll('[data-testid="selectable-text"],.selectable-text,span')];
      return candidates.some(e=>clean(e.innerText||e.textContent)===expected);
    }).length;
}'''


def outgoing_count(page,message):
    # Both the legacy UI and the current msg-container/tail-out UI are supported.
    return page.locator(OUTGOING_SELECTOR).evaluate_all(OUTGOING_MATCH_SCRIPT,message)


def whatsapp_message(browser,recipient,message,send,approve,cancelled=lambda:False):
    recipient=recipient.strip()
    message=message.strip()
    if not recipient or len(recipient)>150 or not message or len(message)>5000:
        raise ValueError('Give one recipient and a message of up to 5,000 characters.')
    if cancelled():
        raise RuntimeError('Stopped by you.')
    page=site_page(browser,'web.whatsapp.com','https://web.whatsapp.com/')
    number=None
    if re.fullmatch(r'\+?[\d\s().-]+',recipient):
        number=re.sub(r'\D','',recipient)
        if not 8<=len(number)<=15:
            raise ValueError('Use the full phone number including country code.')
        page.goto('https://web.whatsapp.com/send?'+urlencode({'phone':number}),wait_until='domcontentloaded',timeout=45000)
    else:
        searches=page.locator('input[aria-label="Search or start a new chat"],input[placeholder="Search or start a new chat"],input[aria-label="Search input textbox"],input[data-tab="3"],[contenteditable="true"][aria-label="Search input textbox"],[contenteditable="true"][data-tab="3"]')
        searches.first.wait_for(state='visible',timeout=25000)
        search=visible_first(searches)
        search.fill(recipient)
        pane=page.locator('#pane-side')
        exact_name=re.compile(r'^\s*'+re.escape(recipient)+r'\s*$',re.I)
        candidate=pane.get_by_title(exact_name).filter(visible=True)
        deadline=time.monotonic()+12
        while time.monotonic()<deadline:
            if cancelled():
                raise RuntimeError('Stopped by you.')
            if candidate.count():
                break
            alternative=pane.get_by_text(exact_name).filter(visible=True)
            if alternative.count():
                candidate=alternative
                break
            page.wait_for_timeout(250)
        if candidate.count()!=1:
            raise RuntimeError(f'I could not find one exact contact named {recipient}. Please give the full phone number. No message was sent.')
        candidate.click()
    page.locator(COMPOSER).first.wait_for(state='visible',timeout=25000)
    identity=header_identity(page)
    if number is None:
        deadline=time.monotonic()+12
        while normalized(recipient).casefold() not in normalized(identity).casefold() and time.monotonic()<deadline:
            if cancelled():
                raise RuntimeError('Stopped by you.')
            page.wait_for_timeout(200)
            identity=header_identity(page)
        if normalized(recipient).casefold() not in normalized(identity).casefold():
            raise RuntimeError('The opened chat does not match the requested contact. No message was sent.')
    # A visible composer can still belong to the previous SPA conversation.
    # Resolve it again only after the expected recipient has appeared.
    page.wait_for_timeout(250)
    composer=visible_first(page.locator(COMPOSER))
    if cancelled():
        raise RuntimeError('Stopped by you.')
    composer.fill(message)
    if composer_text(composer)!=normalized(message):
        raise RuntimeError('The draft text did not match your message. Nothing was sent.')
    draft={'recipient':recipient,'chat_header':identity,'message':message}
    if not send:
        return {'status':'draft_ready',**draft,'message_status':'Prepared only. Not sent.'}
    approve(f'Send this WhatsApp message?\n\nRequested recipient: {recipient}\nOpened chat: {identity}\n\nExact message:\n{message}')
    if cancelled():
        raise RuntimeError('Stopped before sending. Nothing was sent.')
    # Check the recipient and draft again after the human has approved.
    if header_identity(page)!=identity or composer_text(composer)!=normalized(message):
        raise RuntimeError('The recipient or draft changed after approval. Nothing was sent.')
    button=visible_first(page.locator(SEND))
    if button is None:
        raise RuntimeError('The Send button was not found. Your draft is ready, but nothing was sent.')
    before=outgoing_count(page,message)
    button.click()
    # Never retry a send just because confirmation is slow.
    deadline=time.monotonic()+20
    while time.monotonic()<deadline:
        if outgoing_count(page,message)>before and not composer_text(composer):
            return {'status':'submitted',**draft,'message_status':'The outgoing message appeared in WhatsApp. Delivery and read status have not been checked.'}
        page.wait_for_timeout(300)
    return {'status':'send_unconfirmed',**draft,'message_status':'Send was clicked once, but the outgoing bubble was not confirmed. Do not resend. Ask the user to check WhatsApp.'}
