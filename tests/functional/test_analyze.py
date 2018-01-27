import pathlib
import shutil

import pytest

from mkvremux import MKV
from mkvremux.mkvstream import MKVStream
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
    shutil.copy(test_paths['errors']['blank_global_title'], 'tests/processing/0_analyze')
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
    mkv.state.clean_name = 'Stage 2 Test Good'
    mkv.state.assoc_files['stereo_mix'] = pathlib.Path('tests/processing/2_mix/Stage 2 Test Good.m4a')
    mkv.stage = stages.STAGE_2

    yield mkv


class TestStreamExtraction:
    """ Test that streams are extracted properly """

    def test_known_good(self):
        """ The MKV used in this test case has a single Video, Audio, and Subtitle stream:
            Stream #0:0(eng): Video: h264 (High), yuv420p(tv, bt709, progressive), 1920x1080 [SAR 1:1 DAR 16:9],
             23.98 fps, 23.98 tbr, 1k tbn, 47.95 tbc (default)
            Metadata:
              title           : Default Test Video Stream
              BPS             : 25832121
            Stream #0:1(eng): Audio: dts (DTS-HD MA), 48000 Hz, 5.1(side), s32p (24 bit) (default)
            Metadata:
              title           : DTS-HD MA 5.1
              BPS             : 3411810
            Stream #0:2(eng): Subtitle: hdmv_pgs_subtitle, 1920x1080
            Metadata:
              title           : English Subtitles
              BPS             : 19313

            Expected behavior:
                - Video, Audio, and Subtitle streams will be identified

            Expected values:
                - .video     -> instanceof MKVStream
                - .video.stream_count   -> 1
                - .audio     -> instanceof MKVStream
                - .audio.stream_count   -> 1
                - .subs     -> instanceof MKVStream
                - .subs.stream_count   -> 1
        """
        mkv = MKV(test_paths['default'], stages.STAGE_0)
        mkv._analyze()

        assert isinstance(mkv.video, MKVStream)
        assert isinstance(mkv.audio, MKVStream)
        assert isinstance(mkv.subs, MKVStream)
        assert mkv.video.stream_count == 1
        assert mkv.audio.stream_count == 1
        assert mkv.subs.stream_count == 1


@pytest.mark.usefixtures('clean_artifacts')
class TestSetTitle:
    """ Setting the title is one of the first things that happens during processing and is extremely important.

        Ideally, the title will be accurate but that's not always the case. We need to handle the cases
        where the title is missing or wrong which, unfortunately, happens often.

        Test files here represent those situations
            - Blank Global Title.mkv        -> Global "title" tag exists but is blank
            - No Global Title.mkv           -> Global "title" tag doesn't exist at all

        Expected behavior:
            - MKV marked for intervention and user prompted for a title
    """

    def test_no_global_title(self, monkeypatch):
        def ask_for_title(the_mkv):
            title = input('What is the title of this movie: ')
            the_mkv.media_title = title

        def mock_title(_):
            return 'No Global Title'

        monkeypatch.setattr('builtins.input', mock_title)

        # Set up test
        shutil.copy(test_paths['errors']['no_global_title'], 'tests/processing/0_analyze')
        mkv_path = 'tests/processing/0_analyze/No Global Title.mkv'
        mkv = MKV(mkv_path, stages.STAGE_0)

        # Should fail here
        mkv.pre_process()
        assert mkv.intervene['needed']
        assert mkv.intervene['reason']['no_title']
        assert mkv.intervene['reason']['audio_stream'] is False
        assert mkv.intervene['reason']['video_stream'] is False
        assert mkv.intervene['reason']['subtitle_stream'] is False

        mkv.intervention('no_title', ask_for_title)

        assert mkv.media_title == 'No Global Title'

    def test_blank_global_title(self, monkeypatch):
        def ask_for_title(the_mkv):
            title = input('What is the title of this movie: ')
            the_mkv.media_title = title

        def mock_title(_):
            return 'Blank Global Title'

        monkeypatch.setattr('builtins.input', mock_title)

        # Set up test
        shutil.copy(test_paths['errors']['blank_global_title'], 'tests/processing/0_analyze')
        mkv_path = 'tests/processing/0_analyze/Blank Global Title.mkv'
        mkv = MKV(mkv_path, stages.STAGE_0)

        # Should fail here
        mkv.pre_process()
        assert mkv.intervene['needed']
        assert mkv.intervene['reason']['no_title']
        assert mkv.intervene['reason']['audio_stream'] is False
        assert mkv.intervene['reason']['video_stream'] is False
        assert mkv.intervene['reason']['subtitle_stream'] is False

        mkv.intervention('no_title', ask_for_title)

        assert mkv.media_title == 'Blank Global Title'




