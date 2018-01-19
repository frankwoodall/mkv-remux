
from unittest import TestCase
from mkvremux.MKVStream import MKVStream

# Define a bunch of test "streams"
# Most of these are pruned tremendously to keep the size manageable
# We can read some from an actual MKV if we need to but use this whenever possible to save IO time
test_streams = {
    'Video': {

        # A known good video stream that has all of the data I care about
        'default_single': [{
            'codec_long_name': 'H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10',
            'codec_name': 'h264',
            'codec_type': 'video',
            'coded_height': 1080,
            'coded_width': 1920,
            'display_aspect_ratio': '16:9',
            'disposition': {'attached_pic': 0, 'default': 1},
            'field_order': 'progressive',
            'height': 1080,
            'index': 0,
            'level': 41,
            'profile': 'High',
            'tags': {
                'BPS': '25832121',
                'DURATION': '01:55:49.860000000',
                'NUMBER_OF_BYTES': '22441203434',
                'language': 'eng',
                'title': 'h264 Remux'
            },
            'width': 1920
        }],
        'default_two': [{
            'index': 0
            }, {
            'index': 1
        }]

    },
    'Audio': {

        # A known good audio stream that has all of the data I care about
        'default_single': {
            'bits_per_raw_sample': '24',
            'channel_layout': '5.1(side)',
            'channels': 6,
            'codec_long_name': 'DCA (DTS Coherent Acoustics)',
            'codec_name': 'dts',
            'codec_type': 'audio',
            'disposition': {'default': 1},
            'index': 1,
            'profile': 'DTS-HD MA',
            'sample_fmt': 's32p',
            'sample_rate': '48000',
            'tags': {
                'BPS': '3411810',
                'DURATION': '01:55:49.910000000',
                'NUMBER_OF_BYTES': '2963972172',
                'language': 'eng',
                'title': 'DTS-HD MA 5.1'
            }
        }
    },
    'Subtitles': {

        # A known good subtitle stream that has all of the data I care about
        'default_single': {
            'codec_long_name': 'HDMV Presentation Graphic Stream subtitles',
            'codec_name': 'hdmv_pgs_subtitle',
            'codec_type': 'subtitle',
            'disposition': {'default': 0, 'forced': 0},
            'index': 4,
            'tags': {
                'BPS': '19313',
                'DURATION': '01:53:01.524000000',
                'NUMBER_OF_BYTES': '16371964',
                'language': 'eng',
                'title': 'English subs'
            },
        }
    }
}


class TestStreamCreation(TestCase):
    """ Test that each stream kind is created and identified correctly """

    def test_create_video_stream(self):
        """ Can we create a video stream? """
        s = MKVStream('Video')
        self.assertEqual(s.kind, 'video')

    def test_create_audio_stream(self):
        """ Can we create an audio stream? """
        s = MKVStream('Audio')
        self.assertEqual(s.kind, 'audio')

    def test_create_subtitle_stream(self):
        """ Can we create a subtitles stream? """
        s = MKVStream('Subtitles')
        self.assertEqual(s.kind, 'subtitles')

    def test_unsupported_kind(self):
        """ Do unsupported kinds fail expectedly? """
        with self.assertRaises(RuntimeError) as exc:
            MKVStream('foo')
        self.assertEqual(str(exc.exception), 'Unsupported stream kind: foo')


class TestStreamCountProperty(TestCase):
    """ Test that stream_count is updated whenever streams is set """

    def test_no_streams(self):
        """ Does an object with no streams have a count of 0? """
        s = MKVStream('Video')
        self.assertEqual(s.stream_count, 0)

    def test_set_one_stream(self):
        """ Does stream_count get updated? """
        s = MKVStream('Video')
        s.streams = test_streams['Video'].get('default_single')
        print('DEBUG INFORMATION')
        self.assertEqual(s.stream_count, 1)

    def test_set_two_stream(self):
        """ Does stream_count get updated? """
        s = MKVStream('Video')
        s.streams = test_streams['Video'].get('default_two')
        self.assertEqual(s.stream_count, 2)
