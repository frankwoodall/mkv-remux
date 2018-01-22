from mkvremux import MKV
from mkvremux.MKVStream import MKVStream
from tests.env import test_paths


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
        mkv = MKV(test_paths['default'], 0)
        mkv.analyze()

        assert isinstance(mkv.video, MKVStream)
        assert isinstance(mkv.audio, MKVStream)
        assert isinstance(mkv.subs, MKVStream)
        assert mkv.video.stream_count == 1
        assert mkv.audio.stream_count == 1
        assert mkv.subs.stream_count == 1
