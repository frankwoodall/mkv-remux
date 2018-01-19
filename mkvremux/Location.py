from pathlib import Path


class Location:
    """ Helper class to track the state of the file

        Most attributes are stored as the pathlib.Path type.

        Note: the difference between _fname and _name is that
        _fname includes the extension and _name does not.

    Instanced Attributes
    ====================

    stage               Current stage of the pipeline
    orig_path           Path to the original file
    orig_fname          Original filename with extension
    orig_name           Original filename
    ext               File extension
    cur_path            Current path to the file
    cur_fname           Current filename
    next_path           Path to the next location the file should go
    next_fname          Name the file should be after moving to next_path
    assoc_files         A list of files associated with this file
    """

    def __init__(self, _path, __stage):
        """ Constructor for FileOps

        :param _path: A pathlib.Path of the original file location
        :param __stage: Current stage of processing for this mkv. """

        self._stage = __stage

        self.orig_path = _path.resolve()
        self.orig_fname = _path.name
        self.orig_name = _path.stem
        self.ext = _path.suffix

        self.cur_path = _path.resolve()
        self.cur_dir = _path.resolve().parent
        self.cur_fname = _path.name

        if __stage == 0:
            self.next_path = Path(self.orig_path.parent.parent.joinpath('1_needs_stereo'))
        elif __stage == 1:
            self.next_path = Path(self.orig_path.parent.parent.joinpath('2_needs_mux'))

        self.next_fname = None
        self.assoc_files = None

    @property
    def stage(self):
        return self._stage

    @stage.setter
    def stage(self, new_stage):
        """ Ensure paths and filenames are updated each stage transition """

        self._stage = new_stage

        if new_stage == 1:
            # Update current path and next path
            self.cur_path = Path(self.orig_path.parent.parent.joinpath('1_needs_stereo'))
            self.next_path = Path(self.orig_path.parent.parent.joinpath('2_needs_mux'))

        elif new_stage == 2:
            self.cur_path = Path(self.orig_path.parent.parent.joinpath('2_needs_mux'))
            self.next_path = Path(self.orig_path.parent.parent.joinpath('3_review'))

        elif new_stage == 3:
            self.cur_path = Path(self.orig_path.parent.parent.joinpath('3_review'))
            self.next_path = None

    def __repr__(self):
        r_str = '################ FILE OPS #################'
        r_str += '\nStage:\t\t\t{}'.format(str(self._stage))
        r_str += '\no_path:\t\t\t{}'.format(str(self.orig_path))
        r_str += '\no_fname:\t\t{}'.format(str(self.orig_fname))
        r_str += '\no_name:\t\t\t{}'.format(str(self.orig_name))
        r_str += '\nf_ext:\t\t\t{}'.format(str(self.ext))
        r_str += '\nc_path:\t\t\t{}'.format(str(self.cur_path))
        r_str += '\nc_fname:\t\t{}'.format(str(self.cur_fname))
        r_str += '\nn_path:\t\t\t{}'.format(str(self.next_path))
        r_str += '\nn_fname:\t\t{}'.format(str(self.next_fname))
        r_str += '\na_files:\t\t{}'.format(str(self.assoc_files))
        return r_str
