'''
Define functions to manage protocols.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Python
import logging
import os
import subprocess

# Local
from hep_rfm.exceptions import CopyFileError, MakeDirsError


__all__ = [
    'ProtocolPath',
    'LocalPath',
    'RemotePath',
    'SSHPath',
    'XRootDPath',
    'available_path',
    'available_local_path',
    'protocol_path',
    'register_protocol',
    'remote_protocol',
    ]


def decorate_copy( method ):
    '''
    Decorator for the "copy" methods of the protocols.

    :param method: method to wrap, which must be any overriden version of \
    :func:`ProtocolPath.copy`.
    :type method: function
    :returns: wrapper around the method.
    :rtype: function
    '''
    def wrapper( self, target ):
        '''
        Internal wrapper to copy the file to a target.
        '''
        proc = method(self, target)

        if proc.wait() != 0:
            _, stderr = proc.communicate()
            raise CopyFileError(self.path, target, stderr.decode())

    return wrapper


def decorate_mkdirs( method ):
    '''
    Decorator for the "mkdirs" methods of the protocols.

    :param method: method to wrap, which must be any overriden version of \
    :func:`ProtocolPath.mkdirs`.
    :type method: function
    :returns: wrapper around the method.
    :rtype: function
    '''
    def wrapper( self ):
        '''
        Internal wrapper to create the necessary directories to a target.
        '''
        proc = method(self)

        if proc.wait() != 0:
            _, stderr = proc.communicate()
            raise MakeDirsError(self.path, stderr.decode())

    return wrapper


def _process( *args ):
    '''
    Create a subprocess object with a defined "stdout" and "stderr",
    using the given commands.

    :param args: set of commands to call.
    :type args: tuple
    :returns: subprocess applying the given commands.
    :rtype: subprocess.Popen
    '''
    return subprocess.Popen( args,
                             stdout = subprocess.PIPE,
                             stderr = subprocess.PIPE )


def register_protocol( name ):
    '''
    Decorator to register a protocol with the given name.
    The new protocol is stored in a dictionary in the :class:`ProtocolPath`
    class.

    :returns: wrapper for the class.
    :rtype: function
    '''
    def wrapper( protocol ):
        '''
        Wrapper around the protocol constructor.
        '''
        if not issubclass(protocol, ProtocolPath):
            raise RuntimeError('Attempt to register a protocol path that does not inherit from ProtocolPath')

        if name in ProtocolPath.__protocols__:
            raise ValueError('Protocol path with name "{}" already exists'.format(name))

        ProtocolPath.__protocols__[name] = protocol
        protocol.pid = name

        return protocol

    return wrapper


class ProtocolPath(object):

    # All protocols must have a protocol ID.
    __protocols__ = {}

    def __init__( self, path, path_checker = None ):
        '''
        Base class to represent a protocol to manage a path to a file.
        The protocol IDs are defined at runtime, using
        :func:`ProtocolPath.register_protocol`. The protocols are saved on a
        dictionary, where the keys are the protocol IDs.
        This is an abstract class, and any class inheriting from it must
        override the following methods:
        1. :func:`ProtocolPath.check_path`
        3. :func:`ProtocolPath.copy`
        3. :func:`ProtocolPath.is_remote`
        4. :func:`ProtocolPath.mkdirs`
        '''
        if path_checker is not None and not path_checker(path):
            raise ValueError('Instance of protocol path "{}" can not be built from path "{}"'.format(self.__class__.__name__, path))

        self._path = path

    def __eq__( self, other ):
        '''
        Two :class:`ProtocolPath` instances are considered equal if they have
        the same path.

        :returns: whether the two protocol paths are equal
        :rtype: bool
        '''
        return self.path == other.path

    def __neq__( self, other ):
        '''
        Negation of the result from :func:`ProtocolPath.__eq__`.

        :returns: whether two :class:`ProtocolPath` instances are not equal.
        :rtype: bool
        '''
        return not self.__eq__(other)

    def __repr__( self ):
        '''
        Representation of this object when printed.

        :returns: representation of this object when printed.
        :rtype: str
        '''
        return self.__str__()

    def __str__( self ):
        '''
        Representation as a string.

        :returns: this class as a string.
        :rtype: str
        '''
        return "{}(path='{}')".format(self.__class__.__name__, self.path)

    @decorate_copy
    def copy( self, target ):
        '''
        Copy the file associated to this protocol to the target location.
        The target must be accessible.
        In this case, this is an abstract method.
        '''
        raise NotImplementedError('Attempt to call abstract class method')

    @property
    def is_remote( self ):
        '''
        Method to be overriden which determines whether this is a remote
        protocol or not.
        In this case, this is an abstract method.
        '''
        raise NotImplementedError('Attempt to call abstract class method')

    @decorate_mkdirs
    def mkdirs( self ):
        '''
        Make directories to the file path within this protocol.
        In this case, this is an abstract method.
        '''
        raise NotImplementedError('Attempt to call abstract class method')

    @property
    def path( self ):
        '''
        Return the associated path to the file.

        :returns: associated path.
        :rtype: str
        '''
        return self._path


@register_protocol('local')
class LocalPath(ProtocolPath):

    def __init__( self, path ):
        '''
        Represent a path to a local file.
        '''
        super(LocalPath, self).__init__(path)

    @decorate_copy
    def copy( self, target ):
        '''
        Copy the file associated to this protocol to the target location.
        The target must be accessible.

        :param target: where to copy the file.
        :type target: ProtocolPath
        :raises CopyFileError: if a problem appears while copying the file.
        '''
        return _process('cp', self.path, target.path)

    @property
    def is_remote( self ):
        '''
        Return whether this is a remote protocol or not.

        :returns: whether the protocol is local (True in this case).
        :rtype: bool
        '''
        return False

    @decorate_mkdirs
    def mkdirs( self ):
        '''
        Make directories to the file path within this protocol.

        :raises MakeDirsError: if an error occurs while creating directories.
        '''
        dpath = os.path.dirname(self.path)

        return _process('mkdir', '-p', dpath if dpath != '' else './')


class RemotePath(ProtocolPath):

    def __init__( self, path, path_checker = None ):
        '''
        Represent a remote path.
        This is an abstract class, any class inheriting from it must override
        the following methods:
        1. :func:`ProtocolPath.check_path`
        2. :func:`ProtocolPath.copy`
        3. :func:`ProtocolPath.mkdirs`
        4. :func:`RemotePath.split_path`
        '''
        super(RemotePath, self).__init__(path, path_checker)

    @property
    def is_remote( self ):
        '''
        Return whether this is a remote protocol or not.
        '''
        return True

    def split_path( self ):
        '''
        Split the remote path in the server specifications and path in the
        server.
        In this case, this is an abstract method.
        '''
        raise NotImplementedError('Attempt to call abstract class method')


@register_protocol('ssh')
class SSHPath(RemotePath):

    def __init__( self, path ):
        '''
        Represent a path to be handled using SSH.
        '''
        if '@' not in path:
            raise ValueError('Path "{}" is not a valid SSH path'.format(path))

        super(SSHPath, self).__init__(path, lambda p: ('@' in p))

    @decorate_copy
    def copy( self, target ):
        '''
        Copy the file associated to this protocol to the target location.
        The target must be accessible.

        :param target: where to copy the file.
        :type target: ProtocolPath
        :raises CopyFileError: if a problem appears while copying the file.
        '''
        return _process('scp', '-q', self.path, target.path)

    @decorate_mkdirs
    def mkdirs( self ):
        '''
        Make directories to the file path within this protocol.

        :raises MakeDirsError: if an error occurs while creating directories.
        '''
        server, sepath = self.split_path()

        dpath = os.path.dirname(sepath)

        return _process('ssh', '-X', server, 'mkdir', '-p', dpath)

    def specify_server( self, server_spec = None ):
        '''
        Process the given path and return a modified version of it adding
        the correct user name.
        The user name for each host must be specified in server_spec.

        :param path: path to a file.
        :type path: str
        :param server_spec: specification of user for each SSH server. Must \
        be specified as a dictionary, where the keys are the hosts and the \
        values are the user names.
        :type server_spec: dict
        :returns: modified version of "path".
        :rtype: str
        :raises RuntimeError: if there is no way to determine the user name \
        for the given path.
        '''
        path = self.path

        server_spec = server_spec if server_spec is not None else {}

        l = path.find('@')

        if l == 0 and not server_spec:
            raise RuntimeError('User name not specified for path "{}"'.format(self.path))

        uh, _ = self.split_path()

        u, h = uh.split('@')

        for host, uname in server_spec.items():

            if host == h:
                path = uname + path[l:]
                break

        if path.startswith('@'):
            raise RuntimeError('Unable to find a proper user name for path "{}"'.format(self.path))

        return self.__class__(path)

    def split_path( self ):
        '''
        Split the remote path in the server specifications and path in the
        server.

        :returns: server specifications and path in the server.
        :rtype: str, str
        '''
        return self.path.split(':')


@register_protocol('xrootd')
class XRootDPath(RemotePath):

    def __init__( self, path ):
        '''
        Represent a path to be handled using XROOTD protocol.
        '''
        super(XRootDPath, self).__init__(path, lambda p: p.startswith('root://'))

    @decorate_copy
    def copy( self, target ):
        '''
        Copy the file associated to this protocol to the target location.
        The target must be accessible.

        :param target: where to copy the file.
        :type target: ProtocolPath
        :raises CopyFileError: if a problem appears while copying the file.
        '''
        return _process('xrdcp', '-f', '-s', self.path, target.path)

    @decorate_mkdirs
    def mkdirs( self ):
        '''
        Make directories to the file path within this protocol.

        :raises MakeDirsError: if an error occurs while creating directories.
        '''
        server, sepath = self.split_path()

        dpath = os.path.dirname(sepath)

        return _process('xrd', server, 'mkdir', dpath)

    def split_path( self ):
        '''
        Split the remote path in the server specifications and path in the
        server.

        :returns: server specifications and path in the server.
        :rtype: str, str
        '''
        rp = self.path.find('//', 7)
        return self.path[7:rp], self.path[rp + 1:]


def available_local_path( path, use_xrd = False ):
    '''
    If a local path can be resolved from "path", it returns it.
    Return None otherwise.
    If "use_xrd" is True, and the given path is a xrd-protocol path, then
    it will be directly returned.

    :param path: path to process.
    :type path: ProtocolPath
    :param use_xrd: whether to use the xrootd protocol.
    :type use_xrd: bool
    :returns: local path.
    :rtype: ProtocolPath or None
    '''
    if path.is_remote:

        if use_xrd and path.pid == XRootDPath.pid:
            # Using XRootD protocol is allowed
            return path

        server, sepath = path.split_path()

        if os.path.exists(sepath):
            # Local and remote hosts are the same
            return sepath

    else:
        if os.path.exists(path.path):
            return path

    return None


def available_path( paths, use_xrd=False ):
    '''
    Return the first available path from a list of paths. If "use_xrd" is
    set to True, then this also stands for any path using the XRootD
    protocol (by default they are avoided).

    :param paths: list of paths to process.
    :type paths: collection(ProtocolPath)
    :param use_xrd: whether using XRootD protocol is allowed.
    :type use_xrd: bool
    :returns: first available path found.
    :rtype: str
    :raises RuntimeError: if it fails to find an available path.

    .. warning::
       If the path to a file on a remote site matches that of a local file,
       it will be returned. This allows to use local files while specifying
       remote paths. However, if a path on a remote site matches a local
       file, which does not correspond to a proxy of the path referenced by
       this object, it will result on a fake reference to the file.
    '''
    for path in paths:

        p = available_local_path(path, use_xrd)

        if p is not None:
            return p

    raise RuntimeError('Unable to find an available path')


def protocol_path( path, protocol = None ):
    '''
    Return a instantiated protocol using the given path.
    It can be any of the declared protocols, as far as it satisfies the
    :func:`Protocol.check_path` function for it.
    The local protocol is considered as the last option.

    :returns: protocol associated to the given path.
    :rtype: ProtocolPath

    .. warning:: If the result of the :func:`Protocol.check_path` function is \
       True for more than one protocol path, it will return the first found.
    '''
    if protocol == None:
        return LocalPath(path)
    else:
        if protocol in ProtocolPath.__protocols__:
            return ProtocolPath.__protocols__[protocol](path)
        else:
            raise LookupError('Protocol with name "{}" is not registered or unknown'.format(protocol))


def remote_protocol( a, b ):
    '''
    Determine the protocol to use given two paths to files. Return None if
    the two protocols are not compatible.

    :param a: path to the firs file.
    :type a: str
    :param b: path to the second file.
    :type b: str
    :returns: protocol ID.
    :rtype: int
    '''
    if a.is_remote:

        if b.is_remote:

            if a.pid != b.pid:
                return None

        return a.pid

    else:
        return b.pid
