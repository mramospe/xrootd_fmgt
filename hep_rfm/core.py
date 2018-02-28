'''
Main classes and functions to manage files using the ssh protocol.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Custom
from hep_rfm import protocols

# Python
import os, subprocess, socket, warnings


__all__ = [
    'copy_file',
    'FileProxy',
    'getmtime',
    'set_verbose_level'
    ]

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

        for t in self.targets:
            if protocols.is_xrootd(t):
                # The xrootd protocol does not allow to preserve the
                # metadata when copying files.
                warnings.warn('Target "{}" uses xrootd protocol, metadata '\
                                  'will not be updated. The file will always '\
                                  'be updated.'.format(t), Warning)

    def path( self, xrdav=False ):
        '''
        Get the most accessible path to one of the files in this class.

        :param xrdav: whether the xrootd protocol is available in root.
        :type xrdav: bool
        :returns: path to the file.
        :rtype: str
        '''
        host = socket.getfqdn()

        all_paths = list(self.targets)
        all_paths.append(self.source)

        for s in all_paths:

            if protocols.is_ssh(s):

                server, sepath = _split_remote(s)

                if server.endswith(host):
                    return sepath

            elif protocols.is_xrootd(s):
                if xrdav:
                    return s
            else:
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
        if protocols.is_remote(target):

            server, sepath = _split_remote(target)

            dpath = os.path.dirname(sepath)

            if protocols.is_xrootd(target):
                proc = _process('xrd', server, 'mkdir', dpath)
            else:
                proc = _process('ssh', '-X', server, 'mkdir', '-p', dpath)

            if proc.wait() != 0:
                _, stderr = proc.communicate()
                raise RuntimeError('Problem creating directories for "{}", '\
                                       'Error: "{}"'.format(target, stderr))
        else:
            try:
                os.makedirs(os.path.dirname(target))
            except:
                pass

        # Copy the file
        dec = protocols._remote_protocol(source, target)
        if dec == protocols.__different_protocols__:
            # Copy to a temporal file
            if protocols.is_remote(source):
                _, path = _split_remote(source)
            else:
                path = source

            tmp = '/tmp/' + os.path.basename(path)

            copy_file(source, tmp)
            copy_file(tmp, target)
        else:

            _display('Trying to get file from "{}"'.format(source))

            if dec == protocols.__ssh_protocol__:
                proc = _process('scp', '-q', '-p', source, target)
            elif dec == protocols.__xrootd_protocol__:
                proc = _process('xrdcp', '-f', '-s', source, target)
            else:
                proc = _process('cp', '-p', source, target)

            _display('Output will be copied into "{}"'.format(target))

            if proc.wait() != 0:
                _, stderr = proc.communicate()
                raise RuntimeError('Problem copying file "{}", Error: '\
                                       '"{}"'.format(source, stderr))

            if dec == protocols.__xrootd_protocol__ and not protocols.is_xrootd(target):
                # Update the modification time since xrdcp does not
                # preserve it.
                os.utime(target, (os.stat(target).st_atime, itmstp))

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
        print(msg)


def getmtime( path ):
    '''
    Get the modification time for the file in "path". Only the integer part of
    the modification time is used.

    :param path: path to the input file.
    :type path: str
    :returns: modification time.
    :rtype: int or None
    '''
    if protocols.is_remote(path):

        server, sepath = _split_remote(path)

        if protocols.is_ssh(path):
            proc = _process('ssh', '-X', server, 'stat', '-c%Y', sepath)
        else:
            proc = _process('xrd', server, 'stat', sepath)
    else:
        proc = _process('stat', '-c%Y', path)

    if proc.wait() != 0:
        return None

    tmpstp = proc.stdout.read()
    if protocols.is_xrootd(path):
        tmpstp = tmpstp[tmpstp.find('Modtime:') + len('Modtime:'):]

    return int(tmpstp)


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
    if protocols.is_ssh(path):
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
