import shutil
import pathlib
from collections import namedtuple

# Stages of the pipeline
Pipeline = namedtuple('Pipeline', ['STAGE_0', 'STAGE_1', 'STAGE_2', 'STAGE_3'])
stages = Pipeline(0, 1, 2, 3)


class State:
    """ Helper class to track the state of the file through the entire process,
    specifically filename and directory changes.

    Note: The State object should never actually make any changes to itself (e.g. renaming a file).
    All changes should be initiated by the controlling object or code.


    Instance Attributes
    ====================

    stage       int                 Current stage of the pipeline
    orig_path   pathlib.Path        Path to the original file
    orig_dir    pathlib.Path        Path to the original directory
    orig_name   str                 Original filename
    orig_fname  str                 Original filename with extension
    ext         str                 File extension
    root        pathlib.Path        Processing root directory

    cur_path    pathlib.Path        Path to the file's current location
    cur_dir     pathlib.Path        Path to the file's current directory
    cur_fname   str                 Current filename

    out_dir     pathlib.path        Path to where the file should go next

    clean_name  str                 The name of the file with badchars removed
    assoc_files dict                A dict of files associated with this file

    # Maybe not needed
    next_path   pathlib.Path        Path to the next location the file should go
    next_fname  str                 Name the file should be after moving to next_path
    """

    def __init__(self, path: pathlib.Path, start_stage: int):
        """ Constructor for FileOps

        :param path: Path to the original file location
        :param start_stage: Current stage of processing for this mkv.
        """

        if not isinstance(start_stage, int):
            raise TypeError('stage must be an int -- got {} instead'.format(type(start_stage)))

        if not isinstance(path, pathlib.Path):
            raise TypeError('path must be pathlib.Path -- got {} instead'.format(type(path)))

        #self._stage = start_stage
        self._stage = None

        # Save the original path, dir, and filename as well as extension
        #self.orig_path = path
        #self.orig_dir = path.parent
        #self.orig_fname = path.name
        #self.orig_name = path.stem
        self.init_path = path

        #self.ext = path.suffix
        #self.root = path.parent.parent
        self.ext = None
        self.root = None

        # In Stages 1, 2, and 3, the 'current' values will differ
        #self._cur_path = path
        #self.cur_dir = path.parent
        #self.cur_fname = path.name
        self._cur_path = None
        self.cur_dir = None
        self.cur_fname = None

        # This should always point to the next stage's processing dir
        #self.out_dir = self.root.joinpath('1_remux')
        self._out_dir = None
        self.out_fname = None

        # This is filename with windows bad characters removed
        self.clean_name = None

        self.assoc_files = {}

        # If you're wondering how most of the above attributes get set on init. It's here
        self.stage = start_stage

    @property
    def out_dir(self):
        return self._out_dir

    @out_dir.setter
    def out_dir(self, new_path):
        self._out_dir = new_path
        if self.clean_name:
            self.out_fname = self.clean_name + self.ext
        else:
            self.out_fname = self.cur_fname

    @property
    def cur_path(self):
        return self._cur_path

    @cur_path.setter
    def cur_path(self, new_path):
        """ Whenever current path is updated, we need to update all the
            helper attributes we provide.

            Here is what changes:
                - cur_dir
                - cur_fname
        """
        self._cur_path = new_path
        self.cur_dir = new_path.parent
        self.cur_fname = new_path.name

    @property
    def stage(self):
        return self._stage

    @stage.setter
    def stage(self, new_stage):
        """ This is the workhorse of the state class.

        Ensure paths and filenames are updated each stage transition

            In general, here is what needs updating for each transition:
                - cur_path
                - out_dir
        """

        if new_stage == stages.STAGE_0:
            # Need to document all of the attributes that won't ever change
            self.ext = self.init_path.suffix
            self.root = self.init_path.parent.parent
            self.cur_path = self.init_path
            self.out_dir = self.root.joinpath('1_remux')

        elif new_stage == stages.STAGE_1:
            self.cur_path = self.root.joinpath('1_remux', self.clean_name + self.ext)
            self.out_dir = self.root.joinpath('2_mix')

        elif new_stage == stages.STAGE_2:
            self.cur_path = self.root.joinpath('2_mix', self.clean_name + self.ext)
            self.out_dir = self.root.joinpath('3_review')

            # Also update the path for 'stereo_mix'
            if 'stereo_mix' in self.assoc_files:
                mix_file = self.assoc_files['stereo_mix'].name
                self.assoc_files['stereo_mix'] = self.root.joinpath('2_mix', mix_file)

        elif new_stage == stages.STAGE_3:
            self.cur_path = self.root.joinpath('3_review', self.clean_name + self.ext)
            self.out_dir = None

        # Once we know everything else worked, actually update the stage
        self._stage = new_stage
