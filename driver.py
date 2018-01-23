from pprint import pprint
from mkvremux import MKV
from mkvremux import utils
from mkvremux.container import stages


def user_handle(mkv):
    """ Sometimes there are problems that aren't fatal but can't be decided deterministically. In that case
    we need a user to look at whatever the issue is and deconflict.

    I use a flag 'needs_user' in the MKV object to signify this. Each stream can be flagged individually so
    we need to check them all.
    """

    if mkv.video.needs_user:
        pass
    if mkv.audio.needs_user:
        select_audio(mkv)
    if mkv.subs.needs_user:
        pass


def select_audio(mkv):
    """ Sometimes, there are multiple audio streams in an MKV and we can't deterministically pick one. Seeing
    as how different people might want to handle this differently, I just raise a RuntimeError that can
    be caught and handled as desired.

    :param MKV mkv: The offending mkv object
    """

    valid_indices = []  # We'll use this in a bit to validate user input
    # No good way to guess. We need to prompt.
    # First, print an overview of each audio stream.
    # This is generally the information I'd use to decided which stream I want to copy
    for stream in mkv.audio.streams:
        # I don't want non-English language audio
        if stream['tags']['language'] != 'eng':
            continue
        index = stream['index']
        valid_indices.append(str(index))  # Record the index numbers for later validation
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
        for stream in mkv.audio.streams:
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
    for stream in mkv.audio.streams:
        if str(stream['index']) == choice:
            # Overwrite the other audio stream
            mkv.audio.copy_streams = [stream]
            break

    index = mkv.audio.copy_streams[0].get('index')
    mkv.audio.copy_indices.append(index)

    # Set copy count. Again, I can't currently think of when
    # this would ever not be 1
    mkv.audio.copy_count = 1

    # Attempt to set stream title
    mkv.audio.title = mkv.audio.copy_streams[0]['tags'].get('title')
    if mkv.audio.title is None:
        mkv.audio.title = mkv.audio.copy_streams[0].get('codec_name')
        mkv.audio.title += ' ' + mkv.audio.copy_streams[0].get('channel_layout')


def main_loop():
    """ Process each mkv. Processing has 3 distinct steps:

            1) pre-processing
                - Gathers information about the container
                - Prompt for any necessary user input
            2) command execution
                - Builds out commands for next stage
                - Executes any commands (i.e. ffmpeg, qaac)
            3) post-processing
                - Cleans up any artifacts from this stage
                - Transitions mkv to next state

        I have separated these three steps primarily as a way to manage flow and remove user input
        (when necessary) from functional code.

        Note: I have designed this driver to perform pre-processing, command execution, ans post-processing as a batch
        for all MKVs at each each stage.

        This allows me to get all of the user input out of the way (pre-processing) at the beginning. Otherwise,
        I'd have to wait for the (sometimes very long) command execution step of each mkv before being able to
        answer any prompts for the next one.
    """

    # DIRTY HACK FOR TESTING
    #import os
    #import shutil
    #shutil.copy('tests/mkvs/audio/Multiple Audio Streams.mkv', 'tests/processing/0_analyze')
    #os.chdir('tests/processing')

    stage = stages.STAGE_0

    while stage < stages.STAGE_3:
        if stage == 1:
            import sys
            sys.exit()

        print('Processing MKVs for Stage: ' + str(stage))
        mkv_list = utils.get_mkvs(stage)

        print('Found MKVs: ' + str(len(mkv_list)))

        for mkv in mkv_list:
            print('  Pre-proc for MKV: ' + str(mkv.state.cur_path))
            try:
                mkv.pre_process()

                if mkv.needs_user:
                    user_handle(mkv)

            except RuntimeError as exc:

                # These are fatal
                # TODO: This is gross
                if 'Problem extracting stream' in str(exc):
                    mkv.can_transition = False
                elif 'No video streams found' in str(exc):
                    mkv.can_transition = False
                elif 'Multiple video streams detected' in str(exc):
                    mkv.can_transition = False
                elif 'No audio streams found' in str(exc):
                    mkv.can_transition = False

        for mkv in mkv_list:
            print('  Cmd Exec for MKV: ' + str(mkv.state.cur_path))
            if mkv.can_transition:
                try:
                    mkv.run_commands()
                    mkv.stage += 1
                    print('  Cmd Exec: success!')
                except RuntimeError as exc:
                    if 'Problem Extracting Global Format Data' in str(exc):
                        # Probably a show stopper so skip this MKV
                        # TODO: Maybe somehow generate a log that this one failed?
                        continue
                    elif 'MKV missing global title' in str(exc):
                        # TODO: Need to manually prompt for media title
                        pass
            else:
                print('Stopping processing on this MKV due to earlier failure.')

            stage += 1


if __name__ == '__main__':
    main_loop()
