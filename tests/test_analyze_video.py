import pytest
from mkvremux import MKV
from tests.env import test_paths


class TestOne:
    """ Tests for MKVs with one video stream """

    def test_one(self):
        """ The MKV used in this test has a single video stream:
                Stream #0:0(eng): Video: h264 (High), yuv420p(tv, bt709, progressive), 1920x1080 [SAR 1:1 DAR 16:9],
                    23.98 fps, 23.98 tbr, 1k tbn, 47.95 tbc (default)
                Metadata:
                  title           : Default Test Video Stream
                  BPS             : 25832121
                  BPS-eng         : 25832121
                  DURATION-eng    : 01:55:49.860000000
                  NUMBER_OF_FRAMES: 166630
                  NUMBER_OF_FRAMES-eng: 166630
                  NUMBER_OF_BYTES : 22441203434
                  NUMBER_OF_BYTES-eng: 22441203434
                  _STATISTICS_WRITING_APP: mkvmerge v8.0.0 ('Til The Day That I Die') 64bit
                  _STATISTICS_WRITING_APP-eng: mkvmerge v8.0.0 ('Til The Day That I Die') 64bit
                  _STATISTICS_WRITING_DATE_UTC: 2015-09-25 12:17:01
                  _STATISTICS_WRITING_DATE_UTC-eng: 2015-09-25 12:17:01
                  _STATISTICS_TAGS: BPS DURATION NUMBER_OF_FRAMES NUMBER_OF_BYTES
                  _STATISTICS_TAGS-eng: BPS DURATION NUMBER_OF_FRAMES NUMBER_OF_BYTES
                  DURATION        : 00:00:01.626000000

            Expected behavior:
                - Video stream will be identified
                - Video stream will be selected for copying

            Expected values:
                - stream_count  -> 1
                - copy_count    -> 1
                - copy_indices  -> [0]
                - copy_streams[0]['tags']['title'] == 'Default Test Video Stream'
        """

        mkv = MKV(test_paths['default'], 0)
        mkv.analyze()
        assert mkv.video.stream_count == 1
        assert mkv.video.copy_count == 1
        assert mkv.video.copy_indices == [0]
        assert mkv.video.copy_streams[0]['tags']['title'] == 'Default Test Video Stream'


class TestMultiple:
    """ Tests for MKVs with more than one video stream """

    def test_real(self):
        """ The MKV used in this test has two video streams:
                Stream #0:0(eng): Video: h264 (High), yuv420p(progressive), 1920x1080 [SAR 1:1 DAR 16:9], 23.98 fps,
                    23.98 tbr, 1k tbn, 47.95 tbc (default)
                Metadata:
                  title           : Real Video Stream 0
                  DURATION        : 00:00:00.250000000
                Stream #0:1(eng): Video: h264 (High), yuv420p(progressive), 1920x1080 [SAR 1:1 DAR 16:9], 23.98 fps,
                    23.98 tbr, 1k tbn, 47.95 tbc (default)
                Metadata:
                  title           : Real Video Stream 1
                  DURATION        : 00:00:00.250000000

            Expected behavior:
                - Video streams will be identified
                - RunTimeError
                    - I haven't seen this happen enough times to know how I want to handle it
        """
        mkv = MKV(test_paths['video']['mult_real'], 0)
        with pytest.raises(RuntimeError) as exc:
            mkv.analyze()
        assert str(exc.value) == 'Multiple video streams detected'

    def test_fake(self):
        """ The MKV used in this test has three video streams:
                Stream 0:0 is the 'real' video stream
                Streams 0:3 and 0:4 are images.

                Stream #0:0(eng): Video: h264 (High), yuv420p(progressive), 1920x1080 [SAR 1:1 DAR 16:9], 23.98 fps,
                    23.98 tbr, 1k tbn, 47.95 tbc (default)
                Metadata:
                  title           : Real Video Stream
                  DURATION        : 00:00:00.250000000
                Stream #0:1(eng): Audio: dts, 48000 Hz, 8 channels (default)
                Metadata:
                  title           : DTS-HD.MA.7.1
                  DURATION        : 00:00:00.000000000
                Stream #0:2(eng): Subtitle: hdmv_pgs_subtitle
                Metadata:
                  title           : English-PGS
                  DURATION        : 00:00:00.000000000
                Stream #0:3: Video: mjpeg, none(pc, bt470bg/unknown/unknown), 600x882, 1k fps, 1k tbr, 1k tbn, 1k tbc
                Metadata:
                  title           : Fake Video Stream 0
                  FILENAME        : cover.jpg
                  MIMETYPE        : image/jpeg
                  DURATION        : 00:00:00.000000000
                Stream #0:4: Video: mjpeg, none(pc, bt470bg/unknown/unknown), 1067x600, 1k fps, 1k tbr, 1k tbn, 1k tbc
                Metadata:
                  title           : Fake Video Stream 1
                  FILENAME        : cover_land.jpg
                  MIMETYPE        : image/jpeg
                  DURATION        : 00:00:00.000000000

            Expected behavior:
                - Video streams will be identified
                - Video stream 0:0 will be selected for copying
                - Video streams 0:3, 0:4 will be filtered out because they are images

            Expected values:
                - stream_count  -> 3
                - copy_count    -> 1
                - copy_indices  -> [0]
                - copy_streams[0]['tags']['title'] == 'Real Video Stream'
        """

        mkv = MKV(test_paths['video']['mult_fake'], 0)
        mkv.analyze()
        assert mkv.video.stream_count == 3
        assert mkv.video.copy_count == 1
        assert mkv.video.copy_indices == [0]
        assert mkv.video.copy_streams[0]['tags']['title'] == 'Real Video Stream'
