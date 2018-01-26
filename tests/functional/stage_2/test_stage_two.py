import pathlib
import shutil

import pytest

from mkvremux import MKV
from mkvremux.state import stages
from tests.env import test_paths

"""
For the sake of my time (and not writing tests for a living) this test coverage is incomplete. I'll add more tests
as I discover them and have free time.

    Current Coverage:
        - Golden path with a known good input

    TODO:
        - All raised exceptions 

    For a stage_2 -> stage_3 transition, the following happens:

    1) Pre-process 
        - set_metadata()
            - Retrieve metadata from the _resources/movie_details.json file

    2) Cmd exec
        - set_command()
        - run_command()
            - Mux in the stereo mix

    3) Post-process 
        - mkv should be moved to 3_review
        - the stereo mix should be removed from the associated files dict
        - the stereo mix should be deleted
"""


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
    shutil.copy(test_paths['stage_2']['good_mkv'], 'tests/processing/2_mix')
    shutil.copy(test_paths['stage_2']['good_m4a'], 'tests/processing/2_mix')


@pytest.yield_fixture(scope='class')
def get_mkv(request):
    """ Some sort of black magic fixture to provide an object to the entire test class """
    mkv_path = 'tests/processing/2_mix/Stage 2 Test Good.mkv'
    mkv = MKV(mkv_path, stages.STAGE_0)

    if request.cls is not None:
        request.cls.mkv = mkv

    # Note: during normal pipeline execution these values would have been
    # set in previous stages.
    mkv.state.sanitized_name = 'Stage 2 Test Good'
    mkv.state.assoc_files['stereo_mix'] = pathlib.Path('tests/processing/2_mix/Stage 2 Test Good.m4a')
    mkv.stage = stages.STAGE_2

    yield mkv


@pytest.mark.usefixtures('clean_artifacts', 'create_environment', 'get_mkv')
class TestGoldenPath:
    """ There are two files at this stage of the pipeline:
            - The mkv which has the chosen streams
            - The m4a stereo mix file

        Additionally, we rely on a third file to pull metadata:
            - resources/movie_details.json
                - This will be monkey patched in order to keep test data out of this file

        Expected behavior:
            - MKV should complete each step of stage_2 with no errors and no user intervention
    """

    def test_pre_proc(self, monkeypatch):
        """ Pre-processing for stage_2

            Expected Behavior:
                - MKV metadata retrieved successfully

            Expected values:
                - title     -> 'Stage 2 Test Good'
                - prov      -> 'Test'
                - source    -> 'Blu-ray'
                - desc      -> 'Test file for pipeline stage 2'
                - year      -> '1066'
                - imdb_id   -> 'tt0123456'
        """
        def _dork_metadata(mkv):
            mocked_metadata = {
                "title": "Stage 2 Test Good",
                "prov": "Test",
                "source": "Blu-ray",
                "desc": "Test file for pipeline stage 2",
                "year": "1066",
                "imdb_id": "tt0123456"
            }
            mkv.metadata = mocked_metadata

        monkeypatch.setattr(MKV, '_set_metadata', _dork_metadata)

        assert self.mkv.metadata is None
        self.mkv._set_metadata()
        assert self.mkv.metadata['title'] == 'Stage 2 Test Good'
        assert self.mkv.metadata['prov'] == 'Test'
        assert self.mkv.metadata['source'] == 'Blu-ray'
        assert self.mkv.metadata['desc'] == 'Test file for pipeline stage 2'
        assert self.mkv.metadata['year'] == '1066'
        assert self.mkv.metadata['imdb_id'] == 'tt0123456'

    def test_set_command(self):
        """ Is the command generated by pre_process correct?

            Expected behavior:
                - Command to transition from stage_2 -> stage_3 will be generated

            Expected values:
                - len(cmd_list)     -> 1
                - cmd_list[0]       -> matches expected
        """
        self.mkv._set_command()

        expected = [
            'ffmpeg', '-hide_banner', '-i', 'tests\\processing\\2_mix\\Stage 2 Test Good.mkv',
            '-i', 'tests\\processing\\2_mix\\Stage 2 Test Good.m4a',
            '-map', '0', '-map', '1', '-c', 'copy', '-map_metadata', '0',
            '-metadata', 'provenance=Test',
            '-metadata', 'source=Blu-ray',
            '-metadata', 'description=Test file for pipeline stage 2',
            '-metadata', 'rel_year=1066',
            '-metadata', 'imdb_id=tt0123456',
            '-metadata:s:a:1', 'language=eng', '-metadata:s:a:1', "title=Frank's Stereo Mix",
            '-metadata:s:a:1', 'encoder=qaac 2.63, CoreAudioToolbox 7.10.9.0, AAC-LC Encoder, TVBR q127, Quality 96',
            '-disposition:a:1', 'none', 'tests\\processing\\3_review\\Stage 2 Test Good (1066).mkv'
        ]

        assert len(self.mkv.cmd_list) == 1
        assert self.mkv.cmd_list[0] == expected

    def test_execute(self):
        """ Command Execution for Stage_2

            Expected behavior:
                - Stereo mix is muxed into the mkv container

            Expected Outputs:
                - 2_mix/Stage 2 Test Good (1066).mkv
        """

        final_mkv = self.mkv.state._root.joinpath('3_review', 'Stage 2 Test Good (1066).mkv')
        self.mkv.run_commands()
        assert final_mkv.exists()

    def test_post_proc(self):
        """ Post-processing for stage_0

            Expected Behavior:
                - 'stereo_mix' will be removed from the assoc_files dict
                - stage_2 files deleted
        """
        # Here's where the artifacts from stage_2 will be
        mkv_artifact = pathlib.Path('tests/processing/2_mix/Stage 2 Test Good.mkv')
        m4a_artifact = pathlib.Path('tests/processing/2_mix/Stage 2 Test Good.m4a')
        assert self.mkv.state.assoc_files.get('stereo_mix') is not None
        assert mkv_artifact.exists()
        assert m4a_artifact.exists()

        self.mkv.post_process()

        assert self.mkv.state.assoc_files.get('stereo_mix') is None
        assert mkv_artifact.exists() is False
        assert m4a_artifact.exists() is False