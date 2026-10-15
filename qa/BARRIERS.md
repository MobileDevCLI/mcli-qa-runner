# BARRIERS.md — Android QA runner (no-KVM box)

| # | Barrier | Workaround (real, in use) | Status |
|---|---------|---------------------------|--------|
| 1 | No usable KVM (/dev/kvm exists but vCPU hangs at 0%) | TCG software emulation (`-accel off`), API 30 google_apis x86_64 AVD `cs`, headless, swiftshader GPU. Cold boot ~5–9 min. | Working |
| 2 | TCG too slow for Android's 60s system_server Watchdog → system_server restarts/"device offline" | `wd_guard.py` keeps a JDWP debugger attached to system_server (Watchdog skips killing when a debugger is connected); re-attaches after restarts | Working (still sees ~1 restart during boot) |
| 3 | Rob's release APKs are arm64-only (RentHarbor, BizHarbor native libs) | Image includes ARM native-bridge translation (abilist x86_64,x86,arm64-v8a,armeabi-v7a) — installs/runs unmodified | Working |
| 4 | Box RAM 16 GB shared with Chrome (X routines); emulator + Gradle caused OOM → box reboot (17:36 PT) and loss of in-flight QA output | Emulator capped `-memory 1536` (EMU_MEM env), 1 emulator only, Gradle `-Xmx2g` single daemon + `gradle --stop` after builds. qemu RSS ~3.2 GB with TCG translation cache. | Mitigated |
| 5 | Can't add swap (no root/sudo, no swapon) | Memory caps above instead; keep ≥4 GB available | Open (needs root) |
| 6 | No physical phone access for tap testing | UI Automator-driven crawler (`qa/crawler.py`) taps every clickable on every screen, BACKs out, screenshots each step, screenrecord video in 165s segments | Working |
| 7 | `adb input text` can't type unicode/specials | per-char shell escaping for ASCII; ADB_INPUT_TEXT broadcast for unicode (requires ADBKeyboard IME — not yet installed, unicode cases are skipped silently) | Partial |
| 8 | Public file hosts unusable for APK delivery | GitHub release assets in MobileDevCLI/app-downloads | Working |
| 9 | Under TCG, SystemUI itself ANRs and its "not responding" dialog covers the app, stalling the crawler | `settings put global hide_error_dialogs 1` set after boot (start-emu.sh); crawler still detects target-app ANRs via logcat | Working |
| 10 | Box rebooted mid-run (OOM) and restore lost built APKs | QA builds DEBUG APKs itself (no keystore), `--no-daemon -Xmx2g`, emulator stopped during builds; PROGRESS.md checkpoints | Working |
| 11 | Under TCG, device `screencap` takes ~55s and device `screenrecord` starves the CPU (crawler stalled, blank shots) | Host-side capture via emulator console: `adb emu screenrecord screenshot` (0.3s) and `adb emu screenrecord start` (webm video, 4 fps) | Working |
| 12 | TCG throughput ~1 crawler step/40s (40 steps ≈ 28 min/app); 9s input-dispatch ANR threshold trips on idle-trivial work (load ~14) | Short crawls per run, PROGRESS.md checkpoints; app ANRs under TCG are triaged against code before being called real bugs | Mitigated |
| 13 | Shared box: ~7 GB used by processes outside this namespace leaves too little for emulator (~4 GB) + 4 GB reserve for X sweeps | memguard.sh kills emulator+QA chunk below 4.3 GB available; overnight.sh only (re)boots when >8 GB available and resumes from per-app markers | Working (throughput depends on other agents' load) |
