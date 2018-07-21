'''
Object and functions to define and work with tables of files.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Local
from hep_rfm import core
from hep_rfm.parallel import JobHandler, Worker
from hep_rfm import protocols

# Python
import hashlib
import logging
import multiprocessing
import os
import tempfile
from collections import namedtuple


__all__ = ['rfm_hash', 'FileInfo', 'FileMarks', 'Table', 'Manager']


# Default names for the file marks
__default_tmstp__ = 0
__default_fid__   = 'none'

# Buffer size to be able to hash large files
__buffer_size__ = 10485760 # 10MB

# Store the time-stamp and a file ID
FileMarks = namedtuple('FileMarks', ['tmstp', 'fid'])

# Class to store the information of a file
FileInfoBase = namedtuple('FileInfoBase', ['name', 'path', 'marks'])


def rfm_hash( path ):
    '''
    Definition of the hash function for a file.

    :param path: path to the file.
    :type path: str
    '''
    h = hashlib.sha1()

    with open(path) as f:

        # Read in chunks so we do not run out of memory
        while True:

            d = f.read(__buffer_size__)
            if not d:
                break

            h.update(data)

    return h.hexdigest()


class FileInfo(FileInfoBase):

    def __new__( cls, name, path, marks = None ):
        '''
        Initialize the object.

        :param name: name of the file.
        :type name: str
        :param path: path to the file.
        :type path: str
        :param marks: time-stamp and file ID.
        :type marks: FileMarks
        '''
        if marks is None:
            marks = FileMarks(__default_tmstp__, __default_fid__)

        fi = super(FileInfo, cls).__new__(cls, name, path, marks)

        return fi

    @classmethod
    def from_stream_line( cls, line ):
        '''
        Build the class from a line read from a table file.
        '''
        name, path, tmstp, fid = line.split()

        return cls(name, path, FileMarks(float(tmstp), fid))

    @classmethod
    def from_name_and_path( cls, name, path ):
        '''
        Build a from the file at the given path.

        :param name: name of the file.
        :type name: str
        :param path: path to the file.
        :type path: str
        :returns: built :class:`FileInfo` instance.
        :rtype: FileInfo
        '''
        fid = rfm_hash(path)

        tmstp = os.path.getmtime(path)

        marks = FileMarks(tmstp, fid)

        return cls(name, path, marks)

    def info( self ):
        '''
        This method defines the way this class is saved to a file.

        :returns: tuple with the information of this class
        :rtype: tuple(str, str, str, str)
        '''
        return (self.name, self.path, self.marks.tmstp, self.marks.fid)

    def newer_than( self, other ):
        '''
        Return whether this object corresponds to a newer version than that
        given.
        A new :class:`FileInfo` object is considered to be "newer"
        only if the two file IDs differ, and this class has a smaller
        time-stamp than that given.
        '''
        if self.marks.fid != other.marks.fid and self.marks.tmstp > other.marks.tmstp:
            return True

        return False


class Manager(object):

    def __init__( self ):
        '''
        Represent a class to store tables in different local/remote hosts, being
        able to do updates among them.
        '''
        self.tables = []

        super(Manager, self).__init__()

    def add_table( self, path ):
        '''
        Add a new table to the list of tables.

        :param path: path to the new table.
        :type path: str
        '''
        self.tables.append(path)

    def available_table( self, use_xrd = False ):
        '''
        Get the path to the first available table.

        :param use_xrd: whether to use the xrootd protocol if needed.
        :type use_xrd: bool
        :returns: path to the first available table.
        :rtype: str
        '''
        return protocols.available_path(self.tables, use_xrd)

    def update( self, parallelize = False, force = False, server_spec = None ):
        '''
        Update the different tables registered within this manager.

        :param parallelize: number of processes allowed to parallelize the \
        synchronization of all the proxies. By default it is set to 0, so no \
        parallelization  is done (0).
        :type parallelize: int
        :param force: if set to True, the files are copied even if they are \
        up to date.
        :param server_spec: specification of user for each SSH server. Must \
        be specified as a dictionary, where the keys are the hosts and the \
        values are the user names.
        :type server_spec: dict
        :type force: bool
        :raises RuntimeError: if a file is missing for any of the tables.
        '''
        #
        # Determine the files to update
        #
        update_tables = []

        names = set()

        # Copy the tables to a temporary directory to work with them,
        # and get the names of all the files

        logging.getLogger(__name__).info('Copying tables to a temporary directory')

        tmp = tempfile.TemporaryDirectory()
        for i, n in enumerate(self.tables):

            fpath = os.path.join(tmp.name, 'table_{}.txt'.format(i))

            core.copy_file(n, fpath, server_spec=server_spec)

            tu = TableUpdater(n, fpath, Table.read(fpath))

            update_tables.append(tu)

            names = names.union(tu.table.keys())

        # Loop over the tables to get the more recent versions of the files

        logging.getLogger(__name__).info('Determining most recent version of files')

        more_recent = {}

        name_error = False
        for name in names:
            for tu in update_tables:

                try:
                    f = tu.table[name]

                    if name not in more_recent or f.newer_than(more_recent[name]):
                        more_recent[name] = f

                except KeyError:

                    name_error = True

                    logging.getLogger(__name__).error('Table in "{}" does not have file "{}"'.format(tu.path, name))

        if name_error:
            raise RuntimeError('Missing files in some tables')

        # Loop over the information with the more recent versions and mark the
        # the files to update in each table.
        for f in more_recent.values():
            for u in update_tables:
                u.check_changed(f)

        # The update tables notify the tables to change their hash values and
        # timestamps
        for u in update_tables:
            u.update_table()

        #
        # Synchronize the files
        #
        inputs = []

        # Get the list of sources/targets to process from the update tables
        for u in update_tables:

            inputs += u.changes()

            if u.needs_update():
                inputs.append((u.tmp_path, u.path))

        if len(inputs):
            logging.getLogger(__name__).info('Starting to synchronize files')
        else:
            logging.getLogger(__name__).info('All files are up to date')

        kwargs = {'server_spec': server_spec}

        if parallelize:

            lock = multiprocessing.Lock()

            handler = JobHandler(inputs, parallelize)

            func = lambda obj, **kwargs: core.copy_file(*obj, **kwargs)

            kwargs['loglock'] = lock

            for i in range(handler.nproc):
                Worker(handler, func, kwargs=kwargs)

            handler.wait()
        else:
            for i in inputs:
                core.copy_file(*i, **kwargs)


class Table(dict):

    def __init__( self, files ):
        '''
        Create a table storing the information about files.
        '''
        super(Table, self).__init__()

        for f in files:
            self[f.name] = f

    @classmethod
    def read( cls, path ):
        '''
        Build a table from the information in the file at the given path.

        :param path: path to the text file storing the table.
        :type path: str
        :returns: built table.
        :rtype: Table
        '''
        files = []
        with open(path, 'rt') as fi:

            for l in fi:

                fp = FileInfo.from_stream_line(l)

                files.append(fp)

        return cls(files)

    def updated( self ):
        '''
        Return an updated version of this table, checking again all the
        properties of the files within it.
        '''
        output = []
        for f in self.values():

            if os.path.exists(f.path):

                fid = rfm_hash(f.path)

                tmstp = os.path.getmtime(f.path)

                if fid != f.marks.fid or tmstp != f.marks.tmstp:

                    f = FileInfo(f.name, f.path, FileMarks(tmstp, fid))

            output.append(f)

        return self.__class__(output)

    def write( self, path ):
        '''
        Write this table in the following location.

        :param path: where to write this table to.
        :type path: str
        '''
        with open(path, 'wt') as fo:
            for _, f in sorted(self.items()):

                info = f.info()

                frmt = '{}'
                for i in range(len(info) - 1):
                    frmt += '\t{}'
                frmt += '\n'

                fo.write(frmt.format(*info))


class TableUpdater(object):

    def __init__( self, path, tmp_path, table ):
        '''
        Class to ease the procedure of updating tables.

        :param path: path where the information of the given table is holded.
        :type path: str
        :param table: table to work with.
        :type table: Table
        '''
        super(TableUpdater, self).__init__()

        self.path     = path
        self.tmp_path = tmp_path
        self.table    = table
        self._changes = []

    def changes( self ):
        '''
        Returns the changes to apply.

        :returns: changes to apply (input and output paths).
        :rtype: list(tuple(str, str))
        '''
        return list(map(lambda t: (t[0].path, t[1].path), self._changes))

    def check_changed( self, f ):
        '''
        Determine if a content of the table needs to be updated.

        :param f: information of the file to process.
        :type f: FileInfo
        '''
        sf = self.table[f.name]
        if f.newer_than(sf):
            self._changes.append((f, sf))

    def needs_update( self ):
        '''
        Return whether the associated table needs to be updated.

        :returns: whether the associated table needs to be updated.
        :rtype: bool
        '''
        return (self._changes != [])

    def update_table( self ):
        '''
        Update the table stored within this class.
        '''
        for src, tgt in self._changes:

            self.table[tgt.name] = FileInfo(tgt.name, tgt.path, src.marks)

        self.table.write(self.tmp_path)
