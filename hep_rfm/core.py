import tempfile
import subprocess
import os
import logging
import hashlib
from hep_rfm.exceptions import CopyFileError, MakeDirsError
from hep_rfm import parallel
from hep_rfm import protocols
'''
Main classes and functions to manage files using the ssh protocol.
'''

__author__ = ['Miguel Ramos Pernas']
__email__ = ['miguel.ramos.pernas@cern.ch']

# Custom

# Python


__all__ = [
    'copy_file',
    'rfm_hash',
]

# Buffer size to be able to hash large files
__buffer_size__ = 10485760  # 10MB


def copy_file(source, target, wdir=None, loglock=None, modifiers=None):
    '''
    Main function to copy a file from a source to a target.
    The copy is done if the modification time of both files do not coincide.
    Since sometimes the files are very large, in this case it is recommendable
    to specify a directory to copy the temporal files "wdir", so files can be
    copied on disk.

    :param source: where to copy the file from.
    :type source: ProtocolPath
    :param target: where to copy the file.
    :type target: ProtocolPath
    :param wdir: where to create the possible temporary directory. The \
    option is passed to :class:`tempfile.TemporaryDirectory` as "dir".
    :type wdir: str
    :param loglock: possible locker to prevent from displaying at the same \
    time in the screen for two different processes.
    :type loglock: multiprocessing.Lock or None
    :param modifiers: dictionary with the information to modify the path \
    of the input :class:`hep_rfm.ProtocolPath` instances.
    :type modifiers: dict
    :raises CopyFileError: if the file can not be copied.

    .. note:: If source and target point to the same file, no copy will be done.
    '''
    # Set the user names if dealing with SSH paths
    source = source.with_modifiers(modifiers)
    target = target.with_modifiers(modifiers)

    # Make the directories to the target
    target.mkdirs()

    # Copy the file
    dec = protocols.remote_protocol(source, target)
    if dec == None:
        # Copy to a temporal file
        if protocols.is_remote(source):
            _, path = source.split_path()
        else:
            path = source.path

        with tempfile.TemporaryDirectory(dir=wdir) as td:

            tmp = protocols.protocol_path(
                os.path.join(td, os.path.basename(path)))

            copy_file(source, tmp)
            copy_file(tmp, target)

    else:
        if os.path.isfile(source.path) and os.path.isfile(target.path) and os.path.samefile(source.path, target.path):
            return

        parallel.log(logging.getLogger(__name__).info,
                     'Copying file\n source: {}\n target: {}'.format(
                         source.path, target.path),
                     loglock)

        protocols.ProtocolPath.__protocols__[dec].copy(source, target)


def rfm_hash(path):
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
