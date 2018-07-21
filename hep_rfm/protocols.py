'''
Define functions to manage protocols.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Python
import logging
import os

__all__ = [
    'is_remote',
    'is_ssh',
    'is_xrootd'
    ]

# Definition of the protocols to use
__local_protocol__      = 1
__ssh_protocol__        = 2
__xrootd_protocol__     = 3
__different_protocols__ = 4


def available_path( paths, use_xrd=False ):
    '''
    Return the first available path from a list of paths. If "use_xrd" is
    set to True, then this also stands for any path using the XRootD
    protocol (by default they are avoided).

    :param paths: list of paths to process.
    :type paths: collection(str)
    :param use_xrd: whether using XRootD protocol is allowed.
    :type use_xrd: bool
    :returns: first available path found.
    :rtype: str

    .. warning::
       If the path to a file on a remote site matches that of a local file,
       it will be returned. This allows to use local files while specifying
       remote paths. However, if a path on a remote site matches a local
       file, which does not correspond to a proxy of the path referenced by
       this object, it will result on a fake reference to the file.
    '''
    path = None
    for s in paths:

        if is_remote(s):

            server, sepath = split_remote(s)

            if is_xrootd(s):
                if use_xrd:
                    # Using XRootD protocol is allowed
                    path = s

            if os.path.exists(sepath):
                # Local and remote hosts are the same
                path = sepath

        else:
            if os.path.exists(s):
                path = s

        if path is not None:
            break

    if path is not None:
        logging.getLogger(__name__).info('Using path "{}"'.format(path))
        return path

    raise RuntimeError('Unable to find an available path')


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


def remote_protocol( a, b ):
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


def split_remote( path ):
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
        return path[7:rp], path[rp + 1:]
