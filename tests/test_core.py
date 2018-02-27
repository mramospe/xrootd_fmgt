'''
Test function for the "core" module.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Python
import atexit, os

# Custom
import hep_remfm


def test_get_mtime():
    '''
    Create a file and get the modification time.
    '''
    make_fname = lambda i: 'dummy_{}.txt'.format(i)
    fname = 'dummy_0.txt'

    i = 0
    while os.path.exists(fname):
        i += 1
        fname = make_fname(i)

    with open(fname, 'wt') as f:

        atexit.register(lambda: os.remove(fname))

        hep_remfm.core._get_mtime(fname)


def test_remote_name():
    '''
    Test the remote naming scheme.
    '''

    # XROOTD
    assert hep_remfm.core._is_xrootd('root://my-site//')

    assert not hep_remfm.core._is_xrootd('my-site')

    s, p = hep_remfm.core._split_remote('root://my-site//path/to/file')
    assert s == 'my-site' and p == 'path/to/file'

    # SSH
    assert hep_remfm.core._is_ssh('username@server')

    assert not hep_remfm.core._is_ssh('username-server')

    s, p = hep_remfm.core._split_remote('user@my-site:path/to/file')
    assert s == 'user@my-site' and p == 'path/to/file'
