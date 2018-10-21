'''
Define classes and functions to manage files and information about files.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Local
from hep_rfm import core
from hep_rfm import protocols

# Python
import os
from collections import namedtuple


__all__ = ['FileInfoBase', 'FileInfo', 'FileMarksBase', 'FileMarks']


# Default names for the file marks
__default_tmstp__ = 0
__default_fid__   = 'none'

# Store the time-stamp and a file ID
FileMarksBase = namedtuple('FileMarksBase', ['tmstp', 'fid'])
FileMarksBase.__new__.__doc__ = '''
Base class representing an object storing the time-stamp and file ID of a file.
'''

# Class to store the information of a file
FileInfoBase = namedtuple('FileInfoBase', ['name', 'protocol_path', 'marks'])
FileInfoBase.__new__.__doc__ = '''
Base class for an object storing the information about a file.
'''

# Add documentation to classes comming from collections.namedtuple()
namedtuple_extradoc = 'This object has been defined through :func:`collections.namedtuple`.'
for c in (FileMarksBase, FileInfoBase):
    c.__new__.__doc__ += namedtuple_extradoc


# Add references for classes comming from collections.namedtuple() (do not indent)
for c in (FileMarksBase, FileInfoBase):
    c.__new__.__doc__ += '''\n
.. seealso:: :class:`hep_rfm.FileInfo`, :class:`hep_rfm.FileMarks`
'''


class FileInfo(FileInfoBase):

    def __new__( cls, name, protocol_path, marks = None ):
        '''
        Object to store the information about a file.

        :param name: name of the file.
        :type name: str
        :param protocol_path: path to the file.
        :type protocol_path: ProtocolPath
        :param marks: time-stamp and file ID.
        :type marks: FileMarks

        .. seealso:: :class:`hep_rfm.FileMarks`
        '''
        if marks is None:
            marks = FileMarks()

        fi = super(FileInfo, cls).__new__(cls, name, protocol_path, marks)

        return fi

    @classmethod
    def from_stream_line( cls, line ):
        '''
        Build the class from a line read from a table file.
        '''
        name, path, tmstp, fid = line.split()

        pp = protocols.protocol_path(path)

        return cls(name, pp, FileMarks(float(tmstp), fid))

    @classmethod
    def from_name_and_path( cls, name, path ):
        '''
        Build from a name and a path to the file.
        The path must point to a local file or, in case of being a
        remote path, its path must correspond to a local file.

        :param name: name of the file.
        :type name: str
        :param path: path to the file.
        :type path: str
        :returns: built :class:`FileInfo` instance.
        :rtype: FileInfo
        :raises: ValueError: if failed to extract a valid path from that given.
        '''
        pp = protocols.protocol_path(path)

        if pp.pid != 'local':
            raise ValueError('Unable to extract a local path from "{}"'.format(path))

        marks = FileMarks.from_local_path(pp.path)

        return cls(name, pp, marks)

    def info( self ):
        '''
        This method defines the way this class is saved to a file.

        :returns: tuple with the information of this class
        :rtype: tuple(str, str, str, str)
        '''
        return (self.name, self.protocol_path.path, self.marks.tmstp, self.marks.fid)

    def is_bare( self ):
        '''
        Return whether this is a bare file.

        :returns: whether this is a bare file.
        :rtype: bool
        '''
        return self.marks.tmstp == __default_tmstp__ and self.marks.fid == __default_fid__

    def local_path( self ):
        '''
        Return the actual path in the local system, removing the information
        of the remote.
        If this is a bare file, None is returned.
        In the opposite case, an exception is raised if the file is not found
        in the associated path.

        :returns: path in the local system.
        :rtype: str or None
        :raises RuntimeError: if this is a non-bare file, and no file is found \
        in the associated path.
        '''
        if self.is_bare():
            return None

        pp = protocols.available_local_path(self.protocol_path)

        if pp is None:
            raise RuntimeError('Unable to retrieve a valid path to a file from "{}"'.format(self.protocol_path.path))

        return pp.path

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

    def updated( self ):
        '''
        Return the updated version of this file.

        :returns: updated version of this file.
        :rtype: FileInfo
        '''
        path = self.local_path()

        if path is not None:
            marks = FileMarks.from_local_path(path)
        else:
            marks = self.marks

        return FileInfo(self.name, self.protocol_path, marks)


class FileMarks(FileMarksBase):

    def __new__( cls, tmstp = __default_tmstp__, fid = __default_fid__ ):
        '''
        Represent an object storing the time-stamp and file ID of a file.

        :param tmstp: time-stamp of the file.
        :type tmstp: float
        :param fid: file ID.
        :type fid: str

        .. seealso:: :class:`hep_rfm.FileInfo`
        '''
        return super(FileMarks, cls).__new__(cls, tmstp, fid)

    @classmethod
    def from_local_path( cls, path ):
        '''
        Build the class from a local path to a file.

        :param path: path to the file.
        :type path: str
        '''
        fid = core.rfm_hash(path)

        tmstp = os.path.getmtime(path)

        return cls(tmstp, fid)
