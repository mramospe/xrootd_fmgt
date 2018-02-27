'''
Main classes and functions to manage files using the ssh protocol.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Python
import os, subprocess, socket


__all__ = [
    'copy_file',
    'FileProxy',
    'getmtime',
    'is_remote',
    'is_ssh',
    'is_xrootd',
    'set_verbose_level'
    ]

# Definition of the protocols to use
__local_protocol__       = 1
__ssh_protocol__         = 2
__xrootd_protocol__      = 3
__different_protocols__  = 4

# Verbose level
__verbose_level__ = 1


class FileProxy:
    '''
    Object to store the path to a set of files, linked together, where one is
    used to update the others.
    '''
    def __init__( self, source, *targets ):
        '''
        Build a proxy to a file.

        :param source: path to the file to use as a reference.
        :type source: str
        :param targets: path to some other locations to put the target files.
        :type targets: list(str)
        '''
        if len(targets) == 0:
            raise ValueError('At least one target file path must be specified')

        self.source  = source
        self.targets = list(targets)

    def path( self ):
        '''
        Get the most accessible path to one of the files in this class.

        :returns: path to the file.
        :rtype: str
        '''
        host = socket.getfqdn()

        if is_ssh(host):
            for s in self.targets:
                if s.startswith(host):
                    _, path = _split_remote(s)
        else:
            for s in self.targets:
                if not is_ssh(s):
                    return s

        raise RuntimeError('Unable to find an available path')

    def set_username( self, uname, host=None ):
        '''
        Assign the user name "uname" to the source and targets with
        host equal to "host", and which do not have a user name yet.

        :param source: path to a file.
        :type source: str
        :param uname: user name.
        :type uname: str
        :param host: host name.
        :type host: str or None
        '''
        self.source = _set_username(self.source, uname, host)
        for i, t in enumerate(self.targets):
            self.targets[i] = _set_username(t, uname, host)

    def sync( self, **kwargs ):
        '''
        Synchronize the target files using the source file.

        :param kwargs: extra arguments to :func:`copy_file`.
        :type kwargs: dict
        '''
        for target in self.targets:
            copy_file(self.source, target, **kwargs)


def copy_file( source, target, force=False ):
    '''
    Main function to copy a file from a source to a target. The copy is done
    if the modification time of both files do not coincide. If "force" is
    specified, then the copy is done independently on this.

    :param force: if set to True, the files are copied even if they are \
    up to date.
    :type force: bool
    '''
    itmstp = getmtime(source)

    if itmstp == None:
        raise RuntimeError('Unable to synchronize file "{}", the '\
                               'file does not exist'.format(source))

    if getmtime(target) != itmstp or force:

        # Make the directories if they do not exist
        if is_remote(target):

            server, sepath = _split_remote(target)

            dpath = os.path.dirname(sepath)

            if is_xrootd(target):
                proc = _process('xrd', server, 'mkdir', dpath)
            else:
                proc = _process('ssh', '-X', server, 'mkdir', '-p', dpath)

            exitcode = proc.wait()
            if exitcode != 0:
                _, stderr = proc.communicate()
                raise RuntimeError('Problem creating directories for "{}", '\
                                       'Error: "{}"'.format(target, stderr))
        else:
            try:
                os.makedirs(os.path.dirname(target))
            except:
                pass

        # Copy the file
        dec = _remote_protocol(source, target)
        if dec == __different_protocols__:
            # Copy to a temporal file
            if is_remote(source):
                _, path = _split_remote(source)
            else:
                path = source

            tmp = '/tmp/' + os.path.basename(path)

            copy_file(source, tmp)
            copy_file(tmp, target)
        else:

            _display('Trying to get file from "{}"'.format(source))

            if dec == __ssh_protocol__:
                proc = _process('scp', '-q', '-p', source, target)
            elif dec == __xrootd_protocol__:
                proc = _process('xrdcp', '-f', '-s', source, target)
            else:
                proc = _process('cp', '-p', source, target)


            _display('Output will be copied into "{}"'.format(target))

            exitcode = proc.wait()
            if exitcode != 0:
                _, stderr = proc.communicate()
                raise RuntimeError('Problem copying file "{}", Error: '\
                                       '"{}"'.format(source, stderr))

            _display('Successfuly copied file')

    else:
        _display('File "{}" is up to date'.format(target))


def _display( msg ):
    '''
    Display the given message taking into account the verbose level.

    :param msg: message to display.
    :type msg: str
    '''
    if __verbose_level__:
        print msg


def getmtime( path ):
    '''
    Get the modification time for the file in "path".

    :param path: path to the input file.
    :type path: str
    :returns: modification time.
    :rtype: float or None
    '''
    if is_ssh(path):

        server, sepath = _split_remote(path)

        tmpstp = _process('ssh', '-X', server, 'stat', '-c%Y', sepath).stdout.read()

        try:
            return float(tmpstp)
        except:
            return None

    elif is_xrootd(path):

        server, sepath = _split_remote(path)

        tmpstp = _process('xrd', server, 'stat', sepath).stdout.read()

        try:
            return float(tmpstp[tmpstp.find('Modtime:') + len('Modtime:'):])
        except:
            return None

    else:
        if os.path.exists(path):
            return os.path.getmtime(path)
        else:
            return None


def is_remote( path ):
    '''
    Check whether the given path points to a remote file.

    :param path: path to the input file.
    :type path: str
    :returns: output decision.
    :rtype: bool
    '''
    return is_ssh(path) or is_xrootd(path)


def is_ssh( path ):
    '''
    Return whether the standard ssh protocol must be used.

    :param path: path to the input file.
    :type path: str
    :returns: output decision
    :rtype: bool
    '''
    return '@' in path


def is_xrootd( path ):
    '''
    Return whether the path is related to the xrootd protocol.

    :param path: path to the input file.
    :type path: str
    :returns: output decision
    :rtype: bool
    '''
    return path.startswith('root://')


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
                             stderr = subprocess.PIPE)


def _remote_protocol( a, b ):
    '''
    Determine the protocol to use given two paths to files. The protocol IDs
    are defined as:
    - 1: local
    - 2: ssh
    - 3: xrootd
    - 4: different protocols ("a" and "b" are accessed using different \
    protocols)

    :param a: path to the firs file.
    :type a: str
    :param b: path to the second file.
    :type b: str
    :returns: protocol ID.
    :rtype: int
    '''
    if is_ssh(a) and is_xrootd(b):
        return __different_protocols__
    elif is_xrootd(a) and is_ssh(b):
        return __different_protocols__
    elif is_ssh(a) or is_ssh(b):
        return __ssh_protocol__
    elif is_xrootd(a) or is_xrootd(b):
        return __xrootd_protocol__
    else:
        return __local_protocol__


def _set_username( source, uname, host=None ):
    '''
    Return a modified version of "source" in case it contains the
    given host. If no host is provided, then the user name will be
    set unless "source" has already defined one.

    :param source: path to a file.
    :type source: str
    :param uname: user name.
    :type uname: str
    :param host: host name.
    :type host: str or None
    :returns: modified version of "source".
    :rtype: str
    '''
    if source.startswith('@'):

        if host is None:
            return uname + source
        else:
            if source[1:].startswith(host):
                return uname + source

    return source


def _split_remote( path ):
    '''
    Split a path related to a remote file in site and true path.

    :param path: path to the input file.
    :type path: str
    :returns: site and path to the file in the site.
    :rtype: str, str
    '''
    if is_ssh(path):
        return path.split(':')
    else:
        rp = path.find('//', 7)
        return path[7:rp], path[rp + 2:]


def set_verbose_level( lvl ):
    '''
    Set the verbose level in this package.

    :param lvl: verbose level.
    :type lvl: int
    '''
    global __verbose_level__

    available = (0, 1)
    if lvl not in available:
        raise ValueError('Verbose level must be in {}'.format(available))

    __verbose_level__ = lvl
