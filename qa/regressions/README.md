Regression rule: every bug found by QA (crawler, stress, or Rob) gets a permanent script here:
regressions/<app>/<YYYYMMDD>-<short-bug-name>.sh  — args: <pkg> <outdir>; exit non-zero if the bug reproduces.
gate.sh runs all of them; a build cannot ship while any fails. Never delete a regression test.
