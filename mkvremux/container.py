import os
import json
import shutil
import pathlib
from subprocess import run, PIPE, DEVNULL
from typing import Union

import regex

from mkvremux.mkvstream import MKVStream
from mkvremux.state import State, stages

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
        # Multiple items in this list will be piped into each other
        self.cmd_list = []

        # Gets set to false if we fail hard somewhere
        self.can_transition = True

        # Gets set if we need user input for some reason. Try real hard to avoid.
        self.intervene = {
            'needed': False,
            'reason': {
                'no_title': False,
                'audio_stream': False,
                'video_stream': False,
                'subtitle_stream': False
            }
        }

        # Metadata
        self.metadata = None

    @property
    def media_title(self):
        return self._title

    @media_title.setter
    def media_title(self, new_title):
        """ Make sure we update the state output files accordingly """
        # TODO: Might not be using this anymore
        self._title = new_title
        self.state.clean_name = new_title.replace(':', '')

    @property
    def stage(self):
        return self._stage

    @stage.setter
    def stage(self, new_stage):
        """ Ensure we update the stage everywhere when we have a transition """
        self._stage = new_stage
        self.state.stage = new_stage

    def _analyze(self):
        """ This is the heavy lifter of the pre-process step of any given stage. The analyze function
        has three main responsibilities:

            1) Extract all stream information (Video, Audio, and Subtitle) as well as global information about
                the container itself
            2) Given the stream information, select the preferred tracks.
            3) Attempt to determine titles for each chosen stream as well as the global media title.

        Preferred stream selection methodology is explained in the appropriate functions below.
        """

        def extract_streams():
            """ Extract all Video, Audio, and Subtitle streams with ffprobe """

            f = str(self.state.cur_path)
            cmd_v = ['ffprobe', '-show_streams', '-select_streams', 'v', '-print_format', 'json', f]
            cmd_a = ['ffprobe', '-show_streams', '-select_streams', 'a', '-print_format', 'json', f]
            cmd_s = ['ffprobe', '-show_streams', '-select_streams', 's', '-print_format', 'json', f]

            commands = {
                'Video': cmd_v,
                'Audio': cmd_a,
                'Subtitles': cmd_s,
            }

            for kind, cmd in commands.items():
                ret = run(cmd, stdout=PIPE, stderr=DEVNULL)

                if ret.returncode != 0:
                    raise RuntimeError('Problem extracting stream: {}'.format(kind))

                s_data = json.loads(ret.stdout)
                mkv_stream = MKVStream(kind)
                mkv_stream.streams = s_data['streams']

                if kind == 'Video':
                    self.video = mkv_stream

                elif kind == 'Audio':
                    self.audio = mkv_stream

                elif kind == 'Subtitles':
                    self.subs = mkv_stream

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
            """ Choose the preferred audio stream from the extracted streams

                Methodology:
                Assume that the first stream is the only (and therefore the preferred) stream.

                In the case of only a single audio stream, extract the relevant stream elements
                and we're done.

                In the case of no audio streams, RuntimeError.

                Finally, if there are multiple streams, mark the stream for user intervention
                and we'll have to prompt the user later.
            """

            self.audio.copy_streams.append(self.audio.streams[0])

            if self.audio.stream_count == 0:
                raise RuntimeError('No audio streams found')

            elif self.audio.stream_count > 1:
                self.intervene['needed'] = True
                self.intervene['reason']['audio_stream'] = True

            else:
                index = self.audio.copy_streams[0].get('index')
                self.audio.copy_indices.append(index)
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
            """ Attempt to set output filename based on mkv global tag 'title'. """

            f = str(self.state.cur_path)
            cmd = ['ffprobe', '-show_format', '-print_format', 'json', f]

            ret = run(cmd, stdout=PIPE, stderr=DEVNULL)

            if ret.returncode != 0:
                raise RuntimeError('Problem Extracting Global Format Data', ret)

            format_data = json.loads(ret.stdout)
            tags = format_data['format']['tags']

            film_title = tags.get('title')
            if film_title and len(film_title) > 0:
                self.media_title = film_title
            else:
                """ So at this point, we know the title is either blank, or not there at all.
                
                There are a few ways we can handle this:
                    1. Attempt to extract the title from the filename.
                     
                    This could work, but gets really messy really quickly. The problem with this approach 
                    is that there are an infinite number of naming conventions that would need to be 
                    handled as well as edge and corner cases that would break things. 
                    
                    Consider the following cases:
                        - lkjasdf8j23lfdkj23lkj23l2k3js908djlklj.mkv
                        - Bladerunner.2049.2017.1080p.mkv
                        
                    These would be tricky to say the least to figure out what's a name, what's a year, etc.
                    
                    2. Flag for user intervention and keep going.
                    
                    As a general rule I try really, really hard to avoid user input. The point of this is
                    supposed to be automation, after all. I guess at some point though the tradeoff between
                    "Hey, what is the title supposed to be?" and all of the messy code I would have to 
                    write to try to figure out the title from the filename (and still probably fail a lot)
                    isn't worth it.
                    
                    TL;DR - I'm not smart enough to implement this, so I'm just going to ask for the answer.                 
                """
                self.intervene['needed'] = True
                self.intervene['reason']['no_title'] = True

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
            commands = []
            in_file = self.state.cur_dir.joinpath(self.state.cur_fname)
            out_file = self.state.cur_dir.joinpath(self.state.out_fname)

            cmd_list = ['ffmpeg', '-hide_banner', '-i', str(in_file)]

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
            cmd_list += ['-map_metadata', '0']

            # Set the global media title
            cmd_list += ['-metadata', 'title={}'.format(self.media_title)]

            # Set the stream titles
            cmd_list += ['-metadata:s:v:0', 'title={}'.format(self.video.title)]
            cmd_list += ['-metadata:s:a:0', 'title={}'.format(self.audio.title)]

            # Copy without transcoding
            cmd_list += ['-c', 'copy']

            cmd_list += [str(out_file)]
            commands.append(cmd_list)

            return commands

        def cmd_stage_1():
            """ Build the commands for the stage_1 -> stage_2 transition

                1st command: Create a raw stereo mix
                2nd command: AAC encode it """

            commands = []
            in_file = self.state.cur_path
            out_file = self.state.assoc_files['stereo_mix']

            cmd_list = ['ffmpeg', '-hide_banner', '-i', str(in_file)]

            # Extract the audio stream
            cmd_list += ['-map', '0:a:0']

            # Set the output type, codec, and number of channels
            cmd_list += ['-f', 'wav', '-acodec', 'pcm_f32le', '-ac', '2']

            # Set the filter
            cmd_list += ['-af', 'pan=stereo:FL=FC+0.30*FL+0.30*BL:FR=FC+0.30*FR+0.30*BR']

            # Output to stdout
            cmd_list += ['-']
            commands.append(cmd_list)

            # And pipe to qaac
            cmd_list = ['qaac64', '--verbose']

            # qaac args
            cmd_list += ['--tvbr', '127', '--quality', '2', '--rate', 'keep', '--ignorelength', '--no-delay']

            # qaac read from stdin
            cmd_list += ['-']

            # And set output file
            cmd_list += ['-o', str(out_file)]
            commands.append(cmd_list)

            return commands

        def cmd_stage_2():
            """ Build the commands for the stage_2 -> stage_3 transition

                command: Mux in stereo mix and set all global and stream metadata """
            commands = []
            in_file = self.state.cur_path
            stereo_mix = self.state.assoc_files['stereo_mix']
            out_name = '{} ({}){}'.format(self.metadata['title'], self.metadata['year'], self.state.ext)
            out_file = self.state.cur_dir.joinpath(out_name)

            cmd_list = ['ffmpeg', '-hide_banner', '-i', str(in_file)]

            # Second input of stereo mix
            cmd_list += ['-i', str(stereo_mix)]

            # Extract all streams from both inputs. Direct copy
            cmd_list += ['-map', '0', '-map', '1', '-c', 'copy']

            # Copy global metadata
            cmd_list += ['-map_metadata', '0']

            # Set new global metadata
            cmd_list += ['-metadata', 'provenance={}'.format(self.metadata.get('prov'))]
            cmd_list += ['-metadata', 'source={}'.format(self.metadata.get('source'))]
            cmd_list += ['-metadata', 'description={}'.format(self.metadata.get('desc'))]
            cmd_list += ['-metadata', 'rel_year={}'.format(self.metadata.get('year'))]
            cmd_list += ['-metadata', 'imdb_id={}'.format(self.metadata.get('imdb_id'))]

            # Set stream metadata for stereo mix
            cmd_list += ['-metadata:s:a:1', 'language=eng']
            cmd_list += ['-metadata:s:a:1', "title=Frank's Stereo Mix"]
            cmd_list += [
                '-metadata:s:a:1', 'encoder=qaac 2.63, CoreAudioToolbox 7.10.9.0, AAC-LC Encoder, TVBR q127, Quality 96'
            ]

            # Set stereo mix to _not_  be default audio
            cmd_list += ['-disposition:a:1', 'none']

            # And set the output file
            cmd_list += [str(out_file)]
            commands.append(cmd_list)
            return commands

        # Ensure no other commands are present
        self.cmd_list = []

        # TODO: This is kind of ugly
        if self.stage == stages.STAGE_0:
            for cmd in cmd_stage_0():
                self.cmd_list.append(cmd)

        elif self.stage == stages.STAGE_1:
            for cmd in cmd_stage_1():
                self.cmd_list.append(cmd)

        elif self.stage == stages.STAGE_2:
            for cmd in cmd_stage_2():
                self.cmd_list.append(cmd)

    def intervention(self, reason, handler):
        """ Perform user intervention using supplied handler function """

        if handler(self):
            self.intervene['reason'][reason] = False

        # Note: I know this looks kind of janky.
        # In this case there was no title set during analysis and as a result, the state is using the original
        # filename as the output file. We _have_ a title now, so we have to force the update of the output filename
        if reason == 'no_title':
            self.state.out_dir = self.state.out_dir

    def _set_metadata(self):
        r_template = '({}){{e<3}}'
        r_str = r_template.format(self.media_title)

        hit = False

        # Load the data from json file
        with open('resources\movie_details.json', 'r') as md:
            movie_data = json.load(md)

        # Attempt a perfect match first
        for movie in movie_data['Movies']:
            if self.media_title == movie['title']:
                self.metadata = movie
                hit = True
                print('Perfect Name Match!')
                from pprint import pprint
                pprint(self.metadata)
                break

        # If that didn't work, attempt a fuzzy match
        if not hit:
            for movie in movie_data['Movies']:
                # Do a fuzzy match
                if regex.match(r_str, movie.get('title')):
                    self.metadata = movie
                    print('METADATA SET TO: ')
                    from pprint import pprint
                    pprint(self.metadata)
                    break

        # Sanity check
        if self.metadata is None:
            raise Exception('Movie missing from movie_details.json')

    def rename_original(self):
        """ Rename the original file to orig_<filename>.

        This allows us to use the actual filename throughout the pipeline
        without having to worry about name collisions and, in the event
        of a processing failure, clearly indicates the original file."""

        target = self.state.init_path.parent.joinpath('orig_' + self.state.init_path.name)
        self.state.init_path.rename(target)
        self.state.cur_path = target

    def pre_process(self):
        if self.stage == stages.STAGE_0:
            self.rename_original()
            self._analyze()

        if self.stage == stages.STAGE_1:
            mix_path = self.state.cur_dir.joinpath(self.state.clean_name + '.m4a')
            self.state.assoc_files['stereo_mix'] = mix_path

        if self.stage == stages.STAGE_2:
            self._set_metadata()

    def post_process(self):
        """ The final step in a processing stage. Any miscellaneous cleanup that doesn't
         really fit anywhere else happens here.

         Post-Processing should only happen for MKVs that successfully completed the
         command execution step.
        """

        if self.stage == stages.STAGE_0:
            # Move original MKV to the archive
            archive = self.state.root.joinpath('_archive')
            shutil.move(str(self.state.cur_path), str(archive))

            # Update current path to point to newly generated mkv
            self.state.cur_path = self.state.cur_dir.joinpath(self.state.clean_name + self.state.ext)

            # Move new mkv to next stage directory
            shutil.move(str(self.state.cur_path), str(self.state.out_dir))

        elif self.stage == stages.STAGE_1:
            # Move both files to next stage directory
            shutil.move(str(self.state.cur_path), str(self.state.out_dir))
            shutil.move(str(self.state.assoc_files['stereo_mix']), str(self.state.out_dir))

        elif self.stage == stages.STAGE_2:
            # Update current path to point to newly generated mkv
            out_name = '{} ({}){}'.format(self.metadata['title'], self.metadata['year'], self.state.ext)
            self.state.cur_path = self.state.cur_dir.joinpath(out_name)

            # Move final product into next stage directory
            shutil.move(str(self.state.cur_path), str(self.state.out_dir))

            # Clean up artifacts
            self.state.assoc_files.pop('stereo_mix')
            artifacts = [self.state.cur_dir.joinpath(self.state.clean_name + '.mkv'),
                         self.state.cur_dir.joinpath(self.state.clean_name + '.m4a')]
            for item in artifacts:
                item.unlink()

        # Finally, complete the transition to the next stage
        self.stage += 1

    def run_commands(self):
        """ Run the commands to transition to the next stage. """

        self._set_command()

        # Stage 1 is a two parter and handled a bit differently
        if self.stage == stages.STAGE_1:
            cmd_mix = self.cmd_list[0]
            cmd_encode = self.cmd_list[1]

            mix = run(cmd_mix, stdout=PIPE, stderr=PIPE)
            if mix.returncode != 0:
                raise RuntimeError('Issue creating stereo mix for mkv', mix)

            encode = run(cmd_encode, input=mix.stdout, stderr=PIPE)
            if encode.returncode != 0:
                raise RuntimeError('Issue encoding stereo mix', encode)

        # For all other stages, there's only a single command
        else:
            cmd = self.cmd_list[0]
            ret = run(cmd, stdout=PIPE, stderr=PIPE)

            if ret.returncode != 0:
                raise RuntimeError('Issue executing commands for mkv', ret)
