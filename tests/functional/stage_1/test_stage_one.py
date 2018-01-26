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

    For a stage_1 -> stage_2 transition, the following happens:

    1) Pre-process 
        - No pre-processing actions for stage_1

    2) Cmd exec
        - _set_command()
        - run_command()

    3) Post-process 
        - mkv should be moved to 2_mix
        - the aac encoded stereo mix should be attached to it's associated files list
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
    shutil.copy(test_paths['stage_1']['good'], 'tests/processing/1_remux')


@pytest.yield_fixture(scope='class')
def get_mkv(request):
    """ Some sort of black magic fixture to provide an object to the entire test class """
    mkv_path = 'tests/processing/1_remux/Stage 1 Test Good.mkv'
    mkv = MKV(mkv_path, stages.STAGE_0)

    if request.cls is not None:
        request.cls.mkv = mkv

    # Set the sanitized name, since that will be used
    mkv.state.clean_name = 'Stage 1 Test Good'
    mkv.stage = stages.STAGE_1

    yield mkv


@pytest.mark.usefixtures('clean_artifacts', 'create_environment', 'get_mkv')
class TestGoldenPath:
    """ The MKV used in this test class has the following streams:
        Input #0, matroska,webm, from 'Stage 1 Test Good.mkv':
          Metadata:
            title           : Stage 1 Test Good
            creation_time   : 2017-05-29T06:23:24.000000Z
            ENCODER         : Lavf57.83.100
          Duration: 00:00:05.26, start: 0.000000, bitrate: 14703 kb/s

            Stream #0:0(eng): Video: h264 (High), yuv420p(progressive), 1920x1080 [SAR 1:1 DAR 16:9], 23.98 fps,
             23.98 tbr, 1k tbn, 47.95 tbc (default)
            Metadata:
              title           : h264 Remux
              DURATION        : 00:00:05.255000000

            Stream #0:1(eng): Audio: dts (DTS-HD MA), 48000 Hz, 7.1, s16p (default)
            Metadata:
              title           : DTS-HD MA 7.1
              DURATION        : 00:00:05.008000000


        Expected behavior:
            - MKV should complete each step of stage_1 with no errors and no user intervention
    """

    def test_pre_proc(self):
        """ Note: Currently there is no pre-processing for stage_1
            but I wanted to put this test in here to remind myself
            that I didn't forget to write it. """

        self.mkv.pre_process()

        pass

    def test_set_command(self):
        """ Is the generated command correct?

            Expected behavior:
                - Commands to transition from stage 1 -> stage 2 will be generated

            Expected values:
                - len(cmd_list)     -> 2
                - cmd_list[0]       -> matches expected
                - cmd_list[1]       -> matches expected
        """
        self.mkv._set_command()

        expected_0 = [
            'ffmpeg', '-hide_banner', '-i', 'tests\\processing\\1_remux\\Stage 1 Test Good.mkv',
            '-map', '0:a:0', '-f', 'wav', '-acodec', 'pcm_f32le', '-ac', '2', '-af',
            'pan=stereo:FL=FC+0.30*FL+0.30*BL:FR=FC+0.30*FR+0.30*BR', '-'
        ]

        expected_1 = [
            'qaac64', '--verbose', '--tvbr', '127', '--quality', '2', '--rate', 'keep', '--ignorelength',
            '--no-delay', '-', '-o', 'tests\\processing\\1_remux\\Stage 1 Test Good.m4a'
        ]

        assert len(self.mkv.cmd_list) == 2
        assert self.mkv.cmd_list[0] == expected_0
        assert self.mkv.cmd_list[1] == expected_1

    def test_execute(self):
        """ Command Execution for Stage_1

            Expected behavior:
                - Stereo mix is extracted and encoded

            Expected Outputs:
                - 1_remux/Stage 1 Test Good.m4a
        """
        out = pathlib.Path('tests/processing/1_remux/Stage 1 Test Good.m4a')
        self.mkv.run_commands()
        assert out.exists()

    def test_post_proc(self):
        """ Post-processing for stage_0

            Expected Behavior:
                - Stage 1 MKV and Stereo mix file will be moved to 2_mix
        """
        # Expected locations after post processing
        out_0 = pathlib.Path('tests/processing/2_mix/Stage 1 Test Good.mkv')
        out_1 = pathlib.Path('tests/processing/2_mix/Stage 1 Test Good.m4a')

        self.mkv.post_process()
        assert out_0.exists()
        assert out_1.exists()
        assert self.mkv.state.assoc_files['stereo_mix']
