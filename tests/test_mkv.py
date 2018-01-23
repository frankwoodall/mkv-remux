import pytest
import shutil
import pathlib
from mkvremux import MKV
from tests.env import test_paths



class TestMKVLoad:
    """ Ensure we can load an MKV container properly and we handle any errors as expected """

    # noinspection PyTypeChecker
    def test_invalid_input(self):
        """ Do we handle invalid input? """
        with pytest.raises(TypeError) as exc:
            MKV(69, 0)
        assert "not int" in str(exc.value)

    def test_not_exists(self):
        """Do we raise an exception when given a path to a file that doesn't exist?"""
        with pytest.raises(FileNotFoundError) as exc:
            MKV('foo.bar', 0)
        assert str(exc.value) == 'Specified MKV does not exist'

    def test_load(self):
        """Can we load a generic mkv?"""
        m = MKV(test_paths['default'], 0)
        assert isinstance(m, MKV)


class TestMKVStageProperty:
    """ Ensure properties are being get/set properly """

    def test_stage_get(self):
        """ Does the stage getter return the correct value? """
        mkv = MKV(test_paths['default'], 0)
        assert mkv.stage == 0

    def test_stage_set(self):
        """ Does the stage setter work? """
        mkv = MKV(test_paths['default'], 0)
        mkv.stage = 1
        assert mkv.stage == 1

    def test_stage_set_loc(self):
        """ Does the stage setter properly set location's stage? """
        mkv = MKV(test_paths['default'], 0)
        assert mkv.state.stage == 0
        mkv.stage = 1
        assert mkv.state.stage == 1


class TestMediaTitleProperty:
    """ Tests various aspects of file name generation """

    def test_set_title(self):
        """ Does the set_title function work for a known good value? """
        mkv = MKV(test_paths['default'], 0)
        mkv._analyze()
        assert mkv.media_title == 'Default Test'
        assert mkv.state.sanitized_name == 'Default Test'

    def test_colon_in_title(self):
        """ Do we appropriately sanitize colons from file names? """
        mkv = MKV(test_paths['default'], 0)
        mkv.media_title = 'Title 2: Revenge of the Colon'
        assert mkv.media_title == 'Title 2: Revenge of the Colon'
        assert mkv.state.sanitized_name == 'Title 2 Revenge of the Colon'
