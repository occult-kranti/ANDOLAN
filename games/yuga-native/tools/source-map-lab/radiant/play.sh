#!/bin/sh
# Launch a staged original or jade map. The two editions link to one host-game data set.
set -eu
variant=${1:-jade}
[ "$#" -eq 0 ] || shift
case "$variant" in
    original|jade) ;;
    *) echo "Usage: play.sh [jade|original] [--check] [additional DarkPlaces arguments]" >&2; exit 2 ;;
esac
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
root=${YUGA_RADIANT_DIR:-"$here"}
if [ ! -x "$root/runtime/bin/darkplaces" ] && [ -z "${YUGA_RADIANT_DIR:-}" ]; then
    root=/workspace/ANDOLAN-local/dust2-map-lab/radiant
fi
engine="$root/runtime/bin/darkplaces"
[ -x "$engine" ] && [ -r "$root/editions/$variant/data/q3dust2-jb-beta6-$variant.pk3" ] || {
    echo "Set YUGA_RADIANT_DIR to the staged directory containing runtime/ and editions/." >&2
    exit 2
}
check=false
if [ "${1:-}" = "--check" ]; then check=true; shift; fi
if [ -z "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]; then check=true; fi
export LD_LIBRARY_PATH="$root/runtime/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
mkdir -p "$root/profiles"
if [ "$check" = false ]; then
    mkdir -p "$root/profiles/$variant"
    exec "$engine" -nexuiz -basedir "$root/editions/$variant" -userdir "$root/profiles/$variant" \
        -window -width 1280 -height 720 +sv_public 0 +map q3dust2-jb-beta6 +defer 3 "cmd join" "$@"
fi

# A smoke run has its own profile and stages one screenshot and a log per variant.
mkdir -p "$root/checks"
scratch=$(mktemp -d "$root/profiles/.check-$variant.XXXXXX")
xpid=
cleanup() {
    if [ -n "$xpid" ]; then kill "$xpid" 2>/dev/null || true; wait "$xpid" 2>/dev/null || true; fi
    rm -rf -- "$scratch"
}
trap cleanup EXIT
trap 'exit 130' INT TERM
if [ -z "${DISPLAY:-}" ]; then
    "$root/runtime/bin/Xvfb" -displayfd 3 -screen 0 1024x576x24 -nolisten tcp \
        3>"$scratch/display" >"$scratch/xserver.log" 2>&1 &
    xpid=$!
    tries=0
    while [ ! -s "$scratch/display" ]; do
        if ! kill -0 "$xpid" 2>/dev/null || [ "$tries" -ge 100 ]; then
            cat "$scratch/xserver.log" >&2; exit 1
        fi
        sleep 0.1
        tries=$((tries + 1))
    done
    DISPLAY=":$(cat "$scratch/display")"
    export DISPLAY
fi
export LIBGL_ALWAYS_SOFTWARE=${LIBGL_ALWAYS_SOFTWARE:-1}
export SDL_AUDIODRIVER=${SDL_AUDIODRIVER:-dummy}
if ! timeout 100 "$engine" -nexuiz -basedir "$root/editions/$variant" -userdir "$scratch/profile" \
    -window -width 1024 -height 576 +sv_public 0 +map q3dust2-jb-beta6 \
    +defer 4 "cmd join" +defer 8 screenshot +defer 10 quit "$@" \
    >"$root/checks/$variant-client.log" 2>&1; then
    tail -25 "$root/checks/$variant-client.log" >&2
    exit 1
fi
set -- "$scratch"/profile/data/screenshots/*.jpg
if [ ! -s "$1" ] || ! grep -Fq 'is playing now' "$root/checks/$variant-client.log"; then
    tail -25 "$root/checks/$variant-client.log" >&2
    exit 1
fi
cp -- "$1" "$root/checks/$variant-in-game.jpg"
printf 'Joined %s in Nexuiz. Screenshot: %s\n' "$variant" "$root/checks/$variant-in-game.jpg"
