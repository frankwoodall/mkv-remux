from unittest import TestCase
from unittest.mock import patch
from mkvremux import MKV
from tests.env import test_paths

class TestAnalysisAudioOneStream(TestCase):
    """ Test Audio Stream portion of MKV Analysis

        The MKV used in this test class has a single audio stream:
            0:1 -> Audio Stream

        Expected behavior:
            - Correct stream identified
            - Correct index extracted
            - Correct copy_count
    """

    @classmethod
    def setUpClass(cls):
        cls.mkv = MKV(test_paths['default'], 0)
        cls.mkv.analyze()

    def test_copy_count(self):
        """ Is the number of streams to copy correct? """
        self.assertEqual(self.mkv.audio.copy_count, 1)

    def test_copy_indices(self):
        """ Were the correct indices extracted? """
        self.assertEqual(self.mkv.audio.copy_indices, [1])

    def test_copy_streams(self):
        """ Was the correct stream identified? """
        self.assertEqual(self.mkv.audio.copy_streams[0]['tags']['title'], 'DTS-HD MA 5.1')


class TestAnalysisAudioMultStreams(TestCase):
    """ Test Audio Stream portion of MKV Analysis

        The MKV used in this test class has a two audio streams:
            0:1 -> Audio Stream (DTS-HD MA 7.1)
            0:2 -> Audio Stream (DTS-HD MA 5.1)
    """

    def test_good_input_1_copy_count(self):
        user_input = '1'
        mkv = MKV(test_paths['Audio']['mult_audio'], 0)
        with patch('builtins.input', side_effect=user_input):
            mkv.analyze()
        self.assertEqual(mkv.audio.copy_count, 1)

    def test_good_input_1_copy_indices(self):
        user_input = '1'
        mkv = MKV(test_paths['Audio']['mult_audio'], 0)
        with patch('builtins.input', side_effect=user_input):
            mkv.analyze()
        self.assertEqual(mkv.audio.copy_indices, [1])

    def test_good_input_1_copy_streams(self):
        user_input = '1'
        mkv = MKV(test_paths['Audio']['mult_audio'], 0)
        with patch('builtins.input', side_effect=user_input):
            mkv.analyze()
        self.assertEqual(mkv.audio.copy_streams[0]['tags']['title'], 'DTS-HD MA 7.1')

    def test_good_input_2_copy_count(self):
        user_input = '2'
        mkv = MKV(test_paths['Audio']['mult_audio'], 0)
        with patch('builtins.input', side_effect=user_input):
            mkv.analyze()
        self.assertEqual(mkv.audio.copy_count, 1)

    def test_good_input_2_copy_indices(self):
        user_input = '2'
        mkv = MKV(test_paths['Audio']['mult_audio'], 0)
        with patch('builtins.input', side_effect=user_input):
            mkv.analyze()
        self.assertEqual(mkv.audio.copy_indices, [2])

    def test_good_input_2_copy_streams(self):
        user_input = '2'
        mkv = MKV(test_paths['Audio']['mult_audio'], 0)
        with patch('builtins.input', side_effect=user_input):
            mkv.analyze()
        self.assertEqual(mkv.audio.copy_streams[0]['tags']['title'], 'DTS-HD MA 5.1')

