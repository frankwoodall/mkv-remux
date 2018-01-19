# Define paths to our test containers
# Default should be used for any test not requiring a specific mkv
test_paths = {
    # Well formed container with 1 Video, 1 Audio, 1 Sub and global metadata
    'default': 'tests\mkvs\generic\Default Test.mkv',

    # Doesn't exist
    'not_exists': 'tests\mkvs\This is not the mkv you were looking for.mkv',

    # ####################### VIDEO TEST CONTAINERS #######################
    # Video stream specific containers
    'Video': {
        # Well formed container with 2 Real Video, 1 Audio, 1 Sub and global metadata
        'mult_vid_real': r'tests\mkvs\video\Multiple Real Video Streams.mkv',

        # Well formed container with 2 Real Video, 1 Audio, 1 Sub and global metadata
        'mult_vid_fake': r'tests\mkvs\video\Multiple Fake Video Streams.mkv'
    },

    # ####################### AUDIO TEST CONTAINERS #######################
    # Audio stream specific containers
    'Audio': {
        # Well formed container with 1 Video, 2 Audio, and 1 sub
        'mult_audio': r'tests\mkvs\audio\Multiple Audio Streams.mkv'
    },

    # ####################### SUBTITLE TEST CONTAINERS ####################
    # Subtitle stream specific containers
    'Subs': {
        # No subtitles
        'subs_zero': 'tests\mkvs\subs\Zero Subs.mkv',

        # 1 English sub
        'one-eng': 'tests\mkvs\subs\One Eng.mkv',

        # 1 English forced sub
        'one-engf': 'tests\mkvs\subs\One Eng_f.mkv'
    },

    # Container has 1 V, 1 A, 1 S, but the order is Subs, Audio, Video [SAV]
    'weird_order_SAV': 'tests\mkvs\Weird Stream Order 01.mkv',

    # Well formed container with 1 Video, 1 Sub and No Audio
    'no_audio': 'tests\mkvs\Missing Audio Stream.mkv',

    # Representative of something from usenet
    'stage_0_good': 'tests\mkvs\Test.Clip.Bluray.1080p.1956.mkv'
}
