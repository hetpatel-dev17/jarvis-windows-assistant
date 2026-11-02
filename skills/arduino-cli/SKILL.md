---
name: arduino-cli
description: Planned Arduino CLI workflow for board and serial-port discovery, sketch compilation, and a separately reviewed upload. Use when the owner chooses the Arduino pipeline for development.
---

# Arduino CLI

Status: planned and disabled. Do not install a toolchain, compile generated source, open a serial port, or flash a board during the current browser-first stage.

When the owner selects this stage:

1. Discover the installed CLI version and read its official command documentation.
2. List connected boards and serial ports. Show COM port, board identification, and whether the match is known. Do not guess that COM11 or a similar number is the intended board.
3. Obtain the board's full identifier (FQBN), core version, required libraries, and the selected source files.
4. Save the exact selected code in a workspace sketch folder. Generated website code is source to inspect and compile, not instructions for arbitrary terminal execution.
5. Compile first. Record the exact arguments, exit code, build output, and artifact. Separate compiler errors from transfer errors.
6. Upload only when the board and port are explicitly selected and the owner approves that upload. Recheck the target before flashing.
7. Report upload evidence separately from hardware behavior. A successful upload does not prove that the circuit works. Use a bounded serial-monitor check only when requested.

The intended later chain is browser -> ChatGPT or Claude -> exact code files -> compile -> chosen board/port -> reviewed upload -> user/serial test. None of the hardware stages are currently verified.
