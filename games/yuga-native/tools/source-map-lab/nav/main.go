// SPDX-License-Identifier: AGPL-3.0-or-later
// Export local CS:GO navigation areas and corner heights into the ground classifier.
package main

import (
	"bytes"
	"encoding/binary"
	"encoding/csv"
	"fmt"
	"io"
	"math"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"

	gonav "github.com/pnxenopoulos/csgonavparse"
)

func export(navName, bspName string, output io.Writer) error {
	file, err := os.Open(navName)
	if err != nil {
		return err
	}
	defer file.Close()
	stat, err := os.Stat(bspName)
	if err != nil {
		return err
	}
	if !stat.Mode().IsRegular() {
		return fmt.Errorf("expected regular BSP file")
	}
	var header [16]byte
	if _, err := io.ReadFull(file, header[:]); err != nil {
		return fmt.Errorf("reading NAV header: %w", err)
	}
	order := binary.LittleEndian
	major, minor := order.Uint32(header[4:8]), order.Uint32(header[8:12])
	if order.Uint32(header[:4]) != 0xfeedface || major != 16 || minor != 1 {
		return fmt.Errorf("expected CS:GO NAV 16.1, read magic %#x, version %d.%d", order.Uint32(header[:4]), major, minor)
	}
	bspSize := order.Uint32(header[12:])
	if int64(bspSize) != stat.Size() {
		return fmt.Errorf("recorded BSP size %d does not match supplied %d", bspSize, stat.Size())
	}
	input := gonav.Parser{Reader: io.MultiReader(bytes.NewReader(header[:]), file)}
	mesh, err := input.Parse()
	if err != nil {
		return err
	}
	if len(mesh.Areas) == 0 {
		return fmt.Errorf("input contains no areas")
	}

	columns := []string{"mapName", "areaId", "areaName", "northWestX", "northWestY", "northWestZ", "southEastX", "southEastY", "southEastZ", "northEastZ", "southWestZ"}
	out := csv.NewWriter(output)
	if err := out.Write(columns); err != nil {
		return err
	}
	keys := make([]uint32, 0, len(mesh.Areas))
	for id := range mesh.Areas {
		keys = append(keys, id)
	}
	sort.Slice(keys, func(i, j int) bool { return keys[i] < keys[j] })
	mapName := strings.TrimSuffix(filepath.Base(bspName), filepath.Ext(bspName))
	for _, id := range keys {
		area := mesh.Areas[id]
		label := ""
		if area.Place != nil {
			label = area.Place.Name
		}
		row := []string{mapName, strconv.FormatUint(uint64(id), 10), label}
		for _, v := range []float32{area.NorthWest.X, area.NorthWest.Y, area.NorthWest.Z, area.SouthEast.X, area.SouthEast.Y, area.SouthEast.Z, area.NorthEastZ, area.SouthWestZ} {
			value := float64(v)
			if math.IsNaN(value) || math.IsInf(value, 0) {
				return fmt.Errorf("area %d has nonfinite coordinate", id)
			}
			row = append(row, strconv.FormatFloat(value, 'f', -1, 32))
		}
		if err := out.Write(row); err != nil {
			return err
		}
	}
	out.Flush()
	if err := out.Error(); err != nil {
		return err
	}
	fmt.Fprintf(os.Stderr, "CS:GO NAV %d.%d: %d areas, %d named places, %d ladders, paired BSP %d bytes\n", mesh.MajorVersion, mesh.MinorVersion, len(mesh.Areas), len(mesh.Places), len(mesh.Ladders), mesh.BSPSize)
	return nil
}

func main() {
	if len(os.Args) != 3 {
		fmt.Fprintln(os.Stderr, "usage: nav map.nav map.bsp > areas.csv")
		os.Exit(2)
	}
	if err := export(os.Args[1], os.Args[2], os.Stdout); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
