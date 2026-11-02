# Ten-site live acceptance check

On 2 November 2026 the owner requested ten real websites, including product search/open, video playback, and harmless ChatGPT/Claude test messages without another approval prompt. Those two messages used the existing signed-in accounts, not anonymous identities.

The experimental Microsoft Playwright MCP adapter took exclusive control of the dedicated Jarvis browser while the web service was paused. It restored that service afterward. The final pass used the existing local Qwen 7B model.

## Result

| Complete | Partial | Incomplete |
| --- | --- | --- |
| Flipkart, YouTube, ChatGPT, Claude, DuckDuckGo, Python documentation | Amazon, Google Translate | Wikipedia, GitHub |

Machine-readable sanitized evidence is in [live-ten-site-results.json](live-ten-site-results.json).

ChatGPT and Claude each received one fixed test message and produced an actual completed reply. No purchase or personal-file upload occurred. YouTube was paused afterward.

## Shared issues discovered

- Full MCP element references were not reliably copied by the small model.
- Compact numeric control IDs and current-page observations improved action execution.
- Retaining many long old snapshots overwhelmed the local context; a fresh observation plus short action history worked better.
- A product link could open a new tab while the controller kept observing the old one. Following newly opened tabs fixed the Flipkart path.
- Scoping observations to `main` hid global search on Wikipedia and GitHub. The next observer needs both global search/navigation and main content.
- On Amazon the model completed search but repeated the wrong action instead of opening a product.
- Google Translate accepted source text, but the expected translated output was not independently confirmed.

These observations describe the experimental adapter, not a failure of the websites themselves. It is not ready to replace the normal Jarvis driver across all tasks.

## Reproduction boundary

The optional `../scripts/live_site_check.py` runner is an acceptance tool, not a normal Jarvis command. It needs the separate MCP pilot environment with `mcp==2.1.1`, `httpx==0.28.1`, `psutil==7.2.2`, Node/npm, and the existing Jarvis installation/browser profile. It temporarily pauses the Jarvis service to avoid parallel controllers.

Without `--approved-test-messages`, it skips both AI message tests. That flag explicitly authorizes only the two fixed prompts in the source. It refuses to reuse an output folder that already records a send attempt. Normal Jarvis submission-review settings were not changed.

Raw snapshots and logs may include account details. They default to a local data directory and must not be committed. The public report contains only test queries, outcomes, and non-identifying evidence.
