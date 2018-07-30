'''
Main classes and functions to manage files using the ssh protocol.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Custom
from hep_rfm import protocols
from hep_rfm import parallel
from hep_rfm.exceptions import CopyFileError, MakeDirsError

# Python
import hashlib
import logging
import os
import subprocess


__all__ = [
    'copy_file',
    'make_directories',
    'rfm_hash',
    ]

# Buffer size to be able to hash large files
__buffer_size__ = 10485760 # 10MB


def copy_file( source, target, loglock=None, server_spec=None ):
    '''
    Main function to copy a file from a source to a target. The copy is done
    if the modification time of both files do not coincide.

    :param loglock: possible locker to prevent from displaying at the same \
    time in the screen for two different processes.
    :type loglock: multiprocessing.Lock or None
    :param server_spec: specification of user for each SSH server. Must \
    be specified as a dictionary, where the keys are the hosts and the \
    values are the user names.
    :type server_spec: dict
    :raises CopyFileError: if the file can not be copied.
    '''
    # Set the user names if dealing with SSH paths
    if protocols.is_ssh(source):
        source = _set_username(source, server_spec)

    if protocols.is_ssh(target):
        target = _set_username(target, server_spec)

    # Make the directories to the target
    make_directories(target)

    # Copy the file
    dec = protocols.remote_protocol(source, target)
    if dec == protocols.__different_protocols__:
        # Copy to a temporal file
        if protocols.is_remote(source):
            _, path = protocols.split_remote(source)
        else:
            path = source

        with tempfile.TemporaryDirectory() as tmpdir:

            tmp = os.path.join(tmpdir, os.path.basename(path))

            copy_file(source, tmp)
            copy_file(tmp, target)

    else:
        parallel.log(logging.getLogger(__name__).info,
                     'Copying file\n source: {}\n target: {}'.format(source, target),
                     loglock)

        if dec == protocols.__ssh_protocol__:
            proc = _process('scp', '-q', source, target)
        elif dec == protocols.__xrootd_protocol__:
            proc = _process('xrdcp', '-f', '-s', source, target)
        else:
            proc = _process('cp', source, target)

        if proc.wait() != 0:
            _, stderr = proc.communicate()
            raise CopyFileError(source, target, stderr.decode())


def make_directories( target ):
    '''
    Make the directories for the given target in case they do not exist already.

    :param target: path to a target file.
    :type target: str
    :raises MakeDirsError: if the directory could not be created.
    '''
    if protocols.is_remote(target):

        server, sepath = protocols.split_remote(target)

        dpath = os.path.dirname(sepath)

        if protocols.is_xrootd(target):
            proc = _process('xrd', server, 'mkdir', dpath)
        else:
            proc = _process('ssh', '-X', server, 'mkdir', '-p', dpath)

    else:

        dpath = os.path.dirname(target)

        proc = _process('mkdir', '-p', dpath if dpath != '' else './')

    if proc.wait() != 0:

        _, stderr = proc.communicate()

        raise MakeDirsError(target, stderr.decode())


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


def rfm_hash( path ):
    '''
    Use the SHA512 hash function to get the file ID of the file
    in the given path.
    This is achieved by reading the file in binary mode, evaluating
    the hash in chunks of 10 MB, adding them and converting the
    result to hexadecimal.

    :param path: path to the file.
    :type path: str
    :returns: hexadecimal result of evaluating the hash function.
    :rtype: str
    '''
    h = hashlib.sha512()

    with open(path, 'rb') as f:

        # Read in chunks so we do not run out of memory
        while True:

            d = f.read(__buffer_size__)
            if not d:
                break

            h.update(d)

    return h.hexdigest()


def _set_username( path, server_spec=None ):
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
    :raises RuntimeError: if there is no way to determine the user name for \
    the given path.
    '''
    server_spec = server_spec if server_spec is not None else {}

    l = path.find('@')

    if l == 0 and server_spec is None:
        raise RuntimeError('User name not specified for path "{}"'.format(path))

    uh, _ = protocols.split_remote(path)

    u, h = uh.split('@')

    for host, uname in server_spec.items():

        if host == h:
            path = uname + path[l:]
            break

    if path.startswith('@'):
        raise RuntimeError('Unable to find a proper user name for path "{}"'.format(path))

    return path
