class MKVStream:
    """ Represents all of the streams of a particular type in an mkv

        Instanced Attributes
        ====================

        kind            The type of stream (Audio, Video, Sub, or Global)
        streams         A list of the streams themselves
        stream_count    The number of streams of that type in this container
        metadata        The metadata attached to that stream
        indices         A list of indices of the streams that we want to keep
        title           Title of the preferred stream, if applicable

        :param _kind: A string representing the kind of stream (Video, Audio, Subtitles)"""

    def __init__(self, _kind):
        """ Constructor for MKVStream """

        # Validate the stream kind
        if _kind.lower() not in ['video', 'audio', 'subtitles']:
            raise RuntimeError('Unsupported stream kind: {}'.format(_kind.lower()))

        self.kind = _kind.lower()
        self._streams = []
        self.stream_count = 0

        # Information about the streams we want to keep
        self.copy_streams = []
        self.copy_count = 0
        self.copy_indices = []

        self.metadata = None
        self.title = None

        self.needs_user = False

    @property
    def streams(self):
        return self._streams

    @streams.setter
    def streams(self, val):
        """ Ensure we update stream_count whenever we set streams """
        self._streams = val
        self.stream_count = len(val)
