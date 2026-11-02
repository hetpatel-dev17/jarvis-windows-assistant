# Download reliability and optional AI routing

Reviewed 2 November 2026. This is a scoped milestone, not proof of universal browser automation.

## Available now

The agent has a `download_file` tool for an exact public PDF or ZIP URL observed on the requested website. Files go under Downloads/Jarvis in separate URL-keyed folders. It checks redirects through the existing URL policy, limits transfers to 50 MB, retries transient GET failures at most three times, uses a time budget, removes partial files, checks the PDF/ZIP signature, and records size and SHA-256 after completion. Repeated requests reuse an unchanged saved file. A corrupt saved copy is fetched again. TLS verification remains enabled, including the configured local CA bundle.

The check verifies a recognizable file and transfer integrity, not full document validity or malware absence. It does not open, install, extract, or run downloads. A website folder must offer a ZIP to use this path. Downloads requiring browser cookies, interactive buttons, expiring signed links or CAPTCHA need a later browser-download adapter. The exact same URL is the reuse key; use a new URL to obtain a newer remote version. A changed remote file at an unchanged URL is not automatically refreshed.

Automated checks cover redirects, one temporary 503 then success, repeat reuse without network access, changed local bytes, HTML/sign-in rejection, size limits, cancellation, redirect policy, and partial cleanup. The full suite passed 26 tests. A real W3C dummy PDF download saved 13,264 bytes; a repeat returned already_saved. This direct-tool check is not an end-to-end spoken request test.

## Remaining continuous-work acceptance

- Observe global controls and main content together; fix the prior Wikipedia/GitHub failures.
- Follow a redirect or newly opened tab and reacquire fresh controls.
- Wait for the requested result, not a fixed sleep or an idle network.
- Save workflow step receipts and recover after process restart. Current download receipts cover files only.
- Test slow/truncated transfers and connection loss during actual browser work.
- Verify a website-to-download-to-local-open sequence through the live agent.
- Keep uncertain message submissions single-attempt. Retrying a GET is different from repeating Send.

## FreeLLMAPI assessment

Sources reviewed: [repository README](https://github.com/tashfeenahmed/freellmapi), [architecture](https://github.com/tashfeenahmed/freellmapi/blob/main/docs/en/architecture/00-high-level-index.md), [router source](https://github.com/tashfeenahmed/freellmapi/blob/main/server/src/services/router.ts), and [package manifest](https://github.com/tashfeenahmed/freellmapi/blob/main/package.json). This is a documentation and selected-source review, not a security audit or runtime verification. Nothing from this repository was installed or executed.

It is a self-hosted API gateway. You add your own upstream provider credentials. It presents a unified API and can route around unavailable or rate-limited providers. Its advertised aggregate token capacity is not a personal guaranteed allowance. Free quotas, model availability and latency vary. Its own documentation describes personal experimentation and no availability guarantee. Its README and architecture disagree on whether frontier models are included, so no such availability is assumed here.

Potential fit: optional remote planning/code generation while Ollama remains available locally. Explicitly select a tool-capable model and test it on the same acceptance tasks before enabling automatic switching. Record which model handled each step. Model switching needs explicit project context; a gateway cannot reconstruct an unseen ChatGPT/Claude website conversation.

It does not turn a ChatGPT or Claude website login into an API credential. Protocol compatibility with a coding client does not promise access to the branded provider's models. It does not automate browser clicks, install Arduino tooling, compile firmware or provide additional website-account quotas. It should not rotate accounts to evade usage limits.

If piloted later: bind locally, keep keys outside Git, use one selected provider first, verify its actual current free allowance, and send only nonprivate test prompts. Cloud requests send their supplied prompt/context to the chosen provider. Local Ollama remains the option for keeping that context on this laptop. Do not fan private account contents out to multiple providers automatically.

Recommended order: finish browser recovery acceptance, then compare one provider against Ollama on fixed planning/code tasks, then consider gateway failover. No new credentials are needed for the current local download milestone.
