from unittest import TestCase
from mkvremux import MKV
from tests.env import test_paths

class TestAnalysisVideoOneStream(TestCase):
    """ Test Video Stream portion of MKV Analysis

        The MKV used in this test class has a single video stream
    """

    @classmethod
    def setUpClass(cls):
        import os
        print('Execution in: ' + str(os.getcwd()))
        cls.mkv = MKV(test_paths.get('default'), 0)
        cls.mkv.analyze()

    def test_copy_count(self):
        """ Is the number of streams to copy correct? """
        self.assertEqual(self.mkv.video.copy_count, 1)

    def test_copy_indices(self):
        """ Were the correct indices extracted """
        self.assertEqual(self.mkv.video.copy_indices, [0])

    def test_copy_streams(self):
        """ Was the correct stream identified? """
        self.assertEqual(self.mkv.video.copy_streams[0]['tags']['title'], 'h264 Remux')


class TestAnalysisVideoMultStreamsReal(TestCase):
    """ Test Video Stream portion of MKV Anlysis

        The MKV used in this test class has multiple video streams:
            0:0 -> Actual Video
            0:1 -> Actual Video

        Expected behavior: RuntimeError. I can't predict which video stream I'll want.
    """

    def test_mult_vid_streams(self):
        """ Do we raise the correct exception for multiple real video streams? """
        mkv = MKV(test_paths['Video']['mult_vid_real'], 0)
        with self.assertRaises(RuntimeError) as exc:
            mkv.analyze()
        self.assertEqual(str(exc.exception), 'Multiple video streams detected. Stopping processing')


class TestAnalysisVideoMultStreamsFake(TestCase):
    """ Test Video Stream portion of MKV Anlysis

        The MKV used in this test class has multiple video streams:
            0:0 -> Actual Video
            0:3 -> image
            0:4 -> image

        Expected behavior: Streams 0:3 and 0:4 will be ignored
    """

    @classmethod
    def setUpClass(cls):
        cls.mkv = MKV(test_paths['Video']['mult_vid_fake'], 0)
        cls.mkv.analyze()

    def test_copy_count(self):
        """ Is the number of streams to copy correct? """
        self.assertEqual(self.mkv.video.copy_count, 1)

    def test_copy_indices(self):
        """ Were the correct indices extracted """
        self.assertEqual(self.mkv.video.copy_indices, [0])

    def test_copy_streams(self):
        """ Was the correct stream identified? """
        self.assertEqual(self.mkv.video.copy_streams[0]['tags']['title'], 'h264 Remux')

