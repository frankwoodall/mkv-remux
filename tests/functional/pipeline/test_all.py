import pathlib
import shutil

import pytest

from mkvremux import MKV
from mkvremux.state import stages
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
    shutil.copy(test_paths['stage_0']['good'], 'tests/processing/0_analyze')


@pytest.yield_fixture(scope='class')
def get_mkv(request):
    """ Some sort of black magic fixture to provide an object to the entire test class """
    mkv_path = 'tests/processing/0_analyze/Stage 0 Test Good.mkv'
    mkv = MKV(mkv_path, stages.STAGE_0)

    if request.cls is not None:
        request.cls.mkv = mkv

    yield mkv


@pytest.mark.usefixtures('clean_artifacts', 'create_environment', 'get_mkv')
class TestGoldenPath:
    """ A full pipeline test from beginning to end

        As closely as reasonable, this test class will mirror the driver implementation
    """

    def test_stage_0(self):
        """ Test stage_0

            Expected Behavior:
                - Complete pre-processing, command execution, and post-processing with no errors
                - mkv file will be renamed to orig_<name>
                - mkv file will be processed and desired streams flagged
                - Desired streams will be extracted into new mkv file
                - New mkv file moved to next stage
                - Original mkv file archived

            Expected Values:
                - intervene         -> False
                - can_transition    -> True

            Expected Outputs:
                - 'tests/processing/0_analyze/Stage 0 Test Good.mkv'
                - 'tests/processing/1_remux/Stage 0 Test Good.mkv'
                - 'tests/processing/_archive/orig_Stage 0 Test Good.mkv'
        """

        self.mkv.pre_process()
        orig = pathlib.Path('tests/processing/0_analyze/orig_Stage 0 Test Good.mkv')
        assert not self.mkv.intervene
        assert self.mkv.can_transition
        assert orig.exists()

        self.mkv.run_commands()
        out = pathlib.Path('tests/processing/0_analyze/Stage 0 Test Good.mkv')
        assert out.exists()

        self.mkv.post_process()
        moved = pathlib.Path('tests/processing/1_remux/Stage 0 Test Good.mkv')
        archived_orig = pathlib.Path('tests/processing/_archive/orig_Stage 0 Test Good.mkv')
        assert moved.exists()
        assert archived_orig.exists()

    def test_stage_1(self):
        """ Test stage_1

            Expected Behavior:
                - Complete pre-processing, command execution, and post-processing with no errors
                - mkv Audio stream will be downmixed into stereo
                - Stereo mix will be AAC encoded
                - Both files will be moved to stage_2

            Expected Values:
                - intervene         -> False
                - can_transition    -> True

            Expected Outputs:
                - 'tests/processing/1_remux/Stage 0 Test Good.mkv'
                - 'tests/processing/1_remux/Stage 0 Test Good.m4a'
                - 'tests/processing/2_mix/Stage 0 Test Good.mkv'
                - 'tests/processing/2_mix/Stage 0 Test Good.m4a'
        """
        self.mkv.pre_process()
        assert not self.mkv.intervene
        assert self.mkv.can_transition

        self.mkv.run_commands()
        out_0 = pathlib.Path('tests/processing/1_remux/Stage 0 Test Good.mkv')
        out_1 = pathlib.Path('tests/processing/1_remux/Stage 0 Test Good.m4a')
        assert out_0.exists()
        assert out_1.exists()

        self.mkv.post_process()
        moved_0 = pathlib.Path('tests/processing/2_mix/Stage 0 Test Good.mkv')
        moved_1 = pathlib.Path('tests/processing/2_mix/Stage 0 Test Good.m4a')
        assert moved_0.exists()
        assert moved_1.exists()

    def test_stage_2(self, monkeypatch):
        """ Test stage_2

            Expected Behavior:
                - Complete pre-processing, command execution, and post-processing with no errors
                - Retrieve metadata from movie_details.json
                - Stereo mix will be muxed into the mkv file
                - Stereo mix file will be deleted
                - mkv file will be moved to stage_3

            Expected Values:
                - intervene         -> False
                - can_transition    -> True
                - len(metadata)     -> 6
                - metadata['title'] -> 'Full Pipeline Test Good'

            Expected Outputs:
                - 'tests/processing/2_mix/Stage 0 Test Good.mkv'
                - 'tests/processing/3_review/Stage 0 Test Good.mkv'
        """
        def _dork_metadata(mkv):
            mocked_metadata = {
                "title": "Full Pipeline Test Good",
                "prov": "Test",
                "source": "Blu-ray",
                "desc": "Test file for full pipeline",
                "year": "1066",
                "imdb_id": "tt0123456"
            }
            mkv.metadata = mocked_metadata

        monkeypatch.setattr(MKV, '_set_metadata', _dork_metadata)
        assert self.mkv.metadata is None
        self.mkv.pre_process()
        assert not self.mkv.intervene
        assert self.mkv.can_transition
        assert len(self.mkv.metadata) == 6
        assert self.mkv.metadata['title'] == 'Full Pipeline Test Good'

        self.mkv.run_commands()
        out = pathlib.Path('tests/processing/2_mix/Full Pipeline Test Good (1066).mkv')
        assert out.exists()

        self.mkv.post_process()
        moved = pathlib.Path('tests/processing/3_review/Full Pipeline Test Good (1066).mkv')
        mkv_artifact = pathlib.Path('tests/processing/2_mix/Stage 0 Test Good.mkv')
        m4a_artifact = pathlib.Path('tests/processing/2_mix/Stage 0 Test Good.m4a')
        assert self.mkv.state.assoc_files.get('stereo_mix') is None
        assert moved.exists()
        assert mkv_artifact.exists() is False
        assert m4a_artifact.exists() is False

    def test_stage_3(self):
        pass
