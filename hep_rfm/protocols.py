'''
Define functions to manage protocols.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Python
import functools
import logging
import os
import subprocess

# Local
from hep_rfm.fields import function_with_fields
from hep_rfm.exceptions import AbstractMethodError, CopyFileError, MakeDirsError, MustOverrideError
from hep_rfm.parallel import Registry


__all__ = [
    'ProtocolPath',
    'LocalPath',
    'RemotePath',
    'SSHPath',
    'XRootDPath',
    'available_path',
    'available_working_path',
    'is_remote',
    'process',
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
    @functools.wraps(method)
    def wrapper( source, target ):
        '''
        Internal wrapper to copy the file to a target.
        '''
        proc = method(source, target)

        if proc.wait() != 0:
            _, stderr = proc.communicate()
            raise CopyFileError(source.path, target.path, stderr.decode())

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
    @functools.wraps(method)
    def wrapper( self ):
        '''
        Internal wrapper to create the necessary directories to a target.
        '''
        proc = method(self)

        if proc.wait() != 0:
            _, stderr = proc.communicate()
            raise MakeDirsError(self.path, stderr.decode())

    return wrapper


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
        if name in ProtocolPath.__protocols__:
            raise ValueError('Protocol path with name "{}" already exists'.format(name))

        must_override = (
            (ProtocolPath, ProtocolPath.copy),
            (ProtocolPath, ProtocolPath.mkdirs),
            )

        if issubclass(protocol, RemotePath):
            must_override += (
                (RemotePath, RemotePath.join_path),
                (RemotePath, RemotePath.split_path),
                )
        elif issubclass(protocol, ProtocolPath):
            pass
        else:
            raise RuntimeError('Attempt to register a protocol path that does not inherit from ProtocolPath')

        for c, m in must_override:
            if getattr(protocol, m.__name__) == m:
                raise MustOverrideError(protocol, c, m)

        # Apply the decorators
        protocol.copy   = decorate_copy(protocol.copy)
        protocol.mkdirs = decorate_mkdirs(protocol.mkdirs)

        # Add protocol to dictionary
        ProtocolPath.__protocols__[name] = protocol
        protocol.pid = name

        return protocol

    return wrapper


class ProtocolPath(object):

    # All protocols must have a protocol ID.
    __protocols__ = Registry()

    def __init__( self, path, path_checker = None ):
        '''
        Base class to represent a protocol to manage a path to a file.
        The protocol IDs are defined at runtime, using
        :func:`ProtocolPath.register_protocol`.
        These IDs are saved in the registered classes on the attribute
        "pid".
        It is very important not to ovewrite this value, since it would
        lead to undefined behaviour.
        The protocols are saved on a dictionary, where the keys are the
        protocol IDs.
        This is an abstract class, and any class inheriting from it must
        override the following methods:
        1. :func:`ProtocolPath.copy`
        2. :func:`ProtocolPath.mkdirs`

        :param path: path to save, pointing to a file.
        :type path: str
        :param path_checker: possible function that checks the the given path \
        actually corresponds to the protocol. It must take a path as argument \
        and return a bool.
        :type path_checker: function
        :raises ValueError: if the path does not satisfy the requirements \
        from "path_checker".
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

    @staticmethod
    def copy( source, target ):
        '''
        Copy the source file to the target using this protocol.
        The target must be accessible.
        It must return a :class:`subprocess.Popen` object.
        In this case, this is an abstract method.

        :param source: source file to copy.
        :type source: ProtocolPath
        :param target: path where to copy the file to.
        :type target: ProtocolPath
        :returns: running process copying the file in the current location \
        to the target.
        :rtype: subprocess.Popen
        '''
        raise AbstractMethodError()

    def mkdirs( self ):
        '''
        Make directories to the file path within this protocol.
        It must return a :class:`subprocess.Popen` object.
        In this case, this is an abstract method.

        :returns: running process to make the necessary directories to the \
        target.
        :rtype: subprocess.Popen
        '''
        raise AbstractMethodError()

    @property
    def path( self ):
        '''
        Return the associated path to the file.

        :returns: associated path.
        :rtype: str
        '''
        return self._path

    def with_modifiers( self, modifiers = None ):
        '''
        Return an instance of this class after applying modifications.
        The input dictionary can contain information not understood for a given
        :class:`hep_rfm.ProtocolPath`.
        By default the same class, with no modifications, is returned.

        :param modifiers: information to modify the path of this class.
        :type modifiers: dict
        :returns: modified instance if a modification is applied. Otherwise \
        same instance.
        :rtype: ProtocolPath
        '''
        return self


class RemotePath(ProtocolPath):

    def __init__( self, path, path_checker = None ):
        '''
        Represent a remote path.
        This is an abstract class, any class inheriting from it must override
        the following methods:
        1. :func:`ProtocolPath.copy`
        2. :func:`RemotePath.join_path` (must be decorated with :func:`staticmethod`)
        4. :func:`ProtocolPath.mkdirs`
        5. :func:`RemotePath.split_path`

        :param path: path to save, pointing to a file.
        :type path: str
        :param path_checker: possible function that checks the the given path \
        actually corresponds to the protocol. It must take a path as argument \
        and return a bool.
        :type path_checker: function
        :raises ValueError: if the path does not satisfy the requirements \
        from "path_checker".
        '''
        super(RemotePath, self).__init__(path, path_checker)

    @staticmethod
    def join_path( prefix, path ):
        '''
        Policy to merge a prefix and a path in this protocol.
        In this case, this is an abstract method.

        :param prefix: prefix to add to the current path.
        :type prefix: str
        :param path: path to the file in the remote.
        :type path: str
        :returns: result of joining the prefix and the path for this protocol.
        :rtype: str
        '''
        raise AbstractMethodError()

    def split_path( self ):
        '''
        Split the remote path in the server specifications and path in the
        server.
        In this case, this is an abstract method.
        '''
        raise AbstractMethodError()


@register_protocol('local')
class LocalPath(ProtocolPath):

    def __init__( self, path ):
        '''
        Represent a path to a local file.

        :param path: path to save, pointing to a file.
        :type path: str
        '''
        super(LocalPath, self).__init__(path)

    @staticmethod
    def copy( source, target ):
        '''
        Copy the source file to the target using this protocol.
        The target must be accessible.

        :param source: source file to copy.
        :type source: ProtocolPath
        :param target: where to copy the file.
        :type target: ProtocolPath
        :raises CopyFileError: if a problem appears while copying the file.
        '''
        return process('cp', source.path, target.path)

    def mkdirs( self ):
        '''
        Make directories to the file path within this protocol.

        :raises MakeDirsError: if an error occurs while creating directories.
        '''
        dpath = os.path.dirname(self.path)

        return process('mkdir', '-p', dpath if dpath != '' else './')


@register_protocol('ssh')
class SSHPath(RemotePath):

    def __init__( self, path ):
        '''
        Represent a path to be handled using SSH.

        :param path: path to save, pointing to a file.
        :type path: str
        '''
        if '@' not in path:
            raise ValueError('Path "{}" is not a valid SSH path'.format(path))

        super(SSHPath, self).__init__(path, lambda p: ('@' in p))

    @staticmethod
    def copy( source, target ):
        '''
        Copy the source file to the target using this protocol.
        The target must be accessible.

        :param source: source file to copy.
        :type source: ProtocolPath
        :param target: where to copy the file.
        :type target: ProtocolPath
        :raises CopyFileError: if a problem appears while copying the file.
        '''
        return process('scp', '-q', source.path, target.path)

    @staticmethod
    def join_path( prefix, path ):
        '''
        Policy to merge a prefix and a path in this protocol.

        :param prefix: prefix to add to the current path.
        :type prefix: str
        :param path: path to the file in the remote.
        :type path: str
        :returns: result of joining the prefix and the path for this protocol.
        :rtype: str
        '''
        return prefix + ':' + path

    def mkdirs( self ):
        '''
        Make directories to the file path within this protocol.

        :raises MakeDirsError: if an error occurs while creating directories.
        '''
        server, sepath = self.split_path()

        dpath = os.path.dirname(sepath)

        return process('ssh', '-X', server, 'mkdir', '-p', dpath)

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

    def with_modifiers( self, modifiers = None ):
        '''
        Return an instance of this class after applying modifications.
        The input dictionary "modifiers" might contain information about the
        user-name for the host in the stored path.
        The allowed keys for this dictionary are:
        - "ssh_hosts": list containing the hosts accessible from the place
        where the operation is being done. If the path stored in this class
        has a host that coincides with any of those here specified, it will
        return a :class:`hep_rfm.LocalPath` instance.
        - "ssh_usernames": dictionary containing the user-name to use for each
        host (although only one will be appliable for a given
        :class:`hep_rfm.SSHPath` instance). In case the path has already one
        user-name defined, it will be overwritten.

        :param modifiers: information to modify the path of this class.
        :type modifiers: dict
        :returns: modified instance if a modification is applied. Otherwise \
        same instance.
        :rtype: ProtocolPath
        '''
        modifiers = modifiers if modifiers is not None else {}

        path = self.path

        if modifiers:

            uh, p = self.split_path()

            _, h = uh.split('@')

            if 'ssh_hosts' in modifiers:
                for host in modifiers['ssh_hosts']:
                    if host == h:
                        return LocalPath(p)

            if 'ssh_usernames' in modifiers:
                for host, uname in modifiers['ssh_usernames'].items():
                    if host == h:
                        path = uname + path[path.find('@'):]
                        break

        if path.startswith('@'):
            raise RuntimeError('User name must be specified for "{}"'.format(self))

        return self.__class__(path)


@register_protocol('xrootd')
class XRootDPath(RemotePath):

    def __init__( self, path ):
        '''
        Represent a path to be handled using XROOTD protocol.

        :param path: path to save, pointing to a file.
        :type path: str
        '''
        super(XRootDPath, self).__init__(path, lambda p: p.startswith('root://'))

    @staticmethod
    def copy( source, target ):
        '''
        Copy the source file to the target using this protocol.
        The target must be accessible.

        :param source: source file to copy.
        :type source: ProtocolPath
        :param target: where to copy the file.
        :type target: ProtocolPath
        :raises CopyFileError: if a problem appears while copying the file.
        '''
        return process('xrdcp', '-f', '-s', source.path, target.path)

    @staticmethod
    def join_path( prefix, path ):
        '''
        Policy to merge a prefix and a path in this protocol.

        :param prefix: prefix to add to the current path.
        :type prefix: str
        :param path: path to the file in the remote.
        :type path: str
        :returns: result of joining the prefix and the path for this protocol.
        :rtype: str
        '''
        while prefix.endswith('/'):
            prefix = prefix[:-1]

        while path.startswith('/'):
            path = path[1:]

        return prefix + '//' + path

    def mkdirs( self ):
        '''
        Make directories to the file path within this protocol.

        :raises MakeDirsError: if an error occurs while creating directories.
        '''
        server, sepath = self.split_path()

        dpath = os.path.dirname(sepath)

        return process('xrd', server, 'mkdir', dpath)

    def split_path( self ):
        '''
        Split the remote path in the server specifications and path in the
        server.

        :returns: server specifications and path in the server.
        :rtype: str, str
        '''
        rp = self.path.find('//', 7)
        return self.path[7:rp], self.path[rp + 1:]

    def with_modifiers( self, modifiers = None ):
        '''
        Return an instance of this class after applying modifications.
        The input dictionary "modifiers" might contain information about the
        user-name for the host in the stored path.
        The allowed keys for this dictionary are:
        - "xrootd_servers": list containing the XRootD servers accessible from
        the place where the operation is being done. If the path stored in this
        class has a host that coincides with any of those here specified, it
        will return a :class:`hep_rfm.LocalPath` instance.

        :param modifiers: information to modify the path of this class.
        :type modifiers: dict
        :returns: modified instance if a modification is applied. Otherwise \
        same instance.
        :rtype: ProtocolPath
        '''
        modifiers = modifiers if modifiers is not None else {}

        if modifiers:

            h, p = self.split_path()

            if 'xrootd_servers' in modifiers:
                for server in modifiers['xrootd_servers']:
                    if server == h:
                        return LocalPath(p)

        return self.__class__(self.path)


def available_working_path( path, modifiers = None, allow_protocols = None ):
    '''
    If an accessible path can be resolved from "path", it returns it.
    Return None otherwise.
    If "path" is remote, then "allow_protocols" permits the user to make
    this function return a path if it belongs to one of the given
    protocols, that must be specified as a container of strings.

    :param path: path to process.
    :type path: ProtocolPath
    :param modifiers: modifiers to be applied in the set of paths.
    :type modifiers: dict
    :param allow_protocols: possible protocols to consider.
    :type allow_protocols: container(str)
    :returns: local path.
    :rtype: str or None
    '''
    if modifiers is not None:
        path = path.with_modifiers(modifiers)

    if allow_protocols is not None:
        if path.pid in allow_protocols:
            return path.path

    if is_remote(path):

        server, sepath = path.split_path()

        if os.path.exists(sepath):
            # Local and remote hosts are the same
            return sepath

    else:
        if os.path.exists(path.path):
            return path.path

    return None


def available_path( paths, modifiers = None, allow_protocols = None ):
    '''
    Return the first available path from a list of paths.
    If a local path results after applying "modifiers" to any of the
    given paths, then this is returned (as a local path).
    If any of the paths in "paths" is remote, then "allow_protocols" permits
    the user to make this function return a path if it belongs to one of the
    given protocols, that must be specified as a container of strings.
    The first matching path will be returned.

    :param paths: list of paths to process.
    :type paths: collection(ProtocolPath)
    :param modifiers: modifiers to be applied in the set of paths.
    :type modifiers: dict
    :param allow_protocols: possible protocols to consider.
    :type allow_protocols: container(str)
    :returns: first available path found.
    :rtype: str
    :raises RuntimeError: if it fails to find an available path.

    .. seealso:: :func:`available_working_path`

    .. warning::
       If the path to a file on a remote site matches that of a local file,
       it will be returned. This allows to use local files while specifying
       remote paths. However, if a path on a remote site matches a local
       file, which does not correspond to a proxy of the path referenced by
       this object, it will result on a fake reference to the file.
    '''
    for path in paths:

        p = available_working_path(path, modifiers, allow_protocols)

        if p is not None:
            return p

    raise RuntimeError('Unable to find an available path')


def is_remote( path ):
    '''
    Return whether the given protocol path belongs to a remote protocol or not.

    :param path: protocol path to process.
    :type path: ProtocolPath
    :returns: whether the protocol is local (True in this case).
    :rtype: bool
    '''
    return issubclass(path.__class__, RemotePath)


def process( *args ):
    '''
    Create a subprocess object where the output from "stdout" and "stderr"
    is redirected to subprocess.PIPE.

    :param args: set of commands to call.
    :type args: tuple
    :returns: subprocess applying the given commands.
    :rtype: subprocess.Popen
    '''
    return subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE )


def protocol_path( path, protocol = None ):
    '''
    Return a instantiated protocol using the given path and protocol ID.
    If None is provided for "protocol", then a :class:`LocalPath` will
    be used.

    :param path: path to process.
    :type path: ProtocolPath
    :param protocol: protocol ID to use.
    :type protocol: str
    :returns: protocol associated to the given path.
    :rtype: ProtocolPath
    '''
    if protocol is None:
        return LocalPath(path)
    else:
        if protocol in ProtocolPath.__protocols__:
            return ProtocolPath.__protocols__[protocol](path)
        else:
            raise LookupError('Protocol with name "{}" is not registered or unknown'.format(protocol))


@function_with_fields(['path', 'pid'])
def protocol_path_from_fields( **fields ):
    '''
    Return an instantiated protocol from a set of fields, which
    might or not coincide with those in the class constructor.

    :param fields: fields to process.
    :type fields: dict
    :returns: protocol associated to the given path.
    :rtype: ProtocolPath

    .. seealso:: :func:`hep_rfm.protocol_path`
    '''
    return protocol_path(fields['path'], fields['pid'])


def remote_protocol( a, b ):
    '''
    Determine the protocol to use given two paths to files. Return None if
    the two protocols are not compatible.

    :param a: path to the firs file.
    :type a: str
    :param b: path to the second file.
    :type b: str
    :returns: protocol ID.
    :rtype: int or None
    '''
    if is_remote(a):

        if is_remote(b):

            if a.pid != b.pid:
                return None

        return a.pid

    else:
        return b.pid
