# Jarvis Windows Assistant

[![Checks](https://github.com/hetpatel-dev17/jarvis-windows-assistant/actions/workflows/checks.yml/badge.svg)](https://github.com/hetpatel-dev17/jarvis-windows-assistant/actions/workflows/checks.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

A personal Windows assistant that finds local files from remembered name fragments, opens documents and media, and controls selected website workflows through voice or text.

Built on **[OpenJarvis](https://github.com/open-jarvis/OpenJarvis)**, **Ollama**, **Whisper**, **ElevenLabs**, and **Playwright**. This is an independent integration project. It is not the official OpenJarvis application.

**Stage: working prototype.** Features are being verified one pipeline at a time before a final interface is built. See the [verification matrix](docs/VERIFICATION.md) and [roadmap](docs/ROADMAP.md).

## What it does

| Area | Current behavior |
| --- | --- |
| Windows files | Find documents, folders, pictures, music, and videos using fragments or small spelling mistakes. Show numbered matches. Open the chosen result in its Windows app. |
| Voice | Button-based recording, local Whisper transcription, and one ElevenLabs playback channel. Multiple UI tabs cannot replay the same reply. |
| Local AI | OpenJarvis orchestration using a local Ollama model. Common commands have deterministic routes. |
| YouTube | Search and play, pause/resume, next/previous, seek, mute/unmute, and verified volume changes. |
| ChatGPT website | New chats, chat-name search, prompt submission, response readback, and approved file upload plus Send. |
| WhatsApp Web | Prepare a message for an exact recipient. Send after approval. Check for an outgoing bubble. Avoid automatic retries of uncertain sends. |
| Windows settings | Speaker volume and shortcuts to Wi-Fi and Bluetooth settings. |
| Gmail / Calendar | Browser access is wired. Authenticated reading still needs acceptance testing. |

## Start on Windows

Requirements: Windows 10/11 x64, [Git for Windows](https://git-scm.com/downloads/win), [Ollama](https://ollama.com/download/windows), Chrome or Edge, an ElevenLabs account/API key, and space for local AI and speech models. Voice service quotas still apply.

1. Clone this repository, or download and extract its source ZIP.
2. Double-click **Setup Windows.cmd**. Leave the folder in a permanent location.
3. Setup downloads a checksum-verified uv tool, installs Python 3.12 and dependencies, and downloads the speech and default Ollama models.
4. Paste the ElevenLabs key into the hidden setup prompt. It is encrypted for the current Windows account.
5. Open **Start Jarvis** on the Desktop.
6. Use **Open normal sign-in browser**. Sign in to the websites yourself. Close that dedicated browser window. Click **Finish sign-in** in Jarvis.

```powershell
git clone https://github.com/hetpatel-dev17/jarvis-windows-assistant.git
cd jarvis-windows-assistant
.\Setup-Windows.ps1
```

The app opens at `127.0.0.1:8766`. Always use the launcher so it supplies the local access token. Setup for a fresh Windows account has not yet had a complete clean-machine acceptance test. The existing development installation has passed the checks listed in the verification matrix.

The default model is `qwen2.5:7b-instruct-q4_K_M`. Developers can set `JARVIS_MODEL` before starting the app to use another compatible installed Ollama model.

## Try speaking

Press **Speak**, talk, then press **Finish speaking**. Keep **Run spoken commands automatically** checked to run the transcript. Turn it off to review the text first.

```text
Open Desktop.
Find something like project roadmap on Desktop.
Open match one.
Find holiday video in Videos.
Find budget in computer.

Search relaxing music on YouTube and play the first video.
Next video.
Previous video.
Mute.
Unmute.
Volume plus.
Volume max.
Set volume to 30 percent.
Computer volume down.

Open a new chat in ChatGPT.
Ask ChatGPT: Explain solar panels in simple words.
Select the PDF.
Attach and send selected file to ChatGPT.
Stop voice.
Stop task.
```

See [Commands.txt](Commands.txt) for more examples.

## How file search works

Search compares **names**, not file contents. It ranks name fragments and approximate word matches. Desktop, Downloads, Documents, Pictures, Music, Videos, the user home folder, and available local/removable drives are searchable.

Searches are bounded to keep Jarvis responsive. A whole-computer search checks at most 60,000 entries or about six seconds of traversal. Partial results are marked as partial. Narrow the folder to search deeper. System/dependency folders, private settings, hidden paths, and filesystem links are skipped. Offline or permission-restricted locations may be unavailable.

Choose a numbered match before opening an uncertain name. Common documents, pictures, audio, video, and archives open through Windows file associations. Executables, scripts, and shortcuts are not launchable through this operator. Jarvis reports that it asked Windows to open the item; it does not claim to have inspected the destination app.

Local opening and cloud upload are separate. ChatGPT attachments still use the restricted upload picker and approval flow. The current upload limit is 25 MB.

## Data and access

- Ollama reasoning and Whisper transcription run locally.
- ElevenLabs receives the text of spoken replies. Voice usage can cost money.
- Website prompts, messages, and approved attachments go to the selected service.
- Runtime files, the encrypted key, models, and the dedicated browser profile live in `%LOCALAPPDATA%\OpenJarvis`.
- The app and browser-control ports bind to localhost. API calls require a local token and pass origin checks.
- Website login happens in regular Chrome/Edge. Passwords and verification challenges are handled by the user.
- Sending messages and uploading files require a visible review. A declined or uncertain send is not automatically retried.

No credentials, personal documents, session cookies, browser profiles, or model files are included in this repository.

## Development and checks

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
python tests/check_youtube_browser.py
node --check ui.js
```

The browser fixture check requires `playwright` and Chrome, or `python -m playwright install chromium` for the Chromium fallback. Fixtures do not send messages or upload real documents. GitHub Actions runs filename/operator tests, browser fixtures, JavaScript syntax, Python compilation, and PowerShell parsing on Windows.

See [architecture](docs/ARCHITECTURE.md), [contributing](CONTRIBUTING.md), and [security reporting](SECURITY.md).

## Credits and license

Maintained by [hetpatel-dev17](https://github.com/hetpatel-dev17). Development uses AI coding assistance, with verification recorded separately from claims of functionality.

OpenJarvis supplies the agent framework, Ollama engine integration, and speech backends. The custom Windows operator, local UI, and focused workflow integrations live here. See [NOTICE](NOTICE) and the [Apache-2.0 license](LICENSE).
