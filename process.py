#! python3

import os
import json
import regex
import shutil
import logging
import argparse
from pathlib import Path
from pprint import pprint
from collections import namedtuple
from subprocess import run, PIPE, DEVNULL

# Stages of the pipeline
Pipeline = namedtuple('Pipeline', ['STAGE_0', 'STAGE_1', 'STAGE_2', 'STAGE_3'])
stages = Pipeline(0, 1, 2, 3)


class MKV:

    def __init__(self, _path, _stage):
        self.path = _path        # this is a pathlib.Path -- not a string
        self.name = _path.stem
        self.filename = _path.name
        self.stage = _stage

        # Helpers. Hold the command used to process and the output dir
        self.cmd = None
        self.out_dir = None

        # Hold the various streams
        self.audio_streams = None
        self.video_streams = None
        self.subtitle_streams = None

        # These will hold the desired indices for each stream
        self.audio_index = None
        self.video_index = None
        self.sub_indices = None

        # Stream titles
        self.as_title = None
        self.vs_title = None
        self.g_title = None

        # Metadata
        self.metadata = None


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--type', help='Are we processing rips or downloads', default='rips',
                        choices=['rips', 'downloads'])
    parser.add_argument('--log-level', help='What level of logging to display', default='info',
                        choices=['info', 'warning', 'debug', 'critical', 'error'])

    args = parser.parse_args()
    return args


def find_mkvs(stage):
    """ Given a directory, find all of the MKV files inside. No recursion.

    :param stage: Maps to the search directory
    :return: A list of the paths to the mkv files"""

    search_paths = {
        0: '0_downloaded',
        1: '1_needs_stereo',
        2: '2_needs_mux'
    }

    # Get the listing
    p = Path(search_paths.get(stage))
    list = [_ for _ in p.iterdir() if _.suffix == '.mkv']

    # Now turn them into MKV objects
    return [MKV(_, stage) for _ in list]


def handle_error(ret_v, ret_a_, ret_s):
    raise NotImplementedError('Implement me')


def analyze_container(mkv):
    """ When we have a downloaded file to process, we don't really know what's been done to it.

    The goal here is to extract the best video and audio tracks, as well as any forced English subs.

    :param mkv:
    :return:
    """

    def choose_video_streams():
        """ Helper function to select the proper video stream """
        _num_v_streams = len(mkv.video_streams)
        print('\n   [*] Video streams found: ' + str(_num_v_streams))

        # Sanity check. Should really only ever be 1
        if _num_v_streams != 1:
            # Attached covers generally come back as "Video" streams
            # Attempt to filter those out
            # The list of codec names is not complete. Will probably break as I find new ones
            non_image_streams = [x for x in mkv.video_streams if x.get('codec_name').lower() not in ['mjpeg']]

            # If we _still_ have multiple video streams
            if len(non_image_streams) != 1:
                # Need to handle this file manually. Bail
                raise Exception('Multiple video streams detected. Stopping processing')
            else:
                # Otherwise, let's use that one
                mkv.video_streams = non_image_streams

        # Grab the index number
        mkv.video_index = mkv.video_streams[0]['index']
        print('     [*] Index: ' + str(mkv.video_index))

        # Attempt to set title
        mkv.vs_title = mkv.video_streams[0].get('title')
        if mkv.vs_title is None:
            mkv.vs_title = mkv.video_streams[0]['codec_name'] + ' Remux'

    def choose_subtitle_streams():
        """ Helper function to select the correct subtitle streams """
        found_subs = []
        print('\n   [*] Subtitle streams found: ' + str(len(mkv.subtitle_streams)))
        print('     [*] Filtering non-English subs...')

        # We're only interested in english subs, so ditch everything else
        eng_subs = [_ for _ in mkv.subtitle_streams if _['tags']['language'].lower() in ['eng', 'english']]
        print('     [*] English subs remaining: ' + str(len(eng_subs)))

        # If there are English subs
        if len(eng_subs) != 0:
            # We only want _forced_ subs
            for s in eng_subs:
                disp = s.get('disposition')
                forced = disp.get('forced')

                if forced == 1:
                    print('     [*] Forced subs found!')
                    # Add the index to the list
                    found_subs.append(s.get('index'))

        if len(found_subs) > 0:
            mkv.sub_indices = found_subs

    def choose_audio_streams():
        """ Helper function to select the proper audio stream """
        num_a_streams = len(mkv.audio_streams)
        print('\n   [*] Audio streams found: ' + str(num_a_streams))

        # Sanity check. Should always have at least 1
        if num_a_streams == 0:
            # Need to handle file manually. Bail
            raise Exception('Zero audio streams detected. Stopping processing')

        # If there's only one just use it
        elif num_a_streams == 1:
            mkv.audio_index = mkv.audio_streams[0]['index']
            print('     [*] Index: ' + str(mkv.audio_index))

        # Multiple audio streams. Have to prompt.
        else:
            for stream in mkv.audio_streams:
                index = stream['index']
                print('     [Stream #{}]'.format(str(index)))
                print('       [Name]: ' + str(stream.get('title')))
                print('       [Codec]: ' + str(stream.get('codec_name')))
                print('       [Channels]: ' + str(stream.get('channels')))
                print('       [default]: ' + str(stream.get('disposition')['default']))
                print('       [Tags] ')
                for k, v in stream['tags'].items():
                    print('         [{}] {}'.format(k, v))
                print('\n\n')

            a_index = input('     [*] Enter the number of desired audio stream or M for more info: ')
            if a_index.lower() == 'm':
                for stream in mkv.audio_streams:
                    index = stream['index']
                    print('     [Stream #{}]'.format(str(index)))
                    pprint(stream)
                    print('\n\n')

            # Hold the selection
            if a_index.lower() != 'm':
                ans = input('     [*] You entered {} -- is this correct? [Y/n] '.format(str(a_index)))

            else:
                # Just put some value in here so we hit the loop
                ans = 'loop'

            while ans.lower() not in ['', 'y', 'yes']:
                a_index = input('     [*] Enter the number of desired audio stream: ')
                ans = input('     [*] You entered {} -- is this correct? [Y/n] '.format(str(a_index)))

            # Set index
            mkv.audio_index = a_index

            # Attempt to set title for chosen audio stream
            for s in mkv.audio_streams:
                if str(s.get('index')) == mkv.audio_index:
                    mkv.as_title = s.get('title')

            if mkv.as_title is None:
                for s in mkv.audio_streams:
                    if str(s.get('index')) == mkv.audio_index:
                        mkv.as_title = s.get('codec_name') + ' ' + s.get('channel_layout')

    def check_title(tags):
        """ Helper function. Make sure the film title is reasonable.

        :param tags: A dict containing the tags from the original container
        :return:
        """

        print('\n   [*] Checking film title: ')

        og_title = tags.get('title')
        print('     [*] Original title: ' + str(og_title))

        ans = input('     [*] Keep this title or enter a new one [KEEP]: ')
        if ans.lower() not in ['', 'y', 'yes']:
            print('       [*] New title set to: ' + ans)
            mkv.g_title = ans
        else:
            print('       [*] Keeping original title')
            mkv.g_title = og_title

    def review():
        print('\n   [*] Stream titles have been chosen..')
        print('     [*] Video: ' + str(mkv.vs_title))
        print('     [*] Audio: ' + str(mkv.as_title))

        ans = input('     [*] Keep this Video title or provide alternate [KEEP]: ')
        if ans.lower() not in ['', 'y', 'yes']:
            mkv.vs_title = ans
            print('       [*] Overriding Video Stream title...')
            print('       [*] New title: ' + mkv.vs_title)

        ans = input('     [*] Keep this Audio title or provide alternate [KEEP]: ')
        if ans.lower() not in ['', 'y', 'yes']:
            mkv.as_title = ans
            print('       [*] Overriding Audio Stream title...')
            print('       [*] New title: ' + mkv.as_title)

    def choose_streams():
        """ Wrapper function. Choose the appropriate streams and review selection """
        choose_video_streams()
        choose_audio_streams()
        choose_subtitle_streams()
        review()

    cmd_v = ['ffprobe', '-show_streams', '-select_streams', 'v', '-print_format', 'json', str(mkv.path)]
    cmd_a = ['ffprobe', '-show_streams', '-select_streams', 'a', '-print_format', 'json', str(mkv.path)]
    cmd_s = ['ffprobe', '-show_streams', '-select_streams', 's', '-print_format', 'json', str(mkv.path)]
    cmd_g = ['ffprobe', '-show_format', '-print_format', 'json', str(mkv.path)]

    print('     [*] Finding video streams...')
    ret_v = run(cmd_v, stdout=PIPE, stderr=DEVNULL)

    print('     [*] Finding audio streams...')
    ret_a = run(cmd_a, stdout=PIPE, stderr=DEVNULL)

    print('     [*] Finding subtitle streams...')
    ret_s = run(cmd_s, stdout=PIPE, stderr=DEVNULL)

    print('     [*] Getting global metadata...')
    ret_g = run(cmd_g, stdout=PIPE, stderr=DEVNULL)     # Gotta be a better way than this

    # First, let's make sure nothing went wrong
    if sum([ret_v.returncode, ret_a.returncode, ret_s.returncode, ret_g.returncode]) != 0:
        handle_error(ret_v, ret_a, ret_s)

    else:
        # Convert results into something useful
        v_data = json.loads(ret_v.stdout)
        a_data = json.loads(ret_a.stdout)
        s_data = json.loads(ret_s.stdout)
        g_data = json.loads(ret_g.stdout)

        # Set the streams
        mkv.video_streams = v_data['streams']
        mkv.audio_streams = a_data['streams']
        mkv.subtitle_streams = s_data['streams']

        # Check the film title
        check_title(g_data['format']['tags'])

        # Choose the streams
        choose_streams()


def set_metadata(mkv):
    r_template = '({}){{e<3}}'
    r_str = r_template.format(mkv.name)

    hit = False

    # Load the data from json file
    with open('2_needs_mux\movie_details.json', 'r') as md:
        movie_data = json.load(md)

    # Attempt a perfect match first
    for movie in movie_data['Movies']:
        if mkv.name == movie['title']:
            mkv.metadata = movie
            hit = True
            print('Perfect Name Match!')
            from pprint import pprint
            pprint(mkv.metadata)
            break

    # If that didn't work, attempt a fuzzy match
    if not hit:
        for movie in movie_data['Movies']:
            # Do a fuzzy match
            if regex.match(r_str, movie.get('title')):
                mkv.metadata = movie
                print('METADATA SET TO: ')
                from pprint import pprint
                pprint(mkv.metadata)
                break

    # Sanity check
    if mkv.metadata is None:
        raise Exception('Movie missing from movie_details.json')


def build_cmd_0(mkv):
    # Windows can't handle colons in filenames. Just remove it
    new_name = '{}.mkv'.format(str(mkv.g_title).replace(':', ''))
    out_file = mkv.out_dir.resolve().joinpath(new_name)

    cmd_list = ['ffmpeg', '-report', '-hide_banner', '-loglevel', 'verbose', '-i', str(mkv.path)]

    # Extract the video stream
    cmd_list += ['-map', '0:{}'.format(str(mkv.video_index))]

    # Extract the audio stream
    cmd_list += ['-map', '0:{}'.format(str(mkv.audio_index))]

    # Make sure we copy over any global metadata
    cmd_list += ['-map_metadata', '0']

    # Set the film title
    cmd_list += ['-metadata', 'title={}'.format(mkv.g_title)]

    # Make sure stream titles are set
    cmd_list += ['-metadata:s:v:0', 'title={}'.format(mkv.vs_title)]
    cmd_list += ['-metadata:s:a:0', 'title={}'.format(mkv.as_title)]

    # If we have subtitles, add them
    if mkv.sub_indices is not None:
        for s in mkv.sub_indices:
            cmd_list += ['-map', '0:{}'.format(str(s))]

    # Copy without transcoding
    cmd_list += ['-c', 'copy']

    # Tell it where to put the results
    cmd_list.append(str(out_file))

    # Set the command
    mkv.cmd = cmd_list


def build_cmd_1(mkv):
    """ Construct a command to generate a stereo mix from a given mkv file """

    stereo_mix_file = '{}.m4a'.format(mkv.name)
    out_file = mkv.out_dir.resolve().joinpath(stereo_mix_file)

    cmd_list = ['ffmpeg', '-report', '-hide_banner', '-loglevel', 'verbose', '-i', str(mkv.path)]

    # Extract the audio stream
    cmd_list += ['-map', '0:a:0']

    # Set the output type, codec, and number of channels
    cmd_list += ['-f', 'wav', '-acodec', 'pcm_f32le', '-ac', '2']

    # Set the filter
    cmd_list += ['-af', 'pan=stereo:FL=FC+0.30*FL+0.30*BL:FR=FC+0.30*FR+0.30*BR']

    # Output to stdout
    cmd_list += ['-']

    # And pipe to qaac
    cmd_list += ['|', 'qaac64', '--verbose']

    # qaac args
    cmd_list += ['--tvbr', '127', '--quality', '2', '--rate', 'keep', '--ignorelength', '--no-delay']

    # qaac read from stdin
    cmd_list += ['-']

    # And set output file
    cmd_list += ['-o', str(out_file)]

    # Set the command
    mkv.cmd = cmd_list


def build_cmd_2(mkv):
    """ Mux the in the stereo mix and set all metadata """
    stereo_mix_file = mkv.path.parent.joinpath('{}.m4a'.format(mkv.name))
    out_name = '{} ({}).mkv'.format(mkv.metadata['title'].replace(':', ''), mkv.metadata['year'])
    out_file = mkv.out_dir.resolve().joinpath(out_name)

    print('mkv.metadata.title')
    print(mkv.metadata['title'])

    cmd_list = ['ffmpeg', '-report', '-hide_banner', '-loglevel', 'verbose', '-i', str(mkv.path)]

    # Second input of stereo mix
    cmd_list += ['-i', str(stereo_mix_file)]

    # Extract all streams from both inputs. Direct copy
    cmd_list += ['-map', '0', '-map', '1', '-c', 'copy']

    # Copy global metadata
    cmd_list += ['-map_metadata', '0']

    # Set new global metadata
    cmd_list += ['-metadata', 'provenance={}'.format(mkv.metadata.get('prov'))]
    cmd_list += ['-metadata', 'source={}'.format(mkv.metadata.get('source'))]
    cmd_list += ['-metadata', 'description={}'.format(mkv.metadata.get('desc'))]
    cmd_list += ['-metadata', 'rel_year={}'.format(mkv.metadata.get('year'))]
    cmd_list += ['-metadata', 'imdb_id={}'.format(mkv.metadata.get('imdb_id'))]

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

    mkv.cmd = cmd_list


def set_out_dir(mkv):
    # Map current stage to output dir
    out_map = {
        0: '1_needs_stereo',
        1: '2_needs_mux',
        2: '3_review'
    }

    p = Path(out_map.get(mkv.stage))
    mkv.out_dir = p


def set_command(mkv):

    # Figure out which type of command we need
    if mkv.stage == stages.STAGE_0:
        build_cmd_0(mkv)
    elif mkv.stage == stages.STAGE_1:
        build_cmd_1(mkv)
    elif mkv.stage == stages.STAGE_2:
        build_cmd_2(mkv)


def archive(mkv):
    """ Move the original file into the archive in case we need it later. """

    print('     [*] Moving original file to archive...')
    if mkv.stage == stages.STAGE_0:
        shutil.move(str(mkv.path), '_archive\{}_usenet.mkv'.format(str(mkv.name)))
    else:
        shutil.move(str(mkv.path), '_archive\{}_rip.mkv'.format(str(mkv.name)))


def post_process(mkv):
    if mkv.stage == stages.STAGE_0:
        archive(mkv)
    elif mkv.stage == stages.STAGE_1:
        print('     [*] Moving file to stereo muxing...')
        shutil.move(str(mkv.path), str(mkv.out_dir))

        # Set next stage and re-process
        mkv.stage = stages.STAGE_2

        # Update File location
        mkv.path = mkv.out_dir.joinpath(mkv.filename)

        # Next stage!
        process(mkv)
    elif mkv.stage == stages.STAGE_2:
        # We only want to archive if it's not a usenet source (because we already archived that in stage 0)
        if mkv.metadata.get('prov') == 'Usenet':
            print('     [*] Removing extracted file...')
            os.remove(str(mkv.path))
        else:
            archive(mkv)

        print('     [*] Removing stereo mix...')
        os.remove(mkv.path.parent.joinpath('{}.m4a'.format(mkv.name)))


def pre_process(mkv):
    # Handle any stage specific items
    if mkv.stage == stages.STAGE_0:
        # We need to extract the streams
        analyze_container(mkv)

    elif mkv.stage == stages.STAGE_2:
        # We need to ensure all the metadata is set
        set_metadata(mkv)


def process(mkv):
    """ Handle any stage specific needs then execute command """
    print('')
    print('   [*] Processing: [STAGE {}] {}'.format(str(mkv.stage), str(mkv.filename)))

    # Handle any stage specific needs
    pre_process(mkv)

    # Where should we send the output
    set_out_dir(mkv)

    # Construct the command
    set_command(mkv)

    # And execute!
    print('   [*] Executing: ' + ' '.join(mkv.cmd))
    ret = run(mkv.cmd, stdout=PIPE, stderr=DEVNULL, shell=True)

    if ret.returncode == 0:
        print('   [*] Success!')
        post_process(mkv)


def start():
    print("[*] Frank's Media Library Configurator v1.0")
    args = parse_args()

    # Set up logger
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), None))

    # Set stage
    if args.type == 'downloads':
        stage = stages.STAGE_0
    elif args.type == 'rips':
        stage = stages.STAGE_1

    # Find mkvs in appropriate location
    mkv_list = find_mkvs(stage)

    print('[*] MKV Files Found: {}'.format(str(len(mkv_list))))

    for mkv in mkv_list:
        process(mkv)


if __name__ == '__main__':
    start()
