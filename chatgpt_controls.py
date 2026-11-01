import re
import time
from pathlib import Path
from urllib.parse import urlparse
from site_workflows import site_page,visible_first,normalized


EDITORS='#prompt-textarea,[contenteditable="true"][role="textbox"],[contenteditable="true"],textarea:not([id^="pending-"])[aria-label="Ask ChatGPT"],textarea:not([id^="pending-"])[placeholder*="Message"],textarea:not([id^="pending-"])[placeholder*="Ask"]'
ASSISTANTS='[data-message-author-role="assistant"],[data-testid="assistant-message"],[data-chatgpt-selection-message-id]:has([data-markdown-text-style])'
SEND_BUTTONS='button[data-testid="send-button"],button[aria-label="Send prompt"],button[aria-label="Send message"],button[aria-label="Send"],button[type="submit"]'


def active_editor(page):
    return page.locator(EDITORS).filter(visible=True).first


def active_form(page):
    return active_editor(page).locator('xpath=ancestor::form[1]')


def page_for(browser):
    page=site_page(browser,'chatgpt.com','https://chatgpt.com/')
    active_editor(page).wait_for(state='visible',timeout=25000)
    page.wait_for_timeout(300)
    return page


def editor_text(editor):
    return normalized(editor.input_value() if editor.evaluate('(e)=>e.tagName==="TEXTAREA"') else editor.inner_text())


def chat_links(page):
    return page.locator('a[href^="/c/"],a[href^="https://chatgpt.com/c/"]').filter(visible=True).evaluate_all('es=>es.map(e=>({name:(e.getAttribute("title")||e.innerText||"").trim(),url:e.href})).filter(e=>e.name)')


def open_chat(page,name,force_search=False):
    targets=[x for x in chat_links(page) if x['name'].casefold()==name.strip().casefold()]
    if len(targets)!=1 or force_search:
        # Search is a read-only navigation action. Never pick an approximate title.
        search=visible_first(page.get_by_role('button',name=re.compile(r'^Search(?: chats)?$',re.I)))
        if search is None:
            search=visible_first(page.get_by_role('link',name=re.compile(r'^Search chats$',re.I)))
        if search:
            search.click()
            fields=page.locator('input[placeholder*="Search" i],input[aria-label*="Search" i],input[type="search"]').filter(visible=True)
            fields.first.wait_for(state='visible',timeout=10000)
            visible_first(fields).fill(name)
            page.wait_for_timeout(1200)
            dialogs=page.get_by_role('dialog').filter(visible=True)
            scope=dialogs.last if dialogs.count() else page
            found=scope.get_by_text(re.compile(r'^'+re.escape(name.strip())+r'$',re.I)).filter(visible=True)
            if found.count()==1:
                found.click()
                return
        raise RuntimeError('I did not find one exact chat with that name. Check the chat name, or open the chat once yourself.')
    if urlparse(page.url).path!=urlparse(targets[0]['url']).path:
        page.goto(targets[0]['url'],wait_until='commit',timeout=45000)
    else:
        page.bring_to_front()


def attachment_names(page):
    return active_form(page).evaluate_all(r'''forms=>[...new Set(forms.flatMap(form=>[...form.querySelectorAll('[title],span,div')].flatMap(e=>[e.getAttribute('title')||'',e.children.length===0?(e.textContent||'').trim():'']).filter(x=>/^[^\r\n\\/]{1,200}\.(pdf|docx?|xlsx?|csv|pptx?|txt|png|jpe?g|webp|zip)$/i.test(x))))]''')


def send_and_read(page,text,approve,cancelled):
    editor=active_editor(page)
    if text:
        editor.fill(text)
    draft=editor_text(editor)
    files=attachment_names(page)
    if not draft and not files:
        raise RuntimeError('The ChatGPT composer is empty. Say what you want to ask first.')
    before=page.locator(ASSISTANTS).filter(visible=True).count()
    url=page.url
    approve('Send this to ChatGPT?\n\nChat: '+page.title()+'\n\nMessage:\n'+draft+'\n\nAttachments: '+(', '.join(files) if files else 'No named attachments detected. Check the composer.'))
    if cancelled():
        raise RuntimeError('Stopped before sending.')
    if page.url!=url or editor_text(editor)!=draft or attachment_names(page)!=files:
        raise RuntimeError('The chat, message, or attachments changed after approval. Nothing was submitted.')
    send=visible_first(active_form(page).locator(SEND_BUTTONS))
    ready_deadline=time.monotonic()+45
    while (send is None or not send.is_enabled()) and time.monotonic()<ready_deadline:
        if cancelled():raise RuntimeError('Stopped before sending.')
        page.wait_for_timeout(300)
        send=visible_first(active_form(page).locator(SEND_BUTTONS))
    if send is None or not send.is_enabled():
        raise RuntimeError('ChatGPT is not ready to send. Check for an upload in progress or a sign-in prompt.')
    if page.url!=url or editor_text(editor)!=draft or attachment_names(page)!=files:
        raise RuntimeError('The draft or destination changed while waiting. Nothing was submitted.')
    send.click()
    deadline=time.monotonic()+100
    previous='';stable=0
    while time.monotonic()<deadline:
        if cancelled():
            return {'status':'sent','message':'The ChatGPT message was submitted. Reading was stopped. It was not submitted again.'}
        assistants=page.locator(ASSISTANTS).filter(visible=True)
        if assistants.count()>before:
            answer=assistants.last.inner_text().strip()
            streaming=page.locator('button[data-testid="stop-button"],button[aria-label="Stop"],button[aria-label="Stop response"],button[aria-label*="Stop streaming"],button[aria-label*="Stop generating"]').filter(visible=True).count()>0
            stable=stable+1 if answer and answer==previous and not streaming else 0
            previous=answer
            if stable>=2:
                if files and set(attachment_names(page))&set(files):
                    return {'status':'sent_unconfirmed','message':'ChatGPT replied, but an approved attachment is still in the composer. Check the chat before retrying. Nothing will be resent automatically.'}
                return {'status':'answered','message':answer,'chat_url':page.url}
        page.wait_for_timeout(1000)
    return {'status':'sent_unconfirmed','message':'The message was submitted once, but the reply was not confirmed. Check ChatGPT. I will not resend it.'}


def control(browser,action,text='',name='',path='',files=None,approve=None,cancelled=lambda:False):
    if cancelled():
        raise RuntimeError('Stopped by you.')
    page=page_for(browser)
    if action in ('ask','send','attach','attach_send') and approve is None:
        raise RuntimeError('This action requires the Jarvis approval box.')
    if action=='open':
        return {'status':'ok','message':'ChatGPT is open.'}
    if action=='new_chat':
        page.goto('https://chatgpt.com/',wait_until='commit',timeout=45000)
        active_editor(page).wait_for(state='visible',timeout=20000)
        return {'status':'ok','message':'A new ChatGPT chat is open.'}
    if action in ('open_chat','search_chat'):
        open_chat(page,name,force_search=action=='search_chat')
        return {'status':'ok','message':'Opened the ChatGPT chat named '+name+'.'}
    if action=='list_chats':
        return {'status':'ok','chats':chat_links(page)[:40],'message':'These are the chat titles currently available in the sidebar.'}
    if action in ('ask','send'):
        return send_and_read(page,text,approve,cancelled)
    if action=='attach_send':
        if files is None:raise RuntimeError('The file picker is not available.')
        selected=files.attachment(path or None)
        stat=selected.stat();url=page.url
        editor=active_editor(page)
        initial=editor_text(editor)
        requested=text or initial or 'Please confirm that you can see the attached file. Do not summarize it.'
        current_files=attachment_names(page)
        expected_files=set(current_files)|{selected.name}
        approve(f'Upload and SEND this file to ChatGPT?\n\nFile: {selected.name}\nLocation: {selected}\nSize: {stat.st_size:,} bytes\nChat: {page.title()}\n\nMessage:\n{requested}\n\nAttachments: '+', '.join(sorted(expected_files))+'\n\nOne approval covers upload and the final Send click.')
        def unchanged_file():
            check=files.validate(selected).stat()
            if cancelled():raise RuntimeError('Stopped before sending.')
            if page.url!=url or files.attachment()!=selected or check.st_size!=stat.st_size or check.st_mtime_ns!=stat.st_mtime_ns:
                raise RuntimeError('The file or destination changed after approval. Nothing was submitted.')
        unchanged_file()
        if editor_text(editor)!=initial or attachment_names(page)!=current_files:
            raise RuntimeError('The message or attachments changed after approval. Nothing was submitted.')
        if selected.name not in current_files:
            uploaded=control(browser,'attach',path=str(selected),files=files,approve=lambda _:unchanged_file(),cancelled=cancelled)
            if uploaded['status']!='attached':return uploaded
        def approved_submission(_):
            unchanged_file()
            if set(attachment_names(page))!=expected_files or editor_text(editor)!=normalized(requested):
                raise RuntimeError('The final message or attachment list differs from what you approved. Nothing was submitted.')
        return send_and_read(page,requested,approved_submission,cancelled)
    if action=='attach':
        if files is None:
            raise RuntimeError('The file picker is not available.')
        selected=files.attachment(path or None)
        stat=selected.stat();url=page.url
        approve(f'Upload this file to ChatGPT?\n\nFile: {selected.name}\nLocation: {selected}\nSize: {stat.st_size:,} bytes\nChat: {page.title()}\n\nThe file will leave this computer. It will be attached, but the chat message will not be sent yet.')
        if cancelled():
            raise RuntimeError('Stopped before uploading.')
        check=files.validate(selected).stat()
        if page.url!=url or files.attachment()!=selected or check.st_size!=stat.st_size or check.st_mtime_ns!=stat.st_mtime_ns:
            raise RuntimeError('The file or destination chat changed. Nothing was uploaded.')
        inputs=active_form(page).locator('input[type="file"]')
        chosen=None
        for index in range(inputs.count()):
            item=inputs.nth(index)
            accept=(item.get_attribute('accept') or '').lower()
            if not accept or accept.strip() in ('*','*/*') or selected.suffix.lower() in accept or 'application/pdf' in accept and selected.suffix.lower()=='.pdf':
                chosen=item;break
        if chosen is None:
            raise RuntimeError('The ChatGPT file attachment control was not found. Open its attachment menu and try again.')
        before=page.get_by_text(selected.name,exact=True).count()
        chosen.set_input_files(str(selected))
        deadline=time.monotonic()+35
        while time.monotonic()<deadline:
            if page.get_by_text(selected.name,exact=True).count()>before:
                return {'status':'attached','message':selected.name+' is visible as an attachment in ChatGPT. Check that its upload finishes before sending your message.'}
            page.wait_for_timeout(300)
        return {'status':'upload_unconfirmed','message':'The file was passed to ChatGPT once, but its attachment preview was not confirmed. Check the composer before trying again.'}
    if action=='read_reply':
        replies=page.locator(ASSISTANTS).filter(visible=True)
        if not replies.count():
            raise RuntimeError('There is no ChatGPT reply to read in this chat yet.')
        return {'status':'ok','message':replies.last.inner_text().strip()}
    raise ValueError('Unknown ChatGPT control.')
