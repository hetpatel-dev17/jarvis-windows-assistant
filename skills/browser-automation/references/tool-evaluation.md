# Browser automation options

Checked against upstream sources on 2 November 2026. This comparison is separate from live Jarvis verification.

| Project | What it provides | Fit for this Jarvis |
| --- | --- | --- |
| [Browser Use](https://github.com/browser-use/browser-use) | Python browser agent that turns a task into page observations and actions. Its upstream example supports `ChatOllama`; local browsers are supported. MIT license. | Initially a close functional fit. Version 0.13.14 failed the small local-model trial. Windows reported WinError 225 on an auto-downloaded extension resource during cleanup. This candidate is paused and not enabled. |
| [Microsoft Playwright MCP](https://github.com/microsoft/playwright-mcp) | Structured accessibility snapshots and browser actions exposed to an AI client. Supports local Chromium/CDP connections. Apache-2.0 license. | Recommended next integration candidate after the isolated 0.0.84 demo passed with the existing Ollama model. It does not supply the intent model. Live-profile integration needs ownership/serialization and review checks first. |
| [Stagehand](https://github.com/browserbase/stagehand) | Browser-agent SDK with natural-language interaction/extraction and a local-browser option. MIT license. | Another viable candidate. Its Ollama path and compatibility with this Python app have not been tested in this round. |

## Evaluation boundary

The active driver is still the existing Playwright connection. Do not connect any candidate to that signed-in profile in parallel. Keep the current working workflows available while candidates are evaluated.

The Microsoft pilot is `../scripts/pilot_playwright_mcp.py`. It opens a temporary headless browser and generated local catalog. No saved accounts, paid model API, firmware tools, or physical devices are used. The model can only click/type using current page references and report the result. A fixed independent DOM check verifies that the detail was actually opened.

The Browser Use script is paused by its entry point. Its source remains for audit, not a recommendation to rerun it or bypass the Windows block. Original raw logs remain in the private development workspace.

An optional Microsoft pilot uses a separate environment, not Jarvis's existing environment:

```powershell
uv venv --python 3.13 work/playwright-mcp-pilot/.venv
uv pip install --python work/playwright-mcp-pilot/.venv/Scripts/python.exe mcp==2.1.1 httpx==0.28.1
work/playwright-mcp-pilot/.venv/Scripts/python.exe skills/browser-automation/scripts/pilot_playwright_mcp.py --report work/playwright-mcp-pilot/result.json
```

Node.js/npm and Chrome are required. The script pins Microsoft Playwright MCP 0.0.84. HTTPS verification stays enabled. On a computer using a custom trusted certificate chain, configure that CA correctly rather than disabling TLS verification.

## Observed results

- Microsoft pilot: click -> type -> click -> correct visible SKU, with an independent detail-open check. Passed once in 12.1 seconds using `qwen2.5:7b-instruct-q4_K_M`.
- Browser Use pilot: repeated navigation and failed to complete the goal after its bounded run. Windows also blocked an extension resource during cleanup. No saved accounts were used.
- These are two small pilots, not a controlled benchmark. Starting-page setup, prompts, and agent loops differ. Neither result proves universal website reliability.

Machine-readable observations are in `pilot-results.json`.

## Evidence to collect before adoption

- A goal using an unfamiliar page layout, with no site-specific selectors supplied to the model.
- Actual control state proving navigation, input, and the selected detail were completed.
- Recovery from stale elements and honest failure reporting.
- Preserved review for messages/uploads and no replay after uncertain submission.
- Local-model latency and repeated-action behavior.
- A separately verified path to the existing browser session, then a live owner-approved test.

No candidate is a guarantee of flawless operation on every website. The local model, page state, login requirements, and action verification remain part of the pipeline.
