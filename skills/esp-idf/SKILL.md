---
name: esp-idf
description: Planned native Espressif toolchain workflow for ESP-IDF project configuration, building, and reviewed flashing. Use only when the owner chooses this later pipeline.
---

# ESP-IDF

Status: planned and disabled. Do not install ESP-IDF or modify the Windows development environment during browser-first testing.

When selected, check the installed toolchain and official Espressif documentation. Identify the chip target, project version, SDK configuration, connected board, and serial port. Keep this native ESP-IDF path distinct from using an ESP board through Arduino CLI.

Verify a build without flashing. Then obtain approval for the selected target and port, recheck that device, flash once, and report actual tool output. Serial output and physical-device behavior are separate verification steps. Never call a successful build a successful hardware test.
