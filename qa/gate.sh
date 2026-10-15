#!/bin/bash
# Release gate: blocks a build unless crawl + stress + all regression tests pass. Usage: qa/gate.sh <app> [apk]
# Exit 0 = RELEASE OK. Non-zero = BLOCKED.
Q="$(cd "$(dirname "$0")" && pwd)"; APP=$1; FAIL=0
"$Q/run.sh" "$APP" ${GATE_STEPS:-150} "$2" || FAIL=1
OUT=$(ls -d "$Q/reports/$APP-"* | tail -1); PKG=$(grep "^$APP|" "$Q/apps.conf"|cut -d'|' -f2)
"$Q/stress.sh" "$PKG" "$OUT" || FAIL=1
for t in "$Q"/regressions/$APP/*.sh; do [ -e "$t" ] || continue; echo "== regression $(basename $t)"; bash "$t" "$PKG" "$OUT" || { echo "REGRESSION FAIL $t"; FAIL=1; }; done
[ $FAIL = 0 ] && echo "GATE: RELEASE OK ($APP)" || echo "GATE: BLOCKED ($APP) — see $OUT"
exit $FAIL
