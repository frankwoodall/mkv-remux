import os
import json
import pathlib
from pprint import pprint
from typing import Union
from mkvremux.state import stages
from subprocess import run, PIPE, DEVNULL
from mkvremux.state import State
from mkvremux.mkvstream import MKVStream

__author__ = 'Frank Woodall'
__project__ = 'mkvremux'


class MKV:
    """ A representation of the MKV container"""

    def __init__(self, _path: Union[str, bytes, os.PathLike, pathlib.Path], __stage: int):
        """ Constructor for MKV """
        if not isinstance(_path, pathlib.Path):
            _path = pathlib.Path(_path)
            if not _path.exists():
                raise FileNotFoundError('Specified MKV does not exist')

        self._stage = __stage
        self.state = State(_path, __stage)

        # Hold the various streams
        self.audio = None
        self.video = None
        self.subs = None

        # The media title
        self._title = None

        # Helpers. Hold the command used to process and the output dir
        self.cmd_list = []

        # Gets set to false if we fail hard somewhere
        self.can_transition = True

        # Gets set if we need user input for some reason. Try real hard to avoid.
        self.needs_user = False

        # Metadata
        self.metadata = None

    @property
    def media_title(self):
        return self._title

    @media_title.setter
    def media_title(self, new_title):
        """ Make sure we update the state output files accordingly """
        self._title = new_title
        self.state.sanitized_name = new_title.replace(':', '')

    @property
    def stage(self):
        return self._stage

    @stage.setter
    def stage(self, new_stage):
        """ Ensure we update the stage everywhere when we have a transition """
        self._stage = new_stage
        self.state.stage = new_stage

    def __repr__(self):
        r_str = ''
        r_str += 'Comprehensive dump of mkv object'
        r_str += '\nmkv.stage ({}): {}'.format(type(self._stage).__name__, repr(self._stage))
        return r_str

    def _analyze(self):
        """ When we have a downloaded file to process, we don't really know what's been done to it.

        The goal here is to extract the best video and audio tracks, as well as any forced English subs."""

        def extract_streams():
            """ Extract all the streams from the mkv """

            f = str(self.state.cur_path)

            # Extract streams and associated metadata for video, audio, and subtitle streams
            cmd_v = ['ffprobe', '-show_streams', '-select_streams', 'v', '-print_format', 'json', f]
            cmd_a = ['ffprobe', '-show_streams', '-select_streams', 'a', '-print_format', 'json', f]
            cmd_s = ['ffprobe', '-show_streams', '-select_streams', 's', '-print_format', 'json', f]

            commands = {
                'Video': cmd_v,
                'Audio': cmd_a,
                'Subtitles': cmd_s,
            }

            # Execute each command
            for kind, cmd in commands.items():
                ret = run(cmd, stdout=PIPE, stderr=DEVNULL)

                if ret.returncode != 0:
                    raise RuntimeError('Problem extracting stream: {}'.format(kind))

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

            # Attempt to use existing stream title
            self.video.title = self.video.copy_streams[0].get('title')
            if self.video.title is None:
                self.video.title = self.video.copy_streams[0].get('codec_name') + ' Remux'

        def choose_audio():
            """ Choose the preferred audio stream from the extracted streams """

            # Golden path first
            # Assume the first stream is the only (and therefore the preferred)
            # This is meant to be a list of one element
            self.audio.copy_streams.append(self.audio.streams[0])

            # Sanity Check
            if self.audio.stream_count == 0:
                raise RuntimeError('No audio streams found')
            elif self.audio.stream_count > 1:
                # User needs to look at it
                self.audio.needs_user = True
                self.needs_user = True

            if not self.audio.needs_user:
                # At this point, we've isolated a single audio stream
                index = self.audio.copy_streams[0].get('index')
                self.audio.copy_indices.append(index)

                # Set copy count. Again, I can't currently think of when
                # this would ever not be 1
                self.audio.copy_count = 1

                # Attempt to set stream title
                self.audio.title = self.audio.copy_streams[0]['tags'].get('title')
                if self.audio.title is None:
                    self.audio.title = self.audio.copy_streams[0].get('codec_name')
                    self.audio.title += ' ' + self.audio.copy_streams[0].get('channel_layout')

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

        def set_title():
            """ Attempt to set output filename based on mkv global tag 'title'.

            :raises RunTimeError: If the source mkv has no global title """

            f = str(self.state.cur_path)
            cmd = ['ffprobe', '-show_format', '-print_format', 'json', f]

            ret = run(cmd, stdout=PIPE, stderr=DEVNULL)

            if ret.returncode != 0:
                raise RuntimeError('Problem Extracting Global Format Data')

            format_data = json.loads(ret.stdout)
            tags = format_data['format']['tags']

            film_title = tags.get('title')
            if film_title is not None:
                self.media_title = film_title
            else:
                raise RuntimeError('MKV missing global title')

        def choose_preferred_streams():
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
        choose_preferred_streams()
        set_title()

    def _set_command(self):
        """ Responsible for setting the command(s) needed to process the mkv
            from it's current state into the next """

        def cmd_stage_0():
            """ Build the command for the stage_0 -> stage_1 transition """
            out_file = self.state.out_dir.joinpath(self.state.sanitized_name + self.state.ext)

            cmd_list = ['ffmpeg', '-hide_banner', '-i', '{}'.format(str(self.state.cur_path))]

            # Copy the chosen video stream. Should only be one at stage 0
            cmd_list += ['-map', '0:{}'.format(self.video.copy_indices[0])]

            # Copy the chosen audio stream. Should only be one at stage 0
            cmd_list += ['-map', '0:{}'.format(self.audio.copy_indices[0])]

            # Copy the chose subtitles
            if self.subs.copy_count > 0:
                for count, index in enumerate(self.subs.copy_indices):
                    cmd_list += ['-map', '0:{}'.format(index)]
                    # And set title (we know they're English Forced)
                    cmd_list += ['-metadata:s:s:{}'.format(count), '"title={}"'.format('English Forced')]

            # Include global metadata
            # TODO: Might want to add a cmd line option to NOT do this?
            cmd_list += ['-map_metadata', '0']

            # Set the global media title
            cmd_list += ['-metadata', 'title={}'.format(self.media_title)]

            # Set the stream titles
            cmd_list += ['-metadata:s:v:0', 'title={}'.format(self.video.title)]
            cmd_list += ['-metadata:s:a:0', 'title={}'.format(self.audio.title)]

            # Copy without transcoding
            cmd_list += ['-c', 'copy']

            cmd_list += ['{}'.format(str(out_file))]

            return cmd_list


        def cmd_stage_1():
            pass

        def cmd_stage_2():
            pass

        if self.stage == stages.STAGE_0:
            self.cmd_list.append(cmd_stage_0())

    def pre_process(self):
        if self.stage == stages.STAGE_0:
            self._analyze()

    def post_process(self):
        pass

    def run_commands(self):
        """ Run the commands to transition to the next stage. """

        self._set_command()
        for cmd in self.cmd_list:
            ret = run(cmd, stdout=PIPE, stderr=PIPE)

            print('Here is ret')
            print(ret)

            if ret.returncode != 0:
                raise RuntimeError('Issue executing commands for mkv', ret)

