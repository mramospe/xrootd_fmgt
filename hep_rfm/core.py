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
import tempfile


__all__ = [
    'copy_file',
    'rfm_hash',
    ]

# Buffer size to be able to hash large files
__buffer_size__ = 10485760 # 10MB


def copy_file( source, target, wdir=None, loglock=None, modifiers=None ):
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
                     'Copying file\n source: {}\n target: {}'.format(source.path, target.path),
                     loglock)

        protocols.ProtocolPath.__protocols__[dec].copy(source, target)


def parse_fields( expected, inputs, required = 'all' ):
    '''
    Process two sets of fields, one representing the expected and
    the other those to be used for building a class.
    In case one of the expected fields is not present in the inputs,
    if "required" is set to "all" or the name of the field appears
    in it, a :class:`ValueError` will be raised; otherwise a
    warning is displayed, and the corresponding default value is assumed
    to be used.
    On the other hand, if one of the fields in the inputs does not appear
    in those expected it is omitted, displaying also a warning.

    :param expected: fields expected by a function.
    :type expected: container
    :param inputs: fields provided to the function.
    :type inputs: container
    :raises ValueError: if one of the expected fields is not found in the \
    inputs, and "required" is "all" or the name of the field appears in it.
    '''
    for f in set(expected).difference(inputs):
        if required == 'all' or f in required:
            raise ValueError('Required field "{}" is not present; incompatible version'.format(f))
        else:
            logging.getLogger(__name__).warning('Value for field "{}" not found; setting to default value'.format(f))

    for f in set(inputs).difference(expected):
        logging.getLogger(__name__).warning('Field "{}" not found; ignoring it'.format(f))


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
