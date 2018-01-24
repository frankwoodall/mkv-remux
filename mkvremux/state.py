import pathlib
from collections import namedtuple

# Stages of the pipeline
Pipeline = namedtuple('Pipeline', ['STAGE_0', 'STAGE_1', 'STAGE_2', 'STAGE_3'])
stages = Pipeline(0, 1, 2, 3)


class State:
    """ Helper class to track the state of the file through the entire process,
    specifically filename and directory changes.

    Note: the difference between *_fname and *_name is that
    *_fname includes the extension and *_name does not.


    Instance Attributes
    ====================

    stage       int                 Current stage of the pipeline
    orig_path   pathlib.Path        Path to the original file
    orig_fname  str                 Original filename with extension
    orig_name   str                 Original filename
    ext         str                 File extension
    cur_path    pathlib.Path        Current path to the file
    cur_fname   str                 Current filename
    next_path   pathlib.Path        Path to the next location the file should go
    next_fname  str                 Name the file should be after moving to next_path
    assoc_files list                A list of files associated with this file
    """

    def __init__(self, path: pathlib.Path, __stage: int):
        """ Constructor for FileOps

        :param path: Path to the original file location
        :param __stage: Current stage of processing for this mkv.
        """

        if not isinstance(__stage, int):
            raise TypeError('stage must be an int -- got {} instead'.format(type(__stage)))

        if not isinstance(path, pathlib.Path):
            raise TypeError('path must be pathlib.Path -- got {} instead'.format(type(path)))

        self._stage = __stage

        # Save the original path, dir, and filename as well as extension
        self.orig_path = path
        self.orig_dir = path.parent
        self.orig_fname = path.name
        self.orig_name = path.stem

        self.ext = path.suffix
        self._root = path.parent.parent

        # In Stages 1, 2, and 3, the 'current' values will differ
        self._cur_path = path
        self.cur_dir = path.parent
        self.cur_fname = path.name

        # This should always point to the next stage's processing dir
        self.out_dir = self._root.joinpath('1_remux')

        # This is filename with windows bad characters removed
        self.sanitized_name = None

        # ################################
        # Not sure if I need these anymore
        self.next_fname = None
        self.assoc_files = {}

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
        """ Ensure paths and filenames are updated each stage transition

            In general, here is what needs updating for each transition:
                - cur_path
                - out_dir
        """

        self._stage = new_stage

        if new_stage == 1:
            # Update current path
            self.cur_path = self._root.joinpath('1_remux', self.sanitized_name + self.ext)
            self.out_dir = self._root.joinpath('2_mix')

        elif new_stage == 2:
            self.cur_path = self._root.joinpath('2_mix', self.sanitized_name + self.ext)
            self.out_dir = self._root.joinpath('3_review')

        elif new_stage == 3:
            self.cur_path = self._root.joinpath('3_review', self.sanitized_name + self.ext)
            self.out_dir = None

    def __repr__(self):
        r_str = '################ FILE OPS #################'
        r_str += '\nStage:\t\t\t{}'.format(str(self._stage))
        r_str += '\no_path:\t\t\t{}'.format(str(self.orig_path))
        r_str += '\no_fname:\t\t{}'.format(str(self.orig_fname))
        r_str += '\no_name:\t\t\t{}'.format(str(self.orig_name))
        r_str += '\nf_ext:\t\t\t{}'.format(str(self.ext))
        r_str += '\nc_path:\t\t\t{}'.format(str(self.cur_path))
        r_str += '\nc_fname:\t\t{}'.format(str(self.cur_fname))
        r_str += '\nn_path:\t\t\t{}'.format(str(self.out_dir))
        r_str += '\nn_fname:\t\t{}'.format(str(self.next_fname))
        r_str += '\na_files:\t\t{}'.format(str(self.assoc_files))
        return r_str
