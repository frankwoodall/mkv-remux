#! python3

import os
import json
import pathlib
from pprint import pprint
from typing import Union
from subprocess import run, PIPE, DEVNULL
from mkvremux.Location import Location
from mkvremux.MKVStream import MKVStream

__author__ = 'Frank Woodall'
__project__ = 'mkvremux'


class MKV:
    """ A representation of the MKV container"""

    def __init__(self, _path: Union[str, bytes, os.PathLike, pathlib.Path], __stage: int):
        """ Constructor for MKV """
        self._allowed_types = [str, bytes, os.PathLike]

        if type(_path) not in self._allowed_types:
            raise TypeError('Expecting str, bytes, or os.PathLike, not {}'.format(type(_path)))

        if not isinstance(_path, pathlib.Path):
            _path = pathlib.Path(_path)
            if not _path.exists():
                raise FileNotFoundError('Specified MKV does not exist')

        self._stage = __stage
        self.location = Location(_path, __stage)

        # Hold the various streams
        self.audio = None
        self.video = None
        self.subs = None

        # Stream titles
        self.as_title = None
        self.vs_title = None
        self.g_title = None

        # Helpers. Hold the command used to process and the output dir
        self.cmd = None
        self.out_dir = None

        # Metadata
        self.metadata = None

    @property
    def stage(self):
        return self._stage

    @stage.setter
    def stage(self, new_stage):
        """ Ensure we update the stage everywhere when we have a transition """
        self._stage = new_stage
        self.location.stage = new_stage

    def __repr__(self):
        r_str = ''
        r_str += 'Comprehensive dump of mkv object'
        r_str += '\nmkv.stage ({}): {}'.format(type(self._stage).__name__, repr(self._stage))
        return r_str

    def analyze(self):
        """ When we have a downloaded file to process, we don't really know what's been done to it.

        The goal here is to extract the best video and audio tracks, as well as any forced English subs."""

        def extract_streams():
            """ Extract all the streams from the mkv """

            f = str(self.location.cur_path)

            # Extract streams and associated metadata for video, audio, and subtitle streams
            cmd_v = ['ffprobe', '-show_streams', '-select_streams', 'v', '-print_format', 'json', f]
            cmd_a = ['ffprobe', '-show_streams', '-select_streams', 'a', '-print_format', 'json', f]
            cmd_s = ['ffprobe', '-show_streams', '-select_streams', 's', '-print_format', 'json', f]

            commands = {
                'Video': cmd_v,
                'Audio': cmd_a,
                'Subtitles': cmd_s
            }

            # Execute each command
            for kind, cmd in commands.items():
                ret = run(cmd, stdout=PIPE, stderr=DEVNULL)

                if ret.returncode != 0:
                    raise RuntimeError('Problem extracting {} streams'.format(kind))

                # Convert the stream data to something useful
                s_data = json.loads(ret.stdout)

                # Create the object
                streams = MKVStream(kind)
                streams.streams = s_data['streams']

                # And assign it
                if kind == 'Video':
                    self.video = streams

                elif kind == 'Audio':
                    self.audio = streams

                elif kind == 'Subtitles':
                    self.subs = streams

        def choose_video():
            """ Choose the preferred video stream from the extracted streams """
            # Golden path first
            # Assume the first stream is the only (and therefore the preferred)
            # This is meant to be a list of one element
            self.video.copy_streams.append(self.video.streams[0])

            # But just to be sure, a few sanity checks
            # Zero is a problem
            if self.video.stream_count == 0:
                raise RuntimeError('No video streams found')
            # More than one might be a problem
            elif self.video.stream_count > 1:
                # Attached images come back as "Video" streams
                # Attempt to filter those out
                # NOTE: This is a _bad_ way to filter this list.
                #       The list of codec names is not complete. Will probably break as I find new ones
                #       Might be better to use the mimetype?
                non_image_streams = [x for x in self.video.streams if x.get('codec_name').lower() not in ['mjpeg']]

                # If we _still_ have multiple video streams
                if len(non_image_streams) != 1:
                    # Need to handle this file manually. Bail
                    raise RuntimeError('Multiple video streams detected')
                else:
                    # Otherwise, let's use the non-image stream we found
                    self.video.copy_streams = non_image_streams

            # If we made it here we have isolated a single video stream
            # Set the index number of the chosen stream
            index = self.video.copy_streams[0].get('index')
            self.video.copy_indices.append(index)

            # Set copy count. I can't think of a situation where this wouldn't be 1
            self.video.copy_count = 1

        def choose_audio():
            """ Choose the preferred audio stream from the extracted streams """

            # Golden path first
            # Assume the first stream is the only (and therefore the preferred)
            # This is meant to be a list of one element
            self.audio.copy_streams.append(self.audio.streams[0])

            # Sanity Check
            if self.audio.stream_count == 0:
                raise Exception('No audio streams found')
            elif self.audio.stream_count > 1:
                valid_indices = []      # We'll use this in a bit to validate user input
                # No good way to guess. We need to prompt.
                # First, print an overview of each audio stream.
                # This is generally the information I'd use to decided which stream I want to copy
                for stream in self.audio.streams:
                    # I don't want non-English language audio
                    if stream['tags']['language'] != 'eng':
                        continue
                    index = stream['index']
                    valid_indices.append(str(index))    # Record the index numbers for later validation
                    print('     [Stream #{}]'.format(str(index)))
                    print('       [Name]: ' + str(stream.get('tags').get('title')))
                    print('       [Codec]: ' + str(stream.get('codec_name')))
                    print('       [Channels]: ' + str(stream.get('channels')))
                    print('       [default]: ' + str(stream.get('disposition').get('default')))
                    print('       [Tags] ')

                    for key, val in stream['tags'].items():
                        print('         [{}] {}'.format(key, val))
                    print('\n\n')

                # Now ask which one of those we want
                choice = input('     [*] Enter number of desired stream or M for detailed stream info: ')

                # Safety loop
                while choice.lower() != 'm' and not choice.isdigit():
                    print('       [*] Invalid choice! ')
                    choice = input('     [*] Enter number of desired stream or M for detailed stream info: ')

                # If they asked for more details
                if choice.lower() == 'm':
                    for stream in self.audio.streams:
                        index = stream['index']
                        print('     [Stream #{}]'.format(str(index)))
                        pprint(stream)
                        print('\n\n')

                # Ensure the provided number is valid
                valid_choice = True if choice in valid_indices else False
                while not valid_choice:
                    print('       [*] You entered {}. That stream number does not exist!'.format(choice))
                    choice = input('     [*] Enter number of desired stream or M for detailed stream info: ')
                    valid_choice = True if choice in valid_indices else False

                # Add the stream to the copy_streams list
                for stream in self.audio.streams:
                    if str(stream['index']) == choice:
                        # Overwrite the other audio stream
                        self.audio.copy_streams = [stream]
                        break

            # At this point, we've isolated a single audio stream
            index = self.audio.copy_streams[0].get('index')
            self.audio.copy_indices.append(index)

            # Set copy count. Again, I can't currently think of when
            # this would ever not be 1
            self.audio.copy_count = 1

        def choose_subs():
            """ Choose the preffered subtitles stream from the extracted streams

                Preffered subtitles are in English and forced.

                :raises RunTimeError if more than 1 forced English subtitles found
            """
            if self.subs.stream_count > 0:
                # Filter out all non-eng subs
                eng_subs = [_ for _ in self.subs.streams if _.get('tags').get('language').lower() in ['eng', 'english']]

                for subs in eng_subs:
                    if subs.get('disposition').get('forced') == 1:
                        if self.subs.copy_count > 0:
                            raise RuntimeError('Multiple forced English subtitles found')

                        self.subs.copy_streams.append(subs)
                        self.subs.copy_indices.append(subs.get('index'))
                        self.subs.copy_count += 1


        def choose_preferred_stream():
            """ Choose the appropriate streams to copy from the original mkv.

            MKV containers are generally organized into streams. There are three main stream types
            that we care about: Video, Audio, and Subtitles.

            Each type is handled slightly differently, so this function wraps a "choose" function
            for each of the main types.

            In general though, the process for each "choose" function is the same:

                Given a list of all of the streams of one type:
                    1) Identify the number of streams
                    2) In the case of multiple streams, identify the stream(s) that we care about
                        This is stored as:
                            - preferred_streams         List of the streams to copy
                            - indices                   List of their indices in the container
                            - copy_count                Number of streams we plan on copying
                    3) Extra metadata associated with streams we care about


            :return:
            """
            choose_video()
            choose_audio()
            choose_subs()

        extract_streams()
        choose_preferred_stream()
