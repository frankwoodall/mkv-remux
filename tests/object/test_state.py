import pathlib
import shutil

import pytest

from mkvremux import MKV
from mkvremux.state import State, stages
from tests.env import test_paths


@pytest.fixture(scope='class')
def clean_artifacts():
    """ In case a previous test failed. Remove any artifacts """
    paths = [
        pathlib.Path('tests/processing/_archive'),
        pathlib.Path('tests/processing/0_analyze'),
        pathlib.Path('tests/processing/1_remux'),
        pathlib.Path('tests/processing/2_mix'),
        pathlib.Path('tests/processing/3_review')
    ]

    for p in paths:
        for item in p.iterdir():
            item.unlink()


@pytest.fixture(scope='class')
def create_environment():
    """ Stage test files where they need to be """
    shutil.copy(test_paths['default'], 'tests/processing/0_analyze')


@pytest.yield_fixture(scope='class')
def get_mkv(request):
    """ Some sort of black magic fixture to provide an object to the entire test class """
    mkv_path = 'tests/processing/0_analyze/Default Test.mkv'
    mkv = MKV(mkv_path, stages.STAGE_0)

    if request.cls is not None:
        request.cls.mkv = mkv

    yield mkv


@pytest.mark.usefixtures('clean_artifacts', 'create_environment', 'get_mkv')
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
        orig = pathlib.Path('tests/processing/0_analyze/Default Test.mkv')
        cur_dir = pathlib.Path('tests/processing/0_analyze/')
        out_dir = pathlib.Path('tests/processing/1_remux/')
        state = self.mkv.state

        assert state.init_path == orig
        assert state.ext == '.mkv'
        assert state.cur_dir == cur_dir
        assert state.cur_fname == 'Default Test.mkv'
        assert state.out_dir == out_dir
        assert state.out_fname == 'Default Test.mkv'


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
        return MKV('tests/processing/1_remux/Stage 1 Test Good.mkv', stages.STAGE_0)

    def test_init(self, mkv0):
        """ Do all of the instance attributes relating to paths get set correctly?

            Test File:
                - 'tests/mkvs/stage_0/Stage 0 Test Good.mkv'

            Expected values:
                - init_path     -> 'tests/processing/0_analyze/Stage 0 Test Good.mkv'
                - cur_path      -> 'tests/processing/0_analyze/Stage 0 Test Good.mkv'
                - cur_dir       -> 'tests/processing/0_analyze'
                - out_dir       -> 'tests/processing/1_remux'
        """
        mkv = mkv0
        state = mkv.state
        assert state.init_path.as_posix() == 'tests/processing/0_analyze/Stage 0 Test Good.mkv'
        assert state.cur_path.as_posix() == 'tests/processing/0_analyze/Stage 0 Test Good.mkv'
        assert state.cur_dir.as_posix() == 'tests/processing/0_analyze'
        assert state.out_dir.as_posix() == 'tests/processing/1_remux'

    def test_stage0_to_stage1(self, mkv0):
        """ Do path attributes update correctly on stage transition?

            Test File:
                - 'tests/mkvs/stage_0/Stage 0 Test Good.mkv'

            Expected values:
                - init_path     -> 'tests/processing/0_analyze/Stage 0 Test Good.mkv'
                - cur_path      -> 'tests/processing/1_remux/Stage 0 Test Good.mkv'
                - cur_dir       -> 'tests/processing/1_remux'
                - out_dir       -> 'tests/processing/2_mix'
        """
        mkv = mkv0
        mkv.state.clean_name = 'Stage 0 Test Good'
        mkv.stage = stages.STAGE_1
        state = mkv.state

        assert state.init_path.as_posix() == 'tests/processing/0_analyze/Stage 0 Test Good.mkv'
        assert state.cur_path.as_posix() == 'tests/processing/1_remux/Stage 0 Test Good.mkv'
        assert state.cur_dir.as_posix() == 'tests/processing/1_remux'
        assert state.out_dir.as_posix() == 'tests/processing/2_mix'

    def test_stage1_to_stage2(self, mkv1):
        """ Do path attributes update correctly on stage transition?

            Test File:
                - 'tests/mkvs/stage_1/Stage 1 Test Good.mkv'

            Expected values:
                - init_path     -> 'tests/processing/1_remux/Stage 1 Test Good.mkv'
                - cur_path      -> 'tests/processing/2_mix/Stage 1 Test Good.mkv'
                - cur_dir       -> 'tests/processing/2_mix'
                - out_dir       -> 'tests/processing/3_review'
        """
        mkv = mkv1
        mkv.state.clean_name = 'Stage 1 Test Good'
        mkv.stage = stages.STAGE_1
        mkv.stage = stages.STAGE_2
        state = mkv.state
        assert state.init_path.as_posix() == 'tests/processing/1_remux/Stage 1 Test Good.mkv'
        assert state.cur_path.as_posix() == 'tests/processing/2_mix/Stage 1 Test Good.mkv'
        assert state.cur_dir.as_posix() == 'tests/processing/2_mix'
        assert state.out_dir.as_posix() == 'tests/processing/3_review'
