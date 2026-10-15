#!/bin/bash
# Environment/adversarial stress scenarios. Usage: qa/stress.sh <pkg> <outdir>
# Each scenario: apply condition -> exercise app -> screenshot -> crash/ANR check. Writes stress.tsv (scenario<TAB>PASS|FAIL<TAB>detail)
PKG=$1; OUT=$2; Q="$(cd "$(dirname "$0")" && pwd)"; . "$Q/env.sh"; mkdir -p "$OUT/stress"; R="$OUT/stress.tsv"; : > "$R"
launch(){ adb shell monkey -p $PKG -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1; sleep $LAUNCH_WAIT; }
crash(){ adb logcat -d -v brief AndroidRuntime:E ActivityManager:E "*:S" | grep -qE "ANR in $PKG( |\$)|Process: $PKG( |,|\$)"; }
run(){ local name=$1; shift; adb logcat -c; "$@"; sleep 2; adb emu screenrecord screenshot "$(realpath $OUT)/stress/$name.png" >/dev/null
  if crash; then adb logcat -d -v brief AndroidRuntime:E ActivityManager:E '*:S' > "$OUT/stress/$name.log"; echo -e "$name\tFAIL\tcrash/ANR, see stress/$name.log" >> "$R"
  elif ! adb shell pidof $PKG >/dev/null; then echo -e "$name\tFAIL\tprocess not running after scenario" >> "$R"
  else echo -e "$name\tPASS\t" >> "$R"; fi; }
taps(){ adb exec-out uiautomator dump /dev/tty | grep -o 'clickable="true"[^>]*bounds="\[[0-9]*,[0-9]*\]\[[0-9]*,[0-9]*\]"' | grep -o '\[[0-9]*,[0-9]*\]\[[0-9]*,[0-9]*\]' | head -${1:-6} | tr '[],' '  ' ; }
s_rotate(){ launch; adb shell settings put system accelerometer_rotation 0; for r in 1 0 3 0 1 0; do adb shell settings put system user_rotation $r; sleep 1.5; done; }
s_dark(){ adb shell cmd uimode night yes; launch; sleep 2; adb shell cmd uimode night no; sleep 2; }
s_font(){ for f in 2.0 0.85 1.3 1.0; do adb shell settings put system font_scale $f; launch; done; }
s_density(){ for d in 280 640 420; do adb shell wm density $d; launch; done; adb shell wm density reset; }
s_smallscreen(){ adb shell wm size 720x1280; launch; adb shell wm size 1600x2560; launch; adb shell wm size reset; launch; }
s_offline(){ adb shell svc wifi disable; adb shell svc data disable; adb shell cmd connectivity airplane-mode enable 2>/dev/null; launch; taps 6 | while read a b c d; do adb shell input tap $(( (a+c)/2 )) $(( (b+d)/2 )); sleep 1; adb shell input keyevent 4; done; adb shell cmd connectivity airplane-mode disable 2>/dev/null; adb shell svc wifi enable; adb shell svc data enable; }
s_slownet(){ adb emu network speed gsm; adb emu network delay umts; launch; sleep 5; adb emu network speed full; adb emu network delay none; }
s_procdeath(){ launch; taps 1 | while read a b c d; do adb shell input tap $(( (a+c)/2 )) $(( (b+d)/2 )); done; sleep 2; adb shell input keyevent 3; sleep 1; adb shell am kill $PKG; sleep 1; launch; }
s_backspam(){ launch; for i in $(seq 1 25); do adb shell input keyevent 4; done; launch; }
s_doubletap(){ launch; taps 8 | while read a b c d; do x=$(( (a+c)/2 )); y=$(( (b+d)/2 )); adb shell "input tap $x $y & input tap $x $y & input tap $x $y"; sleep 1.2; adb shell input keyevent 4; done; }
s_monkey(){ adb shell monkey -p $PKG --throttle 80 --pct-syskeys 0 --ignore-security-exceptions -s 42 1500 > "$OUT/stress/monkey.txt" 2>&1; grep -qE "CRASH|NOT RESPONDING" "$OUT/stress/monkey.txt" && echo "monkey reported crash" >&2; launch; }
s_permdeny(){ for p in $(adb shell dumpsys package $PKG | grep -oE 'android.permission\.[A-Z_]+: granted=true' | cut -d: -f1 | sort -u); do adb shell pm revoke $PKG $p 2>/dev/null; done; adb shell am force-stop $PKG; launch; taps 6 | while read a b c d; do adb shell input tap $(( (a+c)/2 )) $(( (b+d)/2 )); sleep 1.5; adb shell input keyevent 4; adb shell input keyevent 4; launch >/dev/null; done; }
s_lowstorage(){ FREE=$(adb shell df /data | awk 'NR==2{print $4}'); adb shell "fallocate -l $(( (FREE-60000)*1024 )) /data/local/tmp/qa_fill" 2>/dev/null; launch; taps 4 | while read a b c d; do adb shell input tap $(( (a+c)/2 )) $(( (b+d)/2 )); sleep 1.5; adb shell input keyevent 4; done; adb shell rm -f /data/local/tmp/qa_fill; }
s_inputs(){ launch; python3 "$Q/fuzz_inputs.py" "$PKG" "$OUT/stress"; }
for s in rotate dark font density smallscreen offline slownet procdeath backspam doubletap inputs permdeny lowstorage monkey; do echo "== $s"; run $s s_$s; done
adb shell settings put system font_scale 1.0; adb shell cmd uimode night no; adb shell settings put system user_rotation 0
cat "$R"; ! grep -q FAIL "$R"
