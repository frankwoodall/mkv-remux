from unittest import TestCase
from pathlib import Path
from mkvremux import MKV
from tests.env import test_paths


class TestLocation(TestCase):
    """ Make sure that the location is getting populated correctly
        Stage specific location stuff is tested elsewhere."""

    @classmethod
    def setUpClass(cls):
        cls.mkv = MKV(test_paths.get('default'), 0)

    def test_orig_path(self):
        """ Is the original path set correctly? """
        should_be = Path('tests\mkvs\Default Test Clip.mkv')
        self.assertTrue(self.mkv.location.orig_path.samefile(should_be))

    def test_orig_fname(self):
        """ Is the original filename set correctly? """
        should_be = 'Default Test Clip.mkv'
        self.assertEqual(self.mkv.location.orig_fname, should_be)

    def test_orig_name(self):
        """ Is the original name set correctly? """
        should_be = 'Default Test Clip'
        self.assertEqual(self.mkv.location.orig_name, should_be)

    def test_ext(self):
        """ Is the extension set correctly? """
        should_be = '.mkv'
        self.assertEqual(self.mkv.location.ext, should_be)

    def test_cur_dir(self):
        """ Is the current path set correctly? """
        should_be = Path('tests\mkvs')
        self.assertTrue(self.mkv.location.cur_dir.samefile(should_be))

    def test_cur_fname(self):
        """ Is the current filename set correctly? """
        should_be = 'Default Test Clip.mkv'
        self.assertEqual(self.mkv.location.cur_fname, should_be)


class TestLocStage1(TestCase):
    """ Make sure that the location is getting populated correctly
        Stage specific location stuff is tested elsewhere."""

    def setUp(self):
        self.mkv = MKV(test_paths.get('default'), 1)

    def test_next_path(self):
        """ Does the next path get set correctly for stage 0? """
        should_be = Path(r'tests\2_needs_mux')
        self.assertTrue(self.mkv.location.next_path.samefile(should_be))

