"""Small original fixtures covering geometry hidden by triangle or file counts."""

import csv
from io import BytesIO
from pathlib import Path
import struct
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

import numpy as np

from scene_builder import Assets, Scene
from source_overlays import overlay_mesh
from source_world import DISP, INCH, Nav, SourceWorld, axes, source_transform


class GeometryTests(unittest.TestCase):
    def test_prop_transform_applies_scale_then_source_yaw_and_translation(self):
        mat = np.reshape(
            source_transform((10, 20, 30), (0, 90, 0), (2, 1, 1)), (4, 4), order="F"
        )
        local = [*axes([10, 0, 0]) * INCH, 1.0]
        np.testing.assert_allclose((mat @ local)[:3], axes([10, 40, 30]) * INCH)
        self.assertAlmostEqual(np.linalg.det(mat[:3, :3]), 2.0)

    def test_four_nav_corners_distinguish_overhead_surfaces_and_ramps(self):
        columns = [
            "mapName",
            "areaId",
            "areaName",
            "northWestX",
            "northWestY",
            "northWestZ",
            "southEastX",
            "southEastY",
            "southEastZ",
            "northEastZ",
            "southWestZ",
        ]
        with TemporaryDirectory() as temp:
            path = Path(temp) / "areas.csv"
            with path.open("w", newline="", encoding="utf8") as file:
                writer = csv.writer(file)
                writer.writerow(columns)
                writer.writerow(("test", 41, "Ramp", 10, 20, 0, 20, 40, 0, 12, 16))
            nav = Nav(path, "test")
            self.assertTrue(nav.nearby([[20, 20, 12], [10, 40, 16]], 0, 0.0001))
            self.assertTrue(nav.nearby([[15, 30, 7]], 0, 0.0001))
            self.assertFalse(nav.nearby([[15, 30, 27]], 0, 1))
            self.assertFalse(nav.nearby([[40, 30, 7]], 5, 50))

    def test_displacement_start_rotation_preserves_authored_height_and_uv(self):
        world = SourceWorld.__new__(SourceWorld)
        world.disps = np.zeros(1, dtype=DISP)
        world.disps[0]["power"] = 2
        world.dispverts = np.zeros((25, 5))
        world.dispverts[12, :4] = [0, 0, 1, 2.5]
        world.grids = {}
        quad = np.array([[0, 0, 0], [0, 4, 0], [4, 4, 0], [4, 0, 0.0]])
        for rotation in range(4):
            base = np.roll(quad, rotation, axis=0)
            pts, uv, indices = world.displacement({"disp": 0}, base, base[:, :2] / 4)
            np.testing.assert_allclose(pts[12], [2, 2, 2.5])
            np.testing.assert_allclose(uv, pts[:, :2] / 4)
            self.assertEqual(indices.shape, (32, 3))
            tris = pts[indices]
            self.assertAlmostEqual(
                np.abs(
                    np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])[:, 2]
                ).sum()
                / 2,
                16.0,
            )

    def test_overlay_preserves_uvs_winding_and_deformed_host_surface(self):
        record = bytearray(352)
        struct.pack_into("<ihHi", record, 0, 42, 17, 1, 9)
        # UV0 is bottom left. Valve encodes U in the unused Z values of the first three handles.
        struct.pack_into(
            "<22f",
            record,
            264,
            0,
            1,
            1,
            0,
            -0.5,
            -0.5,
            1,
            -0.5,
            0.5,
            0,
            0.5,
            0.5,
            0,
            0.5,
            -0.5,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
        )
        corners = np.array([[-4, -4, -4], [4, -4, 4], [4, 4, 4], [-4, 4, -4.0]])
        n = np.array([-1.0, 0, 1]) / np.sqrt(2.0)

        def source_face(face):
            self.assertEqual(face, 9)
            return (
                corners,
                np.tile(n, (4, 1)),
                None,
                np.array([[0, 1, 2], [0, 2, 3]]),
                "stone",
            )

        identity, ti, faces, order, (positions, normals, uv, tris) = overlay_mesh(
            record, source_face
        )
        self.assertEqual((identity, ti, faces, order), (42, 17, (9,), 0))
        source = positions - 0.08 * n
        np.testing.assert_allclose(source[:, 0], source[:, 2], atol=1.0e-7)
        np.testing.assert_allclose(uv[:, 0], source[:, 0] + 0.5, atol=1.0e-7)
        np.testing.assert_allclose(uv[:, 1], 0.5 - source[:, 1], atol=1.0e-7)
        np.testing.assert_allclose(normals, np.tile(n, (len(normals), 1)))
        verts = source[tris]
        crosses = np.cross(verts[:, 1] - verts[:, 0], verts[:, 2] - verts[:, 0])
        self.assertTrue(np.all(crosses @ n > 0.0))
        self.assertAlmostEqual(crosses[:, 2].sum() / 2, 1.0)


class MaterialTests(unittest.TestCase):
    def test_ground_slot_identity_pak_precedence_and_missing_asset_report(self):
        with (
            BytesIO() as backing,
            ZipFile(backing, "w") as pak,
            TemporaryDirectory() as tmp,
        ):
            pak.writestr(
                "materials/Wall.vmt",
                '"LightmappedGeneric" { "$basetexture" "map/stone" }',
            )
            disk = Path(tmp) / "materials"
            disk.mkdir()
            (disk / "wall.vmt").write_text(
                '"UnlitGeneric" { "$basetexture" "some/alternative" }'
            )
            assets = Assets(pak, [tmp])
            scene = Scene(assets, 512)
            first = scene.material("wall")
            second = scene.material("wall", ground=True)
            self.assertNotEqual(first, second)
            self.assertEqual(scene.material("WALL", ground=True), second)
            self.assertEqual(
                scene.g["materials"][first]["extras"]["sourceShader"],
                "lightmappedgeneric",
            )
            self.assertFalse(scene.g["materials"][first]["extras"]["yugaGround"])
            self.assertTrue(scene.g["materials"][second]["extras"]["yugaGround"])
            self.assertEqual(scene.texture_issues, {"map/stone": "unresolved VTF"})
            self.assertRaises(ValueError, assets.read, "../outside.vtf")


if __name__ == "__main__":
    unittest.main()
