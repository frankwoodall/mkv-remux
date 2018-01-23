import pathlib
from typing import List
from mkvremux import MKV


def list_by_extension(target: str, ext: str) -> list:
    """ Given a target directory and a file extension, return a dir listing
    containing only files of that type.

    :param str target:  Path to the target directory
    :param str ext:     Desired file extension including the dot (e.g. '.mkv')
    :return list:       A list containing the results
    """

    p = pathlib.Path(target)
    return [_ for _ in p.iterdir() if _.suffix == ext]


def get_mkvs(stage: int) -> List[MKV]:
    """ Given a specific processing stage, find all MKVs that need to be handle

    :param int stage:   The desired processing stage
    :return list:       A list of found MKVs
    """

    search_paths = {
        0: '0_analyze',
        1: '1_remux',
        2: '2_mix'
    }

    files = list_by_extension(search_paths[stage], '.mkv')
    return [MKV(_, stage) for _ in files]
