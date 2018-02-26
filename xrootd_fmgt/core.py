'''
Main classes and functions to manage files using the ssh protocol.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Python
import os, subprocess, socket


__all__ = ['FileProxy']


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
        self.targets = targets

        if _is_ssh(self.source):
            if any(_is_xrootd(s) for s in self.targets):
                raise ValueError('Different protocols specified for '\
                                 'source and target files')
        elif _is_xrootd(self.source):
            if any(_is_ssh(s) for s in self.targets):
                raise ValueError('Different protocols specified for '\
                                 'source and target files')

    def path( self ):
        '''
        Get the most accessible path to one of the files in this class.

        :returns: path to the file.
        :rtype: str
        '''
        host = socket.getfqdn()

        if _is_ssh(host):
            for s in self.targets:
                if s.startswith(host):
                    _, path = _split_remote(s)
        else:
            for s in self.targets:
                if not _is_ssh(s):
                    return s

        raise RuntimeError('Unable to find an available path')

    def sync( self, force=False ):
        '''
        Synchronize the target files using the source file.

        :param force: if set to True, the files are copied even if they are \
        up to date.
        :type force: bool
        '''
        itmstp = _get_mtime(self.source)

        if itmstp == None:
            raise RuntimeError('Unable to synchronize file "{}", the '\
                               'file does not exist'.format(target))

        for target in self.targets:

            otmstp = _get_mtime(target)

            if otmstp != itmstp or force:

                # Make the directories if they do not exist
                try:
                    os.makedirs(os.path.dirname(target))
                except:
                    pass

                # Copy the file
                print('Trying to get file from "{}"'.format(self.source))

                if _is_xrootd(self.source) or _is_xrootd(target):
                    proc = subprocess.Popen(
                        ['xrdcp', '-f', '-s', self.source, target],
                        stdout = subprocess.PIPE,
                        stderr = subprocess.PIPE
                    )
                else:
                    proc = subprocess.Popen(
                        ['scp', '-q', self.source, target],
                        stdout = subprocess.PIPE,
                        stderr = subprocess.PIPE
                    )

                print('Output will be copied into "{}"'.format(target))
                exitcode = proc.wait()

                if exitcode != 0:
                    _, stderr = proc.communicate()
                    raise RuntimeError('Problem copying file "{}", Error: '\
                                       '"{}"'.format(self.source, stderr))

                # Change the time stamp of the new file to match that of
                # the remote path
                os.utime(target, (os.stat(target).st_atime, itmstp))

                print('Successfuly copied file')

            else:
                print('File "{}" is up to date'.format(target))


def _get_mtime( path ):
    '''
    Get the modification time for the file in "path".

    :param path: path to the input file.
    :type path: str
    :returns: modification time.
    :rtype: float or None
    '''
    if _is_ssh(path):

        server, sepath = path.split(':')

        tmpstp = subprocess.Popen(['ssh -X', server, 'stat -c%Y', sepath],
                                  stdout = subprocess.PIPE,
                                  stderr = subprocess.PIPE
                                  ).stdout.read()

        return float(tmpstp)

    else:
        if os.path.exists(path):
            return os.path.getmtime(path)
        else:
            return None


def _is_ssh( path ):
    '''
    Return whether the standard ssh protocol must be used.

    :param path: path to the input file.
    :type path: str
    :returns: output decision
    :rtype: bool
    '''
    return '@' in path


def _is_xrootd( path ):
    '''
    Return whether the path is related to the xrootd protocol.

    :param path: path to the input file.
    :type path: str
    :returns: output decision
    :rtype: bool
    '''
    return path.startswith('root://')


def _split_remote( path ):
    '''
    Split a path related to a remote file in site and true path.

    :param path: path to the input file.
    :type path: str
    :returns: site and path to the file in the site.
    :rtype: str, str
    '''
    if _is_ssh(path):
        return path.split(':')
    else:
        rp = path.find('//', 7)
        return path[7:rp], path[rp + 2:]
