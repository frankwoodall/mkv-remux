import pytest
from pathlib import Path
from mkvremux import MKV
from mkvremux.Location import Location
from tests.env import test_paths


class TestCreation:
    """ Test that Location objected is created and initialized correctly """

    def test_attributes(self):
        """ Are all of the instance attributes initialized correctly?

            Expected behavior:
                - Location object created successfully

            Expected values:
                - orig_path     -> Points to test_paths['default']
                - orig_fname    -> 'Default Test.mkv'
                - orig_name     -> 'Default Test'
                - ext           -> '.mkv'
                - cur_dir       -> Points to test_paths['default']
                - cur_fname     -> 'Default Test'
        """
        mkv = MKV(test_paths['default'], 0)
        loc = mkv.location

        assert loc.orig_path.samefile(Path(test_paths['default']))
        assert loc.orig_fname == 'Default Test.mkv'
        assert loc.orig_name == 'Default Test'
        assert loc.ext == '.mkv'
        assert loc.cur_dir.samefile(Path(test_paths['default']).parent)
        assert loc.cur_fname == 'Default Test.mkv'


class TestWrongTypes:
    """ Test that we fail appropriately when the wrong types are given to the constructor """

    def test_path(self):
        """ Do we fail if path is the wrong type?

            Expected behavior:
                - TypeError
                    - _path must be a pathlib.Path
        """
        with pytest.raises(TypeError) as exc:
            Location('Not a pathlib.path', 0)
        assert 'path must be pathlib.Path' in str(exc.value)

    def test_stage(self):
        """ Do we fail if stage is the wrong type?

            Expected behavior:
                - TypeError
                    - __stage must be an int
        """
        with pytest.raises(TypeError) as exc:
            Location(Path('.'), 'Not an int')
        assert 'stage must be an int' in str(exc.value)
