#!/usr/bin/env bash
# Public English caption attempt; this does not download the video itself.
set -u
if [ "$#" -ne 1 ]; then
  printf 'Usage: %s /path/to/output-directory\n' "$0" >&2
  exit 2
fi
if ! command -v yt-dlp >/dev/null 2>&1; then
  printf 'Install yt-dlp into your own virtual environment first.\n' >&2
  exit 1
fi
mkdir -p "$1"
failed=0
for id in AJdEqssNZ-U Fy0aCDmgnxg LNidsMesxSE hG9SzQxaCm8 \
          tDWtcyeNNew 9W7QgI3pmT8 Pl7ThC4PiVA s9HMWYxwnOw; do
  if ! yt-dlp --no-playlist --skip-download --write-subs --write-auto-subs \
      --sub-langs 'en.*' --sub-format vtt --socket-timeout 10 \
      --retries 0 --extractor-retries 0 -o "$1/%(id)s.%(ext)s" \
      "https://www.youtube.com/watch?v=$id"; then
    printf 'Caption request failed for %s\n' "$id" >&2
    failed=1
  elif ! compgen -G "$1/$id*.vtt" >/dev/null; then
    printf 'No English VTT captions were saved for %s\n' "$id" >&2
    failed=1
  fi
done
exit "$failed"
