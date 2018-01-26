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
    
    For a stage_0 -> stage_1 transition, the following happens:
    
    1) Pre-process 
        - _analyze()
        - possible intervention()
        
    2) Cmd exec
        - _set_command()
                
    3) Post-process 
        - No post-processing actions for stage_0
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
    shutil.copy(test_paths['stage_0']['good'], 'tests/processing/0_analyze')


@pytest.yield_fixture(scope='class')
def get_mkv(request):
    """ Some sort of black magic fixture to provide an object to the entire test class """
    mkv_path = 'tests/processing/0_analyze/Stage 0 Test Good.mkv'
    mkv = MKV(mkv_path, stages.STAGE_0)
    # noinspection PyProtectedMember
    mkv._analyze()

    if request.cls is not None:
        request.cls.mkv = mkv

    yield mkv


@pytest.mark.usefixtures('clean_artifacts', 'create_environment', 'get_mkv')
class TestGoldenPath:
    """ The MKV used in this test class has the following streams:
         Input #0, matroska,webm, from 'Stage 0 Test Good.mkv':
          Metadata:
            title           : Stage 0 Test Good
            creation_time   : 2017-05-29T06:23:24.000000Z
            ENCODER         : Lavf57.83.100
          Duration: 00:00:05.26, start: 0.000000, bitrate: 14704 kb/s

            Stream #0:0(eng): Video: h264 (High), yuv420p(progressive), 1920x1080 [SAR 1:1 DAR 16:9], 23.98 fps,
             23.98 tbr, 1k tbn, 47.95 tbc (default)
            Metadata:
              title           : h264 Remux
              DURATION        : 00:00:05.255000000

            Stream #0:1(eng): Audio: dts (DTS-HD MA), 48000 Hz, 7.1, s16p (default)
            Metadata:
              title           : DTS-HD MA 7.1
              DURATION        : 00:00:05.008000000

            Stream #0:2(eng): Subtitle: hdmv_pgs_subtitle (default)
            Metadata:
              title           : English-PGS
              DURATION        : 00:00:00.000000000


        Expected behavior:
            - MKV should complete each step of stage_0 with no errors and no user intervention
    """

    def test_pre_proc(self):
        """ Pre-processing for stage_0

            Expected Behavior:
                - MKV analyzed without error or user input
                - All attributes necessary for cmd exec step are collected

            Expected values:
                - video.copy_count      -> 1
                - video.copy_indices    -> [0]
                - audio.copy_count      -> 1
                - audio.copy_indices    -> [1]
                - subs.copy_count       -> 0
                - intervene             -> False
        """

        assert self.mkv.video.copy_count == 1
        assert self.mkv.video.copy_indices == [0]
        assert self.mkv.audio.copy_count == 1
        assert self.mkv.audio.copy_indices == [1]
        assert self.mkv.subs.copy_count == 0
        assert not self.mkv.intervene

    def test_set_command(self):
        """ Is the generated command correct?

            Expected behavior:
                - Command to transition from stage 0 -> stage 1 will be generated

            Expected values:
                - len(cmd_list)     -> 1
                - cmd_list[0]       -> matches expected
        """

        self.mkv._set_command()

        expected = [
            'ffmpeg', '-hide_banner', '-i', 'tests\\processing\\0_analyze\\Stage 0 Test Good.mkv',
            '-map', '0:0', '-map', '0:1', '-map_metadata', '0', '-metadata',
            'title=Stage 0 Test Good', '-metadata:s:v:0', 'title=h264 Remux',
            '-metadata:s:a:0', 'title=DTS-HD MA 7.1', '-c', 'copy',
            'tests\\processing\\1_remux\\Stage 0 Test Good.mkv'
        ]

        assert len(self.mkv.cmd_list) == 1
        assert self.mkv.cmd_list[0] == expected

    def test_execute(self):
        """ Command Execution for Stage_0

            Expected behavior:
                - Stage 1 MKV generated successfully
        """
        # This is where the output file should be
        out = self.mkv.state.out_dir.joinpath(self.mkv.state.sanitized_name + '.mkv')
        self.mkv.run_commands()
        assert out.exists()

    def test_post_proc(self):
        """ Post-processing for stage_0

            Expected Behavior:
                - Original MKV will be moved to _archive
        """
        # This is where the archived original should be
        orig = self.mkv.state._root.joinpath('_archive', self.mkv.state.orig_fname)
        self.mkv.post_process()
        assert orig.exists()
