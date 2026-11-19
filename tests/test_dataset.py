import tempfile
import unittest
import zipfile
from pathlib import Path

from dataset import discover_bands, entry_directory, product_name
from download_and_organize import extract_archive, select_entries


PRODUCT = "PHISAT-2_L1_000001340_20241007034054_20241007034103_E04D392C"


class DatasetHelperTests(unittest.TestCase):
    def test_product_name_strips_zip_suffix(self):
        self.assertEqual(product_name(f"  {PRODUCT}.zip "), PRODUCT)

    def test_product_name_rejects_invalid_names(self):
        with self.assertRaises(ValueError):
            product_name("not-a-phisat-product")

    def test_entry_directory_rejects_path_escape(self):
        entry = {"category": "radiometry", "location": "RVUS", "session": "Session1",
                 "directory": "../outside"}
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                entry_directory(entry, Path(temporary))

    def test_discover_bands_finds_numbered_tiffs(self):
        entry = {"category": "radiometry", "location": "RVUS", "session": "Session1"}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "radiometry" / "RVUS" / "Session1"
            folder.mkdir(parents=True)
            for band in range(8):
                (folder / f"original_band_{band}.tiff").write_bytes(b"")

            bands = discover_bands(entry, root)

        self.assertEqual(set(bands), {f"b_{band}" for band in range(8)})


class DownloadSafetyTests(unittest.TestCase):
    def test_extract_archive_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "product.zip"
            with zipfile.ZipFile(archive, "w") as output:
                output.writestr("../escaped.txt", "must not be extracted")

            with self.assertRaises(ValueError):
                extract_archive(archive, root / "target")

            self.assertFalse((root / "escaped.txt").exists())


class SelectionTests(unittest.TestCase):
    def test_select_entries_applies_case_insensitive_filters(self):
        entry = {
            "category": "radiometry",
            "location": "RVUS",
            "session": "Session1",
            "metadata": {"session_id": PRODUCT},
        }
        documents = {"geometry": {"entries": []}, "image_quality": {"entries": []},
                     "radiometry": {"entries": [entry]}}

        selected = select_entries(documents, category="radiometry", location="rvus",
                                  session="session1", products=[f"{PRODUCT}.zip"])

        self.assertEqual(selected, [entry])


if __name__ == "__main__":
    unittest.main()
