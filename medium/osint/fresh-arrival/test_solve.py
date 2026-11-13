#!/usr/bin/env python3
"""Unit test untuk solver Fresh Arrival (OSINT Medium)."""

import hashlib
import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("solve", HERE / "solve.py")
solve_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(solve_mod)

EXPECTED_FLAG = "NFX{XW_CXH_beijing_raihan}"

REQUIRED_ASSETS = [
    "spotted.jpg",
    "kemenhub_car_pk-adl.png",
    "jetphotos_pk-adl.png",
    "airframe_history_msn26854.png",
    "china_xinhua_airlines_info.png",
]


class TestFreshArrival(unittest.TestCase):
    def test_spotted_image_exists_and_hash(self):
        self.assertTrue(
            solve_mod.SPOTTED_IMAGE.is_file(),
            "Berkas assets/spotted.jpg harus tersedia.",
        )
        digest = hashlib.sha256(solve_mod.SPOTTED_IMAGE.read_bytes()).hexdigest()
        self.assertEqual(
            digest,
            solve_mod.EXPECTED_SHA256,
            "Hash SHA256 assets/spotted.jpg tidak cocok.",
        )

    def test_all_assets_exist(self):
        assets_dir = HERE / "assets"
        for asset_name in REQUIRED_ASSETS:
            asset_path = assets_dir / asset_name
            self.assertTrue(
                asset_path.is_file(),
                f"Berkas assets/{asset_name} harus tersedia.",
            )
            self.assertGreater(
                asset_path.stat().st_size,
                0,
                f"Berkas assets/{asset_name} tidak boleh kosong.",
            )

    def test_solve_reproduces_flag(self):
        flag = solve_mod.solve()
        self.assertEqual(flag, EXPECTED_FLAG, "Flag hasil rekonstruksi tidak cocok.")
        self.assertTrue(flag.startswith("NFX{"))
        self.assertTrue(flag.endswith("}"))


if __name__ == "__main__":
    unittest.main()
