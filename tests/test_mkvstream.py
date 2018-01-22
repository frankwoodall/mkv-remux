import pytest
from mkvremux.MKVStream import MKVStream
from tests.env import test_streams


class TestCreation:
    """ Test that each stream type is created and identified correctly """

    def test_video(self):
        """ Can we create a 'Video' stream

            Expected behavior:
                - MKVStream object created successfully

            Expected values:
                - kind      -> video
        """
        stream = MKVStream('Video')
        assert stream.kind == 'video'

    def test_audio(self):
        """ Can we create an 'Audio' stream

            Expected behavior:
                - MKVStream object created successfully

            Expected values:
                - kind      -> audio
        """
        stream = MKVStream('Audio')
        assert stream.kind == 'audio'

    def test_subs(self):
        """ Can we create a 'Subtitles' stream

            Expected behavior:
                - MKVStream object created successfully

            Expected values:
                - kind      -> subtitles
        """
        stream = MKVStream('Subtitles')
        assert stream.kind == 'subtitles'

    def test_fake(self):
        """ Can we create a 'Foo' stream

            Expected behavior:
                - RunTimeError
                    - 'foo' is not a supported stream type
        """
        with pytest.raises(RuntimeError) as exc:
            MKVStream('foo')
        assert str(exc.value) == 'Unsupported stream kind: foo'


class TestStreamsProperty:
    """ Test that the 'streams' property of MKVStream is updating stream_count """

    def test_zero_streams(self):
        """ An object with no streams should report zero

            Expected behavior:
                - MKVStream object created successfully

            Expected values:
                - stream_count  -> 0
        """
        stream = MKVStream('Video')
        assert stream.stream_count == 0

    def test_one_stream(self):
        """ An object with one stream should report 1

            Expected behavior:
                - MKVStream object created successfully

            Expected values:
                - stream_count  -> 1
        """
        stream = MKVStream('Video')
        stream.streams = test_streams['video']['default_single']
        assert stream.stream_count == 1

    def test_two_stream(self):
        """ An object with two streams should report 2

            Expected behavior:
                - MKVStream object created successfully

            Expected values:
                - stream_count  -> 2
        """
        stream = MKVStream('Video')
        stream.streams = test_streams['video']['default_two']
        assert stream.stream_count == 2
