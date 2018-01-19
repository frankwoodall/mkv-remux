from unittest import TestCase
from mkvremux import MKV
from mkvremux.MKVStream import MKVStream
from tests.env import test_paths


# Analysis Function Testing Section
# Stream Extraction
class TestAnalysisStreamExtractionAllTypesOneStream(TestCase):
    """ Ensure that we're handling stage transitions properly """

    @classmethod
    def setUpClass(cls):
        """ Create and analyze an MKV with a single stream of each type """
        print('Setting up for TestAnalysisStreamExtraction')
        cls.mkv = MKV(test_paths.get('stage_0_good'), 0)
        cls.mkv.analyze()

    def test_extract_video(self):
        """ Do the video streams get extracted? """
        self.assertIsInstance(self.mkv.video, MKVStream)

    def test_extract_audio(self):
        """ Do the audio streams get extracted? """
        self.assertIsInstance(self.mkv.audio, MKVStream)

    def test_extract_subs(self):
        """ Do the subtitles streams get extracted? """
        self.assertIsInstance(self.mkv.subs, MKVStream)

    def test_vid_stream_count(self):
        """ Is the video stream count accurate? """
        self.assertEqual(self.mkv.video.stream_count, 1)

    def test_aud_stream_count(self):
        """ Is the audio stream count accurate? """
        self.assertEqual(self.mkv.audio.stream_count, 1)

    def test_sub_stream_count(self):
        """ Is the subtitles stream count accurate? """
        self.assertEqual(self.mkv.subs.stream_count, 1)
