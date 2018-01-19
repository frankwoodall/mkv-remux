from unittest import TestCase
from mkvremux import MKV
from tests.env import test_paths


class TestAnalysisSubsOneEng(TestCase):
    """ Test Audio Stream portion of MKV Analysis

        The MKV used in this test class has a single subtitle stream:
            Stream #0:2(eng): Subtitle: hdmv_pgs_subtitle
            Metadata:
              title           : English-PGS
              DURATION        : 00:00:00.000000000

        Expected behavior:
            - Nothing will be selected to copy since we only want forced subs
    """

    @classmethod
    def setUpClass(cls):
        cls.mkv = MKV(test_paths['Subs']['one-eng'], 0)
        cls.mkv.analyze()

    def test_copy_count(self):
        """ Is the number of streams to copy correct? """
        self.assertEqual(self.mkv.subs.copy_count, 0)

    def test_copy_indices(self):
        """ Were the correct indices extracted """
        self.assertEqual(self.mkv.subs.copy_indices, [])

    def test_copy_streams(self):
        """ Was the correct stream identified? """
        self.assertEqual(self.mkv.subs.copy_streams, [])


class TestAnalysisSubsOneEngForced(TestCase):
    """ Test Audio Stream portion of MKV Analysis

        The MKV used in this test class has a single, forced subtitle stream:
            Stream #0:2(eng): Subtitle: hdmv_pgs_subtitle (forced)
            Metadata:
              title           : English Forced
              DURATION        : 00:00:00.000000000

        Expected behavior:
            - The forced English subtitle track will be selected for copying
            - mkv.subs.copy_count   -> 1
            - mkv.subs.copy_indices -> [2]
            - mkv.subs.copy_streams[0]['tags']['title'] -> English Forced
    """

    @classmethod
    def setUpClass(cls):
        cls.mkv = MKV(test_paths['Subs']['one-engf'], 0)
        cls.mkv.analyze()

    def test_copy_count(self):
        """ Is the number of streams to copy correct? """
        self.assertEqual(self.mkv.subs.copy_count, 1)

    def test_copy_indices(self):
        """ Were the correct indices extracted """
        self.assertEqual(self.mkv.subs.copy_indices, [2])

    def test_copy_streams(self):
        """ Was the correct stream identified? """
        self.assertEqual(self.mkv.subs.copy_streams[0]['tags']['title'], 'English Forced')
