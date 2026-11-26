# Export CS:GO navigation areas

This offline tool exports the four original corner heights and place name of every area in a legacy CS:GO `.nav` file. The floor classifier uses it alongside the corresponding BSP to distinguish stacked walkways and ramps. The navigation mesh covers bot-accessible surfaces. Geometry outside it still needs classification from the source geometry.

From this directory with Go 1.20 or later, supply the two files from the same game build.

```sh
go run . /path/to/csgo/maps/de_dust2.nav /path/to/csgo/maps/de_dust2.bsp > /tmp/official_nav.csv
```

The exporter checks the NAV magic, version 16.1 and the BSP byte length recorded in the header before parsing. For exact identity, verify both SHA-256 values against the source manifest. It writes Source-space coordinates ordered by numeric area ID. Empty place names remain empty. The four horizontal corners are aligned to the Source X/Y axes. North-east and south-west share X/Y coordinates with the other two corners and have independent Z values. The file basename determines the `mapName` column. [Source file identities](../../../docs/research/dust2-map-lab/source-evidence.json)

For the reference `de_dust2.bsp` of 325,735,952 bytes, the exporter found 1,118 areas, 26 named places, 74 individually unnamed areas and zero ladders. The CSV has SHA-256 `b9f7a1d5f764fbd461bba29fbe56c32243ff318d4113869b667d1f28f256aed3` on Linux. The exporter sends its summary to standard error so shell redirection yields clean CSV.

This standalone Go utility links the CS:GO-specific `csgonavparse` fork. Its upstream source notices and the wrapper use AGPL-3.0-or-later. The dependency is pinned by module version and Go checksums. [Upstream at the pinned revision](https://github.com/pnxenopoulos/csgonavparse/tree/354c86f749073e351a1e7d5474d9ef3ce9fedfc6) · [Module checksum](go.sum) · [License](LICENSE)
