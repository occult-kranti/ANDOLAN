# Video and caption access check

On 25 November 2026 the team installed `yt-dlp` **2026.11.23** and `youtube-transcript-api` **1.2.5** into an isolated local virtual environment and tried public English captions. Both tools reached the cloud network's HTTP 403 restriction for YouTube. A Chromium visit to `youtubetranscript.com` returned “No transcript is available” for all eight IDs below. `withtranscript.ai` supplied titles but reported no cached transcript for those IDs. No video, caption or transcript was obtained or reviewed. These are observations of the services used on that date, not a claim that captions do not exist elsewhere.

| Public video | Metadata visible through the third-party page | Access result |
| --- | --- | --- |
| [AJdEqssNZ-U](https://www.youtube.com/watch?v=AJdEqssNZ-U) | Jan Willem Nijman, “The art of screenshake” | Direct 403; no cached transcript in the two tested services. |
| [Fy0aCDmgnxg](https://www.youtube.com/watch?v=Fy0aCDmgnxg) | “Juice it or lose it” | Same. |
| [LNidsMesxSE](https://www.youtube.com/watch?v=LNidsMesxSE) | “Animation Bootcamp: An Indie Approach to Procedural Animation” | Same. |
| [hG9SzQxaCm8](https://www.youtube.com/watch?v=hG9SzQxaCm8) | “Math for Game Programmers: Building a Better Jump” | Same. |
| [tDWtcyeNNew](https://www.youtube.com/watch?v=tDWtcyeNNew) | “Quantum breakthrough, Gemini 4 Argon, MOSS Image, KLING 4, OpenAI spy, Muse Wonder: AI NEWS” | Same. |
| [9W7QgI3pmT8](https://www.youtube.com/watch?v=9W7QgI3pmT8) | “AI Can Now Reverse Engineer Games” | Same. |
| [Pl7ThC4PiVA](https://www.youtube.com/watch?v=Pl7ThC4PiVA) | “How Games Are Decompiled: Reverse Engineering Byte by Byte” | Same. |
| [s9HMWYxwnOw](https://www.youtube.com/watch?v=s9HMWYxwnOw) | “Reverse Engineer Anything (REA) EXPLAINED!” | Same. |

Titles above are metadata displayed by the third-party transcript site. They do not establish the video's actual discussion, model claims or a usable transcript. Public code search for these IDs found links and related game-code references, not a verified caption file for these talks. The earlier [book and sample study](../../docs/research/gamecraft-sources-2026/README.md) remains separate evidence.

To retry on a computer with access to YouTube, use an isolated Python environment and the included pinned tool versions. This script requests English manual and automatic VTT captions without downloading the video. It returns a failure when the request fails or no VTT was saved. Review automatic captions against the source, and check rights before redistributing transcript text.

```sh
packet=games/yuga-native/art/agentic-cinematography-2026
python3 -m venv /tmp/yuga-video-tools
/tmp/yuga-video-tools/bin/pip install -r "$packet/video-tools-requirements.txt"
PATH="/tmp/yuga-video-tools/bin:$PATH" "$packet/fetch-captions.sh" /tmp/yuga-captions
```

Once text is actually available, record the title, date, source URL, caption type and relevant timestamps, then compare each transferable claim with the current game's code and a playable test. Until then, do not mark the videos as studied.
