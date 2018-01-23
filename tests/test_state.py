import pytest
import shutil
import pathlib
from mkvremux import MKV
from mkvremux.state import State
from mkvremux.state import stages
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
        state = mkv.state

        assert state.orig_path.samefile(pathlib.Path(test_paths['default']))
        assert state.orig_fname == 'Default Test.mkv'
        assert state.orig_name == 'Default Test'
        assert state.ext == '.mkv'
        assert state.cur_dir.samefile(pathlib.Path(test_paths['default']).parent)
        assert state.cur_fname == 'Default Test.mkv'


# noinspection PyTypeChecker
class TestWrongTypes:
    """ Test that we fail appropriately when the wrong types are given to the constructor """

    def test_path(self):
        """ Do we fail if path is the wrong type?

            Expected behavior:
                - TypeError
                    - _path must be a pathlib.Path
        """
        with pytest.raises(TypeError) as exc:
            State('Not a pathlib.path', 0)
        assert 'path must be pathlib.Path' in str(exc.value)

    def test_stage(self):
        """ Do we fail if stage is the wrong type?

            Expected behavior:
                - TypeError
                    - __stage must be an int
        """
        with pytest.raises(TypeError) as exc:
            State(pathlib.Path('.'), 'Not an int')
        assert 'stage must be an int' in str(exc.value)


class TestPaths:
    """ Test that the paths are extracted and updated correctly """

    @pytest.fixture(autouse=True)
    def clean_artifacts(self):
        """ In case a previous test failed. Remove any artifacts """
        paths = [
            pathlib.Path('tests/processing/0_analyze'),
            pathlib.Path('tests/processing/1_remux'),
            pathlib.Path('tests/processing/2_mix'),
            pathlib.Path('tests/processing/3_review')
        ]

        for p in paths:
            for item in p.iterdir():
                item.unlink()

    @pytest.fixture(autouse=True)
    def create_environment(self):
        """ Stage test files where they need to be """
        shutil.copy(test_paths['stage_0']['good'], 'tests/processing/0_analyze')
        shutil.copy(test_paths['stage_1']['good'], 'tests/processing/1_remux')

    @pytest.fixture
    def mkv0(self):
        return MKV('tests/processing/0_analyze/Stage 0 Test Good.mkv', stages.STAGE_0)

    @pytest.fixture
    def mkv1(self):
        return MKV('tests/processing/1_remux/Stage 1 Test Good.mkv', stages.STAGE_1)

    def test_init(self, mkv0):
        """ Do all of the instance attributes relating to paths get set correctly?

            Test File:
                - 'tests/mkvs/stage_0/Stage 0 Test Good.mkv'

            Expected values:
                - orig_path     -> 'tests/processing/0_analyze/Stage 0 Test Good.mkv'
                - orig_dir      -> 'tests/processing/0_analyze'
                - cur_path      -> 'tests/processing/0_analyze/Stage 0 Test Good.mkv'
                - cur_dir       -> 'tests/processing/0_analyze'
                - out_dir       -> 'tests/processing/1_remux'
        """
        mkv = mkv0
        state = mkv.state
        assert state.orig_path.as_posix() == 'tests/processing/0_analyze/Stage 0 Test Good.mkv'
        assert state.orig_dir.as_posix() == 'tests/processing/0_analyze'
        assert state.cur_path.as_posix() == 'tests/processing/0_analyze/Stage 0 Test Good.mkv'
        assert state.cur_dir.as_posix() == 'tests/processing/0_analyze'
        assert state.out_dir.as_posix() == 'tests/processing/1_remux'

    def test_stage0_to_stage1(self, mkv0):
        """ Do path attributes update correctly on stage transition?

            Test File:
                - 'tests/mkvs/stage_0/Stage 0 Test Good.mkv'

            Expected values:
                - orig_path     -> 'tests/processing/0_analyze/Stage 0 Test Good.mkv'
                - orig_dir      -> 'tests/processing/0_analyze'
                - cur_path      -> 'tests/processing/1_remux/Stage 0 Test Good.mkv'
                - cur_dir       -> 'tests/processing/1_remux'
                - out_dir       -> 'tests/processing/2_mix'
        """
        mkv = mkv0
        mkv.stage = 1
        state = mkv.state
        assert state.orig_path.as_posix() == 'tests/processing/0_analyze/Stage 0 Test Good.mkv'
        assert state.orig_dir.as_posix() == 'tests/processing/0_analyze'
        assert state.cur_path.as_posix() == 'tests/processing/1_remux/Stage 0 Test Good.mkv'
        assert state.cur_dir.as_posix() == 'tests/processing/1_remux'
        assert state.out_dir.as_posix() == 'tests/processing/2_mix'

    def test_stage1_to_stage2(self, mkv1):
        """ Do path attributes update correctly on stage transition?

            Test File:
                - 'tests/mkvs/stage_1/Stage 1 Test Good.mkv'

            Expected values:
                - orig_path     -> 'tests/processing/1_remux/Stage 1 Test Good.mkv'
                - orig_dir      -> 'tests/processing/1_remux'
                - cur_path      -> 'tests/processing/2_mix/Stage 1 Test Good.mkv'
                - cur_dir       -> 'tests/processing/2_mix'
                - out_dir       -> 'tests/processing/3_review'
        """
        mkv = mkv1
        mkv.stage = stages.STAGE_2
        state = mkv.state
        assert state.orig_path.as_posix() == 'tests/processing/1_remux/Stage 1 Test Good.mkv'
        assert state.orig_dir.as_posix() == 'tests/processing/1_remux'
        assert state.cur_path.as_posix() == 'tests/processing/2_mix/Stage 1 Test Good.mkv'
        assert state.cur_dir.as_posix() == 'tests/processing/2_mix'
        assert state.out_dir.as_posix() == 'tests/processing/3_review'


