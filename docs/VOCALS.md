# Automatic browser voice pilot

Updated 3 November 2026. Recognized browser/media commands no longer require Run task or Enter. Say Hey Jarvis, then Open YouTube; Search Kishore Kumar; Play the third video; Set volume to 10 percent; Skip this video; Open Netflix; Search Lucifer; Open Amazon; Go back to Netflix; Go to sleep.

This is a limited deterministic parser. It accepts registered-site navigation, browser search and YouTube controls. It does not automatically submit messages, purchases, uploads, arbitrary URLs or unknown long instructions. Those remain drafts. The manual task button remains available for general tasks and existing reviews.

Exact commands can complete without punctuation. Variable-length searches need Windows sentence punctuation to avoid cutting off titles. Text also settles unchanged for one second before interpretation, to allow Windows corrections. This is a heuristic, not proof of speaker intent. There is no maximum speaking duration in Jarvis. The editor supports up to one million characters. Windows may stop dictation independently.

Consecutive recognized sentences execute in order. Only an accepted command prefix is removed. Later words remain queued. The next task waits for the earlier task and voice to finish. Failed or uncertain submission blocks continuation and is not repeated. Unresolved instructions are not silently skipped. Go to sleep ends the session, not Windows.

The wake engine is local Vosk. Desktop dictation uses Windows voice typing. Ollama reasons; it does not transcribe. The web recording button still uses Whisper.

Windows + H requires a focused text field and does not expose final-utterance events here. Foreground browser changes can stop it. Jarvis requests dictation again after work, but Windows may refuse focus or retain its toolbar. Use Windows typing / resume if needed. Siri-style background listening, interruption and universal conversational understanding are not verified. Netflix opening/search is not proof of Continue watching or playback. Verified playback controls are for YouTube.

Windows speech can use Microsoft online processing. No OS privacy settings are changed. Sleep locks the editor and attempts dismissal; confirm Windows stopped, or say Stop listening. Closing Jarvis stops Vosk, but Windows owns its dictation service.

## Evidence

36 unit tests passed, including complete versus unfinished commands, long drafts, unknown actions, ordered consumption, volume and sleep. A controlled Playwright browser fixture executed ten commands in order: YouTube open/search/third-video, volume 10/100, next video, Netflix open/search, Amazon open, sleep. Player and page state were checked. Existing conversation fixtures also passed. These tests did not use real accounts or Windows dictation.

Live owner speech, Windows punctuation, focus recovery and authenticated Netflix playback remain pending. Do not label the full requested workflow verified.

[Microsoft voice typing guide](https://support.microsoft.com/en-us/accessibility/windows/use-voice-typing-to-talk-instead-of-type-on-your-pc).
