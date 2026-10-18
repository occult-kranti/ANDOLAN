YUGA's native offline preview now has a shared launch screen, clearer loading and retry states, consistent buttons and typography, saved controls and ability options, and updated lane HUD, map and result panels. Opening the overview holds combat and hero animation together; closing it resumes the same action.

Download and extract the ZIP for your operating system, then use its included launcher (`launch.sh` on Linux or `launch.bat` on Windows). Choose **Confluence** for local three-lane practice or **Bow training** for Rama's abilities. Help and Settings are available on the title screen. This is a desktop download, not an embedded ChatGPT or browser build.

Source: [`9e81a7c849837dea477ddb5a8c93f43665774573`](https://github.com/occult-kranti/ANDOLAN/tree/9e81a7c849837dea477ddb5a8c93f43665774573). [Native foundation CI passed](https://github.com/occult-kranti/ANDOLAN/actions/runs/39087210717). The two ZIPs are the exact locally qualified artifacts; SHA256SUMS.txt and both manifests accompany them.

Validation: 459 screen assertions, 741 visual/contract assertions, seeded loader stress, and actual Linux package launch, settings changes, same-save relaunch and Quit. Reviewers inspected the original captures. Result and respawn screens were exercised through an explicitly staged rule fixture. Two stale-coordinate input recoveries in the first capture run are documented; relaunch and staged runs needed none.

This remains an offline preview. The Deadlock-level visual target, full hero roster and native online matches are unfinished. Foot contact and motion transitions need further work, and compact HUD text is small. Linux execution used software Vulkan with Dummy audio; this does not establish hardware performance or listening quality. The Windows archive was verified but not executed.

[Build and next-agent handoff](https://github.com/occult-kranti/ANDOLAN/blob/game/yuga-native-production/games/yuga-native/docs/SCREEN_CAMPAIGN_HANDOFF.md) · [Roadmap](https://github.com/occult-kranti/ANDOLAN/blob/game/yuga-native-production/games/yuga-native/docs/ROADMAP_BACKLOG.json)
