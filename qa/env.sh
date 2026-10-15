# CI/KVM env: SDK comes from the runner; fall back to the box SDK locally.
export ANDROID_HOME=${ANDROID_HOME:-/home/box/android-sdk}; export ANDROID_SDK_ROOT=${ANDROID_SDK_ROOT:-$ANDROID_HOME}
export PATH=$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH
export LAUNCH_WAIT=${LAUNCH_WAIT:-4}   # KVM emulator: app cold start ~2s (TCG needed 12s)
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
