import pytest
from mkvremux import MKV
from tests.env import test_paths


class TestZero:
    """ Tests for MKVs with zero subtitle streams """

    def test_none(self):
        """ The MKV used in this test class does not have a subtitle stream.

            Expected behavior:
                - No subtitle streams identified
                - Nothing will be selected to copy

            Expected values:
                - stream_count  -> 0
                - copy_count    -> 0
                - copy_indices  -> []
                - copy_streams  -> []
        """
        mkv = MKV(test_paths['subs']['zero'], 0)
        mkv.analyze()
        assert mkv.subs.stream_count == 0
        assert mkv.subs.copy_count == 0
        assert mkv.subs.copy_indices == []
        assert mkv.subs.copy_streams == []


class TestOne:
    """ Tests for MKVs with a single subtitle stream """

    def test_eng(self):
        """ The MKV used in this test class has a single subtitle stream:
                Stream #0:2(eng): Subtitle: hdmv_pgs_subtitle
                Metadata:
                  title           : English-PGS
                  DURATION        : 00:00:00.000000000

            Expected behavior:
                - Subtitle stream will be identified
                - Nothing will be selected to copy since we only want forced subs

            Expected values:
                - stream_count  -> 1
                - copy_count    -> 0
                - copy_indices  -> []
                - copy_streams  -> []
        """
        mkv = MKV(test_paths['subs']['one-eng'], 0)
        mkv.analyze()
        assert mkv.subs.stream_count == 1
        assert mkv.subs.copy_count == 0
        assert mkv.subs.copy_indices == []
        assert mkv.subs.copy_streams == []

    def test_dut(self):
        """ The MKV used in this test class has a single subtitle stream:
                Stream #0:2(dut): Subtitle: subrip
                Metadata:
                  title           : Dutch-Retail Srt
                  DURATION        : 00:00:00.000000000

            Expected behavior:
                - Nothing will be selected to copy since we only want English subs

            Expected Values:
                - stream_count  -> 1
                - copy_count    -> 0
                - copy_indices  -> []
                - copy_streams  -> []
        """
        mkv = MKV(test_paths['subs']['one-dut'], 0)
        mkv.analyze()
        assert mkv.subs.stream_count == 1
        assert mkv.subs.copy_count == 0
        assert mkv.subs.copy_indices == []
        assert mkv.subs.copy_streams == []

    def test_dut_forced(self):
        """ The MKV used in this test class has a single subtitle stream:
                Stream #0:2(dut): Subtitle: subrip (forced)
                Metadata:
                  title           : Dutch Forced
                  DURATION        : 00:00:00.000000000

            Expected behavior:
                - Nothing will be selected to copy since we only want English subs

            Expected Values:
                - stream_count  -> 1
                - copy_count    -> 0
                - copy_indices  -> []
                - copy_streams  -> []
        """
        mkv = MKV(test_paths['subs']['one-dutf'], 0)
        mkv.analyze()
        assert mkv.subs.stream_count == 1
        assert mkv.subs.copy_count == 0
        assert mkv.subs.copy_indices == []
        assert mkv.subs.copy_streams == []

    def test_eng_forced(self):
        """ The MKV used in this test class has a single, forced subtitle stream:
                Stream #0:2(eng): Subtitle: hdmv_pgs_subtitle (forced)
                Metadata:
                  title           : English Forced
                  DURATION        : 00:00:00.000000000

            Expected behavior:
                - Subtitle stream will be identified
                - The forced English subtitle track will be selected for copying

            Expected values:
                - stream_count  -> 1
                - copy_count    -> 1
                - copy_indices  -> [2]
                - copy_streams[0]['tags']['title'] -> English Forced
        """
        mkv = MKV(test_paths['subs']['one-engf'], 0)
        mkv.analyze()
        assert mkv.subs.stream_count == 1
        assert mkv.subs.copy_count == 1
        assert mkv.subs.copy_indices == [2]
        assert mkv.subs.copy_streams[0]['tags']['title'] == 'English Forced'


class TestTwo:
    """ Tests for MKVs with two subtitle streams """

    def test_engeng(self):
        """ The MKV used in this test class has two subtitle stream:
                Stream #0:2(eng): Subtitle: hdmv_pgs_subtitle
                Metadata:
                  title           : English-PGS
                  DURATION        : 00:00:00.000000000
                Stream #0:3(eng): Subtitle: hdmv_pgs_subtitle
                Metadata:
                  title           : English-PGS
                  DURATION        : 00:00:00.000000000

            Expected behavior:
                - Subtitle stream will be identified
                - Nothing will be selected to copy since we only want forced subs

            Expected values:
                - stream_count  -> 2
                - copy_count    -> 0
                - copy_indices  -> []
                - copy_streams -> []
        """
        mkv = MKV(test_paths['subs']['two-engeng'], 0)
        mkv.analyze()
        assert mkv.subs.stream_count == 2
        assert mkv.subs.copy_count == 0
        assert mkv.subs.copy_indices == []
        assert mkv.subs.copy_streams == []

    def test_engdut(self):
        """ The MKV used in this test class has two subtitle stream:
                Stream #0:2(eng): Subtitle: hdmv_pgs_subtitle
                Metadata:
                  title           : English-PGS
                  DURATION        : 00:00:00.000000000
                Stream #0:3(dut): Subtitle: subrip
                Metadata:
                  title           : Dutch-Retail Srt
                  DURATION        : 00:00:00.000000000

            Expected behavior:
                - Subtitle stream will be identified
                - Nothing will be selected to copy since we only want English forced subs

            Expected values:
                - stream_count  -> 2
                - copy_count    -> 0
                - copy_indices  -> []
                - copy_streams -> []
        """
        mkv = MKV(test_paths['subs']['two-engdut'], 0)
        mkv.analyze()
        assert mkv.subs.stream_count == 2
        assert mkv.subs.copy_count == 0
        assert mkv.subs.copy_indices == []
        assert mkv.subs.copy_streams == []

    def test_dutdut(self):
        """ The MKV used in this test class has two subtitle stream:
                Stream #0:2(dut): Subtitle: subrip
                Metadata:
                  title           : Dutch-Retail Srt
                  DURATION        : 00:00:00.000000000
                Stream #0:3(dut): Subtitle: subrip
                Metadata:
                  title           : Dutch-Retail Srt
                  DURATION        : 00:00:00.000000000

            Expected behavior:
                - Subtitle stream will be identified
                - Nothing will be selected to copy since we only want English subs

            Expected values:
                - stream_count  -> 2
                - copy_count    -> 0
                - copy_indices  -> []
                - copy_streams -> []
        """
        mkv = MKV(test_paths['subs']['two-dutdut'], 0)
        mkv.analyze()
        assert mkv.subs.stream_count == 2
        assert mkv.subs.copy_count == 0
        assert mkv.subs.copy_indices == []
        assert mkv.subs.copy_streams == []

    def test_engdut_forced(self):
        """ The MKV used in this test class has two subtitle stream:
                Stream #0:2(eng): Subtitle: hdmv_pgs_subtitle
                Metadata:
                  title           : English-PGS
                  DURATION        : 00:00:00.000000000
                Stream #0:3(dut): Subtitle: subrip (forced)
                Metadata:
                  title           : Dutch Forced
                  DURATION        : 00:00:00.000000000

            Expected behavior:
                - Subtitle stream will be identified
                - Nothing will be selected to copy since we only want forced English subs

            Expected values:
                - stream_count  -> 2
                - copy_count    -> 0
                - copy_indices  -> []
                - copy_streams -> []
        """
        mkv = MKV(test_paths['subs']['two-engdutf'], 0)
        mkv.analyze()
        assert mkv.subs.stream_count == 2
        assert mkv.subs.copy_count == 0
        assert mkv.subs.copy_indices == []
        assert mkv.subs.copy_streams == []

    def test_eng_forced_dut(self):
        """ The MKV used in this test class has two subtitle stream:
                Stream #0:2(eng): Subtitle: hdmv_pgs_subtitle (forced)
                Metadata:
                  title           : English Forced
                  DURATION        : 00:00:00.000000000
                Stream #0:3(dut): Subtitle: subrip
                Metadata:
                  title           : Dutch-Retail Srt
                  DURATION        : 00:00:00.000000000

            Expected behavior:
                - Subtitle stream will be identified
                - The forced English stream will be selected

            Expected values:
                - stream_count  -> 2
                - copy_count    -> 1
                - copy_indices  -> [2]
                - copy_streams[0]['tags']['title'] -> English Forced
        """
        mkv = MKV(test_paths['subs']['two-engfdut'], 0)
        mkv.analyze()
        assert mkv.subs.stream_count == 2
        assert mkv.subs.copy_count == 1
        assert mkv.subs.copy_indices == [2]
        assert mkv.subs.copy_streams[0]['tags']['title'] == 'English Forced'

    def test_eng_forced_eng(self):
        """ The MKV used in this test class has two subtitle stream:
                Stream #0:2(eng): Subtitle: hdmv_pgs_subtitle (forced)
                Metadata:
                  title           : English Forced
                  DURATION        : 00:00:00.000000000
                Stream #0:3(eng): Subtitle: hdmv_pgs_subtitle
                Metadata:
                  title           : English-PGS
                  DURATION        : 00:00:00.000000000

            Expected behavior:
                - Subtitle stream will be identified
                - The forced English stream will be selected

            Expected values:
                - stream_count  -> 2
                - copy_count    -> 1
                - copy_indices  -> [2]
                - copy_streams[0]['tags']['title'] -> English Forced
        """
        mkv = MKV(test_paths['subs']['two-engfeng'], 0)
        mkv.analyze()
        assert mkv.subs.stream_count == 2
        assert mkv.subs.copy_count == 1
        assert mkv.subs.copy_indices == [2]
        assert mkv.subs.copy_streams[0]['tags']['title'] == 'English Forced'

    def test_engeng_forced(self):
        """ The MKV used in this test class has two subtitle stream:
                Stream #0:2(eng): Subtitle: hdmv_pgs_subtitle
                Metadata:
                  title           : English-PGS
                  DURATION        : 00:00:00.000000000
                Stream #0:3(eng): Subtitle: hdmv_pgs_subtitle (forced)
                Metadata:
                  title           : English Forced
                  DURATION        : 00:00:00.000000000

            Expected behavior:
                - Subtitle stream will be identified
                - The forced English stream will be selected

            Expected values:
                - stream_count  -> 2
                - copy_count    -> 1
                - copy_indices  -> [3]
                - copy_streams[0]['tags']['title'] -> English Forced
        """
        mkv = MKV(test_paths['subs']['two-engengf'], 0)
        mkv.analyze()
        assert mkv.subs.stream_count == 2
        assert mkv.subs.copy_count == 1
        assert mkv.subs.copy_indices == [3]
        assert mkv.subs.copy_streams[0]['tags']['title'] == 'English Forced'


class TestThree:
    """ Tests for MKVs with three subtitle streams """

    def test_engengeng(self):
        """ The MKV used in this test class has three subtitle streams:
                Stream #0:2(eng): Subtitle: hdmv_pgs_subtitle
                Metadata:
                  title           : English-PGS
                  DURATION        : 00:00:00.000000000
                Stream #0:3(eng): Subtitle: hdmv_pgs_subtitle
                Metadata:
                  title           : English-PGS
                  DURATION        : 00:00:00.000000000
                Stream #0:4(eng): Subtitle: hdmv_pgs_subtitle
                Metadata:
                  title           : English-PGS
                  DURATION        : 00:00:00.000000000

            Expected behavior:
                - Subtitle streams will be detected
                - Nothing will be selected to copy since we only want forced subs

            Expected values:
                - stream_count  -> 3
                - copy_count    -> 0
                - copy_indices  -> []
                - copy_streams  -> []
        """
        mkv = MKV(test_paths['subs']['three-engengeng'], 0)
        mkv.analyze()
        assert mkv.subs.stream_count == 3
        assert mkv.subs.copy_count == 0
        assert mkv.subs.copy_indices == []
        assert mkv.subs.copy_streams == []

    def test_dutduteng_forced(self):
        """ The MKV used in this test class has three subtitle streams:
                Stream #0:2(dut): Subtitle: subrip
                Metadata:
                  title           : Dutch-Retail Srt
                  DURATION        : 00:00:00.000000000
                Stream #0:3(dut): Subtitle: subrip
                Metadata:
                  title           : Dutch-Retail Srt
                  DURATION        : 00:00:00.000000000
                Stream #0:4(eng): Subtitle: hdmv_pgs_subtitle (forced)
                Metadata:
                  title           : English Forced
                  DURATION        : 00:00:00.000000000

            Expected behavior:
                - Subtitle streams will be detected
                - The forced English subtitle track will be selected for copying

            Expected values:
                - stream_count  -> 3
                - copy_count    -> 1
                - copy_indices  -> [4]
                - copy_streams[0]['tags']['title'] -> English Forced
        """
        mkv = MKV(test_paths['subs']['three-dutdutengf'], 0)
        mkv.analyze()
        assert mkv.subs.stream_count == 3
        assert mkv.subs.copy_count == 1
        assert mkv.subs.copy_indices == [4]
        assert mkv.subs.copy_streams[0]['tags']['title'] == 'English Forced'

    def test_eng_forced_engeng_forced(self):
        """ The MKV used in this test class has three subtitle streams:
                Stream #0:2(eng): Subtitle: hdmv_pgs_subtitle (forced)
                Metadata:
                  title           : English Forced
                  DURATION        : 00:00:00.000000000
                Stream #0:3(eng): Subtitle: hdmv_pgs_subtitle
                Metadata:
                  title           : English-PGS
                  DURATION        : 00:00:00.000000000
                Stream #0:4(eng): Subtitle: hdmv_pgs_subtitle (forced)
                Metadata:
                  title           : English Forced 2
                  DURATION        : 00:00:00.000000000

            Expected behavior:
                - Subtitle streams will be identified
                - RunTimeError
                    - Can't have multiple, forced english subs
                    - At least I don't think you can.
        """
        mkv = MKV(test_paths['subs']['three-engfengengf'], 0)
        with pytest.raises(RuntimeError) as exc:
            mkv.analyze()
        assert str(exc.value) == 'Multiple forced English subtitles found'
