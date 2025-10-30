import os
import tempfile
import unittest

from src.models import STATUSES, Shirt
from src.inventory_manager import add_shirt, update_status, delete_shirt, counts_by_status
from src.storage import save_shirts, load_shirts


class InventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.data_path = os.path.join(self.tmpdir.name, "shirts.json")
        self.shirts = []

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def test_add_and_persist(self):
        s = add_shirt(self.shirts, "Tee", "Blue", "M", STATUSES[0])
        self.assertEqual(s.id, 1)
        save_shirts(self.shirts, self.data_path)
        loaded = load_shirts(self.data_path)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].name, "Tee")

    def test_update_status(self):
        s = add_shirt(self.shirts, "Tank", "Red", "S", STATUSES[0])
        update_status(self.shirts, s.id, STATUSES[1])
        self.assertEqual(self.shirts[0].status, STATUSES[1])

    def test_delete(self):
        s1 = add_shirt(self.shirts, "A", "Black", "L", STATUSES[0])
        s2 = add_shirt(self.shirts, "B", "White", "M", STATUSES[2])
        delete_shirt(self.shirts, s1.id)
        self.assertEqual(len(self.shirts), 1)
        self.assertEqual(self.shirts[0].id, s2.id)

    def test_counts(self):
        add_shirt(self.shirts, "A", "Black", "L", STATUSES[0])
        add_shirt(self.shirts, "B", "White", "M", STATUSES[2])
        c = counts_by_status(self.shirts)
        self.assertEqual(c[STATUSES[0]], 1)
        self.assertEqual(c[STATUSES[2]], 1)


if __name__ == "__main__":
    unittest.main()


