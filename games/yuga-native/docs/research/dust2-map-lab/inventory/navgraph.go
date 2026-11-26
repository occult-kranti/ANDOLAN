// SPDX-License-Identifier: AGPL-3.0-or-later
// Read local Source NAV 16.1 with the map lab's pinned csgonavparse module.
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"sort"

	gonav "github.com/pnxenopoulos/csgonavparse"
)

type area struct {
	ID    uint32 `json:"id"`
	Place string `json:"place"`
	// NW x/y/z, SE x/y/z, NE z, SW z in local Source units.
	Bounds     [8]float32 `json:"bounds"`
	Flags      uint32     `json:"flags"`
	Neighbours []uint32   `json:"neighbours"`
	Hiding     int        `json:"hiding"`
	Encounters int        `json:"encounters"`
}

type census struct {
	Version  [2]uint32 `json:"version"`
	BSPBytes uint32    `json:"bsp_bytes"`
	Ladders  int       `json:"ladders"`
	Places   int       `json:"declared_places"`
	Areas    []area    `json:"areas"`
}

func run() error {
	if len(os.Args) != 2 {
		return fmt.Errorf("usage: navgraph path/to/de_dust2.nav")
	}
	f, err := os.Open(os.Args[1])
	if err != nil {
		return err
	}
	defer f.Close()
	reader := gonav.Parser{Reader: f}
	mesh, err := reader.Parse()
	if err != nil {
		return err
	}
	if mesh.MajorVersion != 16 || mesh.MinorVersion != 1 {
		return fmt.Errorf("expected a CS:GO 16.1 NAV")
	}
	r := census{Version: [2]uint32{mesh.MajorVersion, mesh.MinorVersion}, BSPBytes: mesh.BSPSize, Ladders: len(mesh.Ladders), Places: len(mesh.Places)}
	for _, a := range mesh.Areas {
		row := area{ID: a.ID, Flags: a.Flags, Hiding: len(a.HidingSpots), Encounters: len(a.EncounterPaths), Neighbours: []uint32{}, Bounds: [8]float32{a.NorthWest.X, a.NorthWest.Y, a.NorthWest.Z, a.SouthEast.X, a.SouthEast.Y, a.SouthEast.Z, a.NorthEastZ, a.SouthWestZ}}
		if a.Place != nil {
			row.Place = a.Place.Name
		}
		for _, c := range a.Connections {
			if c.TargetArea == nil {
				return fmt.Errorf("unresolved connection from %d to %d", a.ID, c.TargetAreaID)
			}
			row.Neighbours = append(row.Neighbours, c.TargetAreaID)
		}
		sort.Slice(row.Neighbours, func(i, j int) bool { return row.Neighbours[i] < row.Neighbours[j] })
		r.Areas = append(r.Areas, row)
	}
	sort.Slice(r.Areas, func(i, j int) bool { return r.Areas[i].ID < r.Areas[j].ID })
	return json.NewEncoder(os.Stdout).Encode(r)
}

func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
