import re


def playback_command(text):
    t=re.sub(r'\byou\s*tube\b','youtube',text)
    t=re.sub(r'\s+(?:on|in) youtube$','',t)
    t=re.sub(r'^youtube[,: ]+','',t)
    t=re.sub(r'\s+youtube$','',t).strip()
    if re.fullmatch(r'(?:play |go to |go forward to |skip to )?(?:the )?next(?: (?:video|song|track))?|skip(?: (?:this|the)(?: video|song|track)?| video| song| track)?|forward video',t):
        return 'youtube_control',{'action':'next'}
    if re.fullmatch(r'(?:(?:play|go back to|go to|back to) (?:the )?)?(?:previous|last)(?: (?:video|song|track))?|back video',t):
        return 'youtube_control',{'action':'previous'}
    system=bool(re.search(r'\b(?:computer|system|windows|laptop)\b',t))
    destination='desktop_control' if system else 'youtube_control'
    v=re.sub(r'\b(?:youtube|computer|system|windows|laptop|video|the)\b','',t)
    v=re.sub(r'\s+',' ',v).strip()
    if re.fullmatch(r'(?:unmute|un mute)(?: (?:the )?(?:sound|volume|music))?|turn (?:the )?sound on',v):
        return destination,{'action':'unmute'}
    if re.fullmatch(r'mute(?: (?:the )?(?:sound|volume|music))?|turn (?:the )?sound off',v):
        return destination,{'action':'mute'}
    if re.fullmatch(r'(?:(?:set|turn|change) (?:the )?)?(?:volume (?:to )?(?:max(?:imum)?|full|highest)|(?:max(?:imum)?|full|highest) volume)(?: volume)?',v):
        return destination,{'action':'set_volume','level':100}
    if re.fullmatch(r'(?:(?:set|turn|change) (?:the )?)?(?:volume (?:to )?(?:min(?:imum)?|lowest)|(?:min(?:imum)?|lowest) volume)',v):
        return destination,{'action':'set_volume','level':0}
    found=re.fullmatch(r'(?:(?:set|change|turn) (?:the )?)?volume\s+(?:to\s+)?(\d+)\s*(?:%|percent)?',v)
    if found:return destination,{'action':'set_volume','level':int(found.group(1))}
    if re.fullmatch(r'volume (?:up|plus|higher|increase|\+)|(?:increase|raise) (?:the )?volume|turn (?:the )?volume up|(?:higher|louder)(?: volume)?',v):
        return destination,{'action':'volume_up'}
    if re.fullmatch(r'volume (?:down|minus|lower|decrease|-)|(?:decrease|lower|reduce) (?:the )?volume|turn (?:the )?volume down|(?:lower|quieter)(?: volume)?',v):
        return destination,{'action':'volume_down'}
    return None


def parse(text):
    raw=text.strip()
    t=re.sub(r'^(?:please\s+|can you\s+|could you\s+|jarvis[, ]+)+','',raw,flags=re.I).strip()
    lower=re.sub(r'[, ]*please$','',t.lower().rstrip('.!?')).strip()
    # Explicit attachment commands keep using the separate upload picker below.
    if not re.search(r'chat\s*gpt|\b(?:attach|upload|select|choose)\b',lower):
        found=re.fullmatch(r'(?:open|launch|double[ -]?click|play)\s+(?:(?:that|this|the|my)\s+)?(.+?\.(?:pdf|docx?|dxf|dwg|xlsx?|pptx?|stl|step|stp|png|jpe?g|mp[34]|wav)|pdf(?: file)?|word(?: document| file)?|document|drawing|dxf(?: file)?|dwg(?: file)?|spreadsheet)',t.rstrip('.!?'),re.I)
        if found:return 'windows_operator',{'action':'open','target':found.group(1)}
        if re.fullmatch(r'(?:show|list)(?: me)? (?:the )?(?:files|folder contents|files here)',lower):return 'windows_operator',{'action':'list'}
        found=re.fullmatch(r'(?:open|play|show)\s+(?:match|result|number|option)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten)',lower)
        if found:
            number={'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10}.get(found.group(1),found.group(1))
            return 'windows_operator',{'action':'open_match','target':str(number)}
        found=re.fullmatch(r'(?:find|look for|search for|search)\s+(.+?)(?:\s+(?:on|in|under)\s+(?:my |the )?(desktop|downloads|documents|pictures|music|videos|home|computer|all drives|this folder|here|[a-z]:|[a-z] drive|drive [a-z]))?',t.rstrip('.!?'),re.I)
        if found and not re.search(r'\b(?:youtube|you tube|google|web|browser|whatsapp|internet)\b',lower):
            query=re.sub(r'^(?:(?:a |the )?(?:file|folder|document)\s+(?:(?:called|named|containing)\s+)?|something\s+(?:(?:like|called|named)\s+)?)','',found.group(1),flags=re.I).strip(' "\'')
            scope=(found.group(2) or 'computer').casefold()
            if 'drive' in scope and scope!='all drives':scope=re.search(r'\b[a-z]\b',scope).group()+':'
            return 'windows_operator',{'action':'search','query':query,'scope':scope}
        found=re.fullmatch(r'(?:open|go to|show)\s+(?:my |the )?(desktop|downloads|documents|pictures|music|videos)(?: folder)?',lower)
        if found:return 'windows_operator',{'action':'open','target':found.group(1)}
        found=re.fullmatch(r'(?:open|go to)\s+(?:the )?(?:drive ([a-z])|([a-z]) drive|([a-z]):)',lower)
        if found:return 'windows_operator',{'action':'open','target':next(g for g in found.groups() if g)+':'}
        if re.fullmatch(r'(?:go )?(?:back|up)(?: one)? folder',lower):
            return 'windows_operator',{'action':'open','target':'..'}
        found=re.fullmatch(r'(?:open|play)\s+(?:the )?(?:file|folder|document|local video|local song)\s+(.+)',t,re.I)
        if found:return 'windows_operator',{'action':'open','target':found.group(1).strip(' "\'')}
    # Specific destinations come before generic volume/file commands.
    if 'chatgpt' in lower or 'chat gpt' in lower:
        if re.search(r'\b(?:attach|upload)\b.*\bsend\b',lower) or re.search(r'\bsend (?:the )?(?:selected file|selected pdf|this file)\b',lower):
            params={'action':'attach_send'}
            chosen=re.search(r'\b(?:attach|upload)\s+(?:and\s+send\s+)?(?:the\s+)?(.+?)\s+(?:to|on|in)\s+chat\s*gpt\b',t,re.I)
            if chosen:
                target=re.sub(r'^file\s+','',chosen.group(1).strip(' "\''),flags=re.I)
                if target.casefold() not in ('selected file','selected pdf','this file','it','file'):
                    params['path']=target
            prompt=re.search(r'\bchat\s*gpt\s+(?:saying|with\s+(?:the\s+)?message|with\s+text)\s*:\s*(.+)$',t,re.I)
            if prompt:params['text']=prompt.group(1)
            return 'chatgpt',params
        found=re.search(r'\b(?:ask|tell|send\s+to)\s+chat\s*gpt\s*[:,]?\s+(.+)$',t,re.I)
        if found:return 'chatgpt',{'action':'ask','text':found.group(1)}
        found=re.search(r'\b(?:open|go to)\s+(?:the\s+)?(?:old\s+)?chat\s+(?:named|called)\s+(.+?)\s+(?:in|on)\s+chat\s*gpt[.!?]*$',t,re.I)
        if found:return 'chatgpt',{'action':'open_chat','name':found.group(1).strip(' "\'')}
        found=re.search(r'\bsearch\s+chat\s*gpt\s+chats\s+for\s+(.+)$',t,re.I)
        if found:return 'chatgpt',{'action':'search_chat','name':found.group(1).strip(' "\'')}
        if re.search(r'\bnew chat\b',lower):return 'chatgpt',{'action':'new_chat'}
        if re.search(r'\battach\b',lower):
            found=re.search(r'\battach\s+(?:the\s+)?(.+?)\s+(?:to|in|on)\s+chat\s*gpt[.!?]*$',t,re.I)
            params={'action':'attach'}
            if found:
                chosen=re.sub(r'^file\s+','',found.group(1).strip(' "\''),flags=re.I)
                if chosen.casefold() not in ('selected file','this file','it','selected pdf'):
                    params['path']=chosen
            return 'chatgpt',params
        if re.search(r'\b(?:read|speak)\b',lower):return 'chatgpt',{'action':'read_reply'}
        if re.search(r'^(?:send (?:it|this|the message)|submit)',lower):return 'chatgpt',{'action':'send'}
        if re.fullmatch(r'(?:open|go to) chat\s*gpt',lower):return 'chatgpt',{'action':'open'}
    found=re.search(r'\b(?:search(?:\s+for)?|find)\s+(.+?)\s+(?:on|in)\s+you\s*tube\b',t,re.I)
    if found and re.search(r'\bplay\b',t,re.I):return 'youtube_control',{'action':'search_play','query':found.group(1).strip(' "\'')}
    if re.fullmatch(r'(?:play|open)\s+(?:the\s+)?first\s+(?:video|result)(?:\s+on\s+youtube)?',lower):return 'youtube_control',{'action':'play_first'}
    playback=playback_command(lower)
    if playback:return playback
    if re.fullmatch(r'(?:skip|next|skip (?:this|the|to the next))\s*(?:video|song)?',lower):return 'youtube_control',{'action':'next'}
    if re.fullmatch(r'(?:go back to (?:the )?|play (?:the )?|go to (?:the )?)?previous\s+(?:video|song)',lower):return 'youtube_control',{'action':'previous'}
    if re.fullmatch(r'(?:pause|pause (?:the )?(?:video|youtube|music))',lower):return 'youtube_control',{'action':'pause'}
    if re.fullmatch(r'(?:resume|resume (?:the )?(?:video|youtube|music)|play (?:the )?video)',lower):return 'youtube_control',{'action':'play'}
    found=re.fullmatch(r'(?:skip (?:ahead|forward)|forward|rewind|go back)\s*(\d+)?\s*(?:seconds?)?',lower)
    if found:return 'youtube_control',{'action':'rewind' if lower.startswith(('rewind','go back')) else 'forward','seconds':int(found.group(1) or 10)}
    if re.fullmatch(r'(?:open|show|go to)\s+(?:my\s+)?(?:wi[ -]?fi|wireless)(?:\s+settings)?',lower):return 'desktop_control',{'action':'wifi_settings'}
    if re.fullmatch(r'(?:open|show|go to)\s+(?:my\s+)?bluetooth(?:\s+settings)?',lower):return 'desktop_control',{'action':'bluetooth_settings'}
    found=re.fullmatch(r'(?:set|change|turn)\s+(?:the\s+)?(?:computer |system )?volume\s+(?:to\s+)?(\d+)\s*(?:%|percent)?',lower)
    if found:return 'desktop_control',{'action':'set_volume','level':int(found.group(1))}
    if re.fullmatch(r'(?:volume up|increase (?:the )?volume|turn (?:the )?volume up)',lower):return 'desktop_control',{'action':'volume_up'}
    if re.fullmatch(r'(?:volume down|decrease (?:the )?volume|lower (?:the )?volume|turn (?:the )?volume down)',lower):return 'desktop_control',{'action':'volume_down'}
    if re.fullmatch(r'(?:mute|mute (?:the )?(?:computer|sound|volume))',lower):return 'desktop_control',{'action':'mute'}
    if re.fullmatch(r'(?:unmute|unmute (?:the )?(?:computer|sound|volume))',lower):return 'desktop_control',{'action':'unmute'}
    if re.fullmatch(r'(?:open|go to|show)\s+(?:the\s+)?(?:desktop|downloads|documents)(?:\s+folder)?',lower):
        root=re.search(r'(desktop|downloads|documents)',lower).group(1)
        return 'file_browser',{'action':'open','target':root}
    found=re.fullmatch(r'(?:open|go to)\s+(?:the\s+)?folder\s+(.+)',t,re.I)
    if found:return 'file_browser',{'action':'open','target':found.group(1).strip(' "\'')}
    found=re.fullmatch(r'(?:select|choose)\s+(?:the\s+)?(?:file\s+)?(.+)',t,re.I)
    if found:return 'file_browser',{'action':'select','target':found.group(1).strip(' "\'')}
    if re.fullmatch(r'(?:go )?(?:back|up)(?: one)?(?: folder)?',lower):return 'file_browser',{'action':'open','target':'..'}
    if re.fullmatch(r'(?:show|open) (?:the )?(?:file picker|files|attachments)',lower):return 'file_browser',{'action':'list'}
    return None
