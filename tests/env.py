# Define paths to our test containers
# Default should be used for any test not requiring a specific mkv
test_paths = {
    # Well formed container with 1 Video, 1 Audio, 1 Sub and global metadata
    'default': 'tests\mkvs\generic\Default Test.mkv',

    # Doesn't exist
    'not_exists': 'tests\mkvs\This is not the mkv you were looking for.mkv',

    # ####################### VIDEO TEST CONTAINERS #######################
    # Video stream specific containers
    'video': {
        # Well formed container with 2 Real Video, 1 Audio, 1 Sub and global metadata
        'mult_real': r'tests\mkvs\video\Multiple Real Video Streams.mkv',

        # Well formed container with 2 Real Video, 1 Audio, 1 Sub and global metadata
        'mult_fake': r'tests\mkvs\video\Multiple Fake Video Streams.mkv'
    },

    # ####################### AUDIO TEST CONTAINERS #######################
    # Audio stream specific containers
    'audio': {
        # 2 Audio | DTS-HD MA 7.1 (eng) | DTS-HD MA 5.1 (eng)
        'two': r'tests\mkvs\audio\Multiple Audio Streams.mkv'

    },

    # ####################### SUBTITLE TEST CONTAINERS ####################
    # Subtitle stream specific containers
    'subs': {
        # No subtitles
        'zero': 'tests\mkvs\subs\Zero Subs.mkv',

        # 1 sub | English
        'one-eng': 'tests\mkvs\subs\One Eng.mkv',

        # 1 sub | English (forced)
        'one-engf': 'tests\mkvs\subs\One Eng_f.mkv',

        # 1 sub | Dutch
        'one-dut': 'tests\mkvs\subs\One Dut.mkv',

        # 1 sub | Dutch
        'one-dutf': 'tests\mkvs\subs\One Dut_f.mkv',

        # 2 subs | English | English
        'two-engeng': 'tests\mkvs\subs\Two Eng Eng.mkv',

        # 2 subs | English | Dutch
        'two-engdut': 'tests\mkvs\subs\Two Eng Dut.mkv',

        # 2 subs | Dutch | Dutch
        'two-dutdut': 'tests\mkvs\subs\Two Dut Dut.mkv',

        # 2 subs | English | Dutch (forced)
        'two-engdutf': 'tests\mkvs\subs\Two Eng Dut_f.mkv',

        # 2 subs | English (forced) | Dutch
        'two-engfdut': 'tests\mkvs\subs\Two Eng_f Dut.mkv',

        # 2 subs | English (forced) | English
        'two-engfeng': 'tests\mkvs\subs\Two Eng_f Eng.mkv',

        # 2 subs | English | English (forced)
        'two-engengf': 'tests\mkvs\subs\Two Eng Eng_f.mkv',

        # 3 subs | English | English | English
        'three-engengeng': 'tests\mkvs\subs\Three Eng Eng Eng.mkv',

        # 3 subs | Dutch | Dutch | English (forced)
        'three-dutdutengf': 'tests\mkvs\subs\Three Dut Dut Eng_f.mkv',

        # 3 subs | English (forced) | English | English (forced)
        'three-engfengengf': 'tests\mkvs\subs\Three Eng_f Eng Eng_f.mkv'
    },

    # Container has 1 V, 1 A, 1 S, but the order is Subs, Audio, Video [SAV]
    'weird_order_SAV': 'tests\mkvs\Weird Stream Order 01.mkv',

    # Well formed container with 1 Video, 1 Sub and No Audio
    'no_audio': 'tests\mkvs\Missing Audio Stream.mkv',

    # Representative of something from usenet
    'stage_0_good': 'tests\mkvs\Test.Clip.Bluray.1080p.1956.mkv'
}

# Define a bunch of test "streams" for testing MKVStream class
# Most of these are pruned tremendously to keep the size manageable
# We can read some from an actual MKV if we need to but use this whenever possible to save IO time
test_streams = {
    'video': {

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

        # Two "streams". For testing the streams property only
        'default_two': [{
            'index': 0
            }, {
            'index': 1
        }]

    },
    'audio': {

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
    'subs': {

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
