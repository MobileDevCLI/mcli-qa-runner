#!/bin/bash
# Usage: qa/run.sh <cleanscan|rentharbor|bizharbor> [max_steps=120] [apk_override]
set -e; Q="$(cd "$(dirname "$0")" && pwd)"; . "$Q/env.sh"
APP=$1; STEPS=${2:-120}; L=$(grep "^$APP|" "$Q/apps.conf") || { echo "unknown app"; exit 2; }
PKG=$(cut -d'|' -f2 <<<"$L"); APK=${3:-$ROOT/$(cut -d"|" -f3 <<<"$L")}
adb wait-for-device
OUT="$Q/reports/$APP-$(date +%Y%m%d-%H%M%S)"; mkdir -p "$OUT"
adb uninstall "$PKG" >/dev/null 2>&1 || true
adb install -r -t -g "$APK" | tee "$OUT/install.txt"
python3 "$Q/crawler.py" "$PKG" "$OUT" "$STEPS"
echo "Report: $OUT/report.html"
