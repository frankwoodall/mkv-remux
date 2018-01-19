from unittest import TestCase
from mkvremux import MKV
from tests.env import test_paths


class TestMKVLoad(TestCase):
    """ Ensure we can load an MKV container properly and we handle any errors as expected """

    def test_not_exists(self):
        """Do we raise an exception when given a path to a file that doesn't exist?"""
        with self.assertRaises(FileNotFoundError) as exc:
            MKV('foobar', 0)
        self.assertEqual(str(exc.exception), 'Specified MKV does not exist')

    def test_load(self):
        """Can we load a generic mkv?"""
        m = MKV(test_paths.get('default'), 0)
        self.assertIsInstance(m, MKV)


class TestMKVStageProperty(TestCase):
    """ Ensure properties are being get/set properly """

    def test_stage_get(self):
        """ Does the stage getter return the correct value? """
        mkv = MKV(test_paths.get('default'), 0)
        self.assertEqual(mkv.stage, 0)

    def test_stage_set(self):
        """ Does the stage setter return the correct value? """
        mkv = MKV(test_paths.get('default'), 0)
        mkv.stage = 1
        self.assertEqual(mkv.stage, 1)

    def test_stage_set_loc(self):
        """ Does the stage setter properly set location's stage? """
        mkv = MKV(test_paths.get('default'), 0)
        mkv.stage = 1
        self.assertEqual(mkv.location.stage, 1)
