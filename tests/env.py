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
        'mult_vid_real': r'tests\mkvs\video\Multiple Real Video Streams.mkv',

        # Well formed container with 2 Real Video, 1 Audio, 1 Sub and global metadata
        'mult_vid_fake': r'tests\mkvs\video\Multiple Fake Video Streams.mkv'
    },

    # ####################### AUDIO TEST CONTAINERS #######################
    # Audio stream specific containers
    'audio': {
        # Well formed container with 1 Video, 2 Audio, and 1 sub
        'mult_audio': r'tests\mkvs\audio\Multiple Audio Streams.mkv'
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
