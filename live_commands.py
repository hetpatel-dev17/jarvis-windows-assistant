"""Automatic low-impact command boundaries; never infer arbitrary long intent."""
import re
import browser_commands
import command_routes


def candidate(text):
    """Return a complete command, or None while the draft is incomplete.

    Variable-length search terms need a Windows sentence boundary. Exact
    navigation/media commands can complete without punctuation. No draft limit.
    """
    original=text.strip()
    t=re.sub(r'^(?:(?:hey|hello)\s+)?jarvis[,\s]+','',original,flags=re.I)
    t=re.sub(r'^(?:now |please |okay |ok )+','',t,flags=re.I)
    t=re.sub(r'^no[, ]+no[, ]*','',t,flags=re.I)
    t=re.sub(r'[.!?]+$','',t).strip()
    if t.casefold() in ('go to sleep','shut down go to sleep','go to sleep jarvis'):
        return ('sleep','')
    if re.fullmatch(r'(?:set|turn|increase|decrease|lower|reduce|turn down|turn up)(?: the)? volume to (\d+)\s*(?:%|percent)',t,re.I):
        level=int(re.search(r'\d+',t).group())
        if level>100:return None
        t=f'set volume to {level} percent'
    found=re.fullmatch(r'(?:go |switch |take me )?back to (youtube|netflix|amazon|flipkart)',t,re.I)
    if found:t='open '+found.group(1)
    search=re.fullmatch(r'(?:search(?: for)?|find|look up)\s+(.+)',t,re.I)
    if search:
        # A pause alone cannot delimit a song name or a long query.
        if not re.search(r'[.!?]\s*$',original):return None
        if not re.search(r'\b(?:on|in|here)\b',search.group(1),re.I):t='search '+search.group(1)+' on this website'
    command=browser_commands.parse(t,'browser')
    if command and command[0]=='browser_control':
        params=command[1]
        # Only registered sites and ordinary navigation, never messages/uploads.
        if params['action']=='open' and params['target'] not in browser_commands.SITES:return None
        return 'submit',t
    command=command_routes.parse(t)
    if command and command[0]=='youtube_control':return 'submit',t
    return None


def next_command(text):
    """Take one sentence at a time and preserve any later words verbatim."""
    for match in re.finditer(r'[.!?](?:\s+|$)',text):
        end=match.end()
        result=candidate(text[:end])
        if result:return (*result,end)
        # Do not skip an unresolved instruction to act on a later sentence.
        return None
    result=candidate(text)
    return (*result,len(text)) if result else None
