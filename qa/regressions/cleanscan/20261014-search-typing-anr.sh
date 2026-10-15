#!/bin/bash
# Bug: ANR (input dispatch timeout) while typing into home search (crawler step 2, 2026-10-14). Exit 1 if reproduces, 3 if setup fails.
PKG=$1; U="python3 $(dirname "$0")/../../ui.py"
adb shell cmd statusbar collapse; adb shell input keyevent 3; adb shell settings put system user_rotation 0
adb shell pm clear $PKG >/dev/null; adb logcat -c
adb shell monkey -p $PKG -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1
$U tap-text Skip || echo "note: no onboarding Skip shown, continuing"   # monkey stress can leave onboarding dismissed
$U tap-class EditText || { echo "setup: no search field"; exit 3; }
for i in 1 2 3 4 5; do adb shell input text "QA%stest%s123%sinvoice"; done; sleep 15
if adb logcat -d -v brief ActivityManager:E '*:S' | grep -q "ANR in $PKG"; then echo "REPRODUCED: ANR"; exit 1; fi
adb shell pidof $PKG >/dev/null || { echo "app died"; exit 1; }
echo "OK: no ANR after 100 chars"
