import pytest
from mkvremux import MKV
from tests.env import test_paths


class TestMKVLoad:
    """ Ensure we can load an MKV container properly and we handle any errors as expected """

    def test_invalid_input(self):
        """ Do we handle invalid input? """
        with pytest.raises(TypeError) as exc:
            MKV(69, 0)
        assert "not <class 'int'>" in str(exc.value)

    def test_not_exists(self):
        """Do we raise an exception when given a path to a file that doesn't exist?"""
        with pytest.raises(FileNotFoundError) as exc:
            MKV('foo.bar', 0)
        assert str(exc.value) == 'Specified MKV does not exist'

    def test_load(self):
        """Can we load a generic mkv?"""
        m = MKV(test_paths.get('default'), 0)
        assert isinstance(m, MKV)


class TestMKVStageProperty:
    """ Ensure properties are being get/set properly """

    def test_stage_get(self):
        """ Does the stage getter return the correct value? """
        mkv = MKV(test_paths.get('default'), 0)
        assert mkv.stage == 0

    def test_stage_set(self):
        """ Does the stage setter work? """
        mkv = MKV(test_paths.get('default'), 0)
        mkv.stage = 1
        assert mkv.stage == 1

    def test_stage_set_loc(self):
        """ Does the stage setter properly set location's stage? """
        mkv = MKV(test_paths.get('default'), 0)
        assert mkv.location.stage == 0
        mkv.stage = 1
        assert mkv.location.stage == 1
