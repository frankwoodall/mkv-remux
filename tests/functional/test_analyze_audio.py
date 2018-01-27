from mkvremux import MKV
from tests.env import test_paths


class TestOne:
    """ Tests for MKVs with a single audio stream """

    def test_one(self):
        """ The MKV used in this test has a single audio stream:
            Stream #0:1(eng): Audio: dts (DTS-HD MA), 48000 Hz, 5.1(side), s32p (24 bit) (default)
            Metadata:
              title           : DTS-HD MA 5.1
              BPS             : 3411810
              BPS-eng         : 3411810
              DURATION-eng    : 01:55:49.910000000
              NUMBER_OF_FRAMES: 651554
              NUMBER_OF_FRAMES-eng: 651554
              NUMBER_OF_BYTES : 2963972172
              NUMBER_OF_BYTES-eng: 2963972172
              _STATISTICS_WRITING_APP: mkvmerge v8.0.0 ('Til The Day That I Die') 64bit
              _STATISTICS_WRITING_APP-eng: mkvmerge v8.0.0 ('Til The Day That I Die') 64bit
              _STATISTICS_WRITING_DATE_UTC: 2015-09-25 12:17:01
              _STATISTICS_WRITING_DATE_UTC-eng: 2015-09-25 12:17:01
              _STATISTICS_TAGS: BPS DURATION NUMBER_OF_FRAMES NUMBER_OF_BYTES
              _STATISTICS_TAGS-eng: BPS DURATION NUMBER_OF_FRAMES NUMBER_OF_BYTES
              DURATION        : 00:00:01.428000000

            Expected behavior:
                - Audio stream will be identified
                - Audio stream will be selected for copying

            Expected values:
                - stream_count  -> 1
                - copy_count    -> 1
                - copy_indices  -> [1]
                - copy_streams[0]['tags']['title'] == 'DTS-HD MA 5.1'
        """

        mkv = MKV(test_paths['default'], 0)
        mkv._analyze()
        assert mkv.audio.stream_count == 1
        assert mkv.audio.copy_count == 1
        assert mkv.audio.copy_indices == [1]
        assert mkv.audio.copy_streams[0]['tags']['title'] == 'DTS-HD MA 5.1'


class TestMult:
    """ Tests for MKVs with multiple audio streams """

    def test_two_pick_1(self):
        """ The MKV used in this test has two audio streams:
            Stream #0:1(eng): Audio: dts, 48000 Hz, 8 channels (default)
            Metadata:
              title           : DTS-HD MA 7.1
              DURATION        : 00:00:00.000000000
            Stream #0:2(eng): Audio: dts, 48000 Hz, 6 channels (default)
            Metadata:
              title           : DTS-HD MA 5.1
              DURATION        : 00:00:00.000000000

            Expected behavior:
                - Multiple audio streams will be identified
                - User will be prompted for selection
                    - User enters "1"

            Expected values:
                - stream_count  -> 2
                - copy_count    -> 1
                - copy_indices  -> [1]
                - copy_streams[0]['tags']['title'] == 'DTS-HD MA 7.1'
        """
        mkv = MKV(test_paths['audio']['two'], 0)
        mkv._analyze()
        assert mkv.audio.stream_count == 2
        assert mkv.audio.copy_count == 0
        assert mkv.audio.copy_indices == []
        assert mkv.intervene['needed']
