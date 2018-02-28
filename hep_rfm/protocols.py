'''
Define functions to manage protocols.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

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
