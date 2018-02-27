'''
Test function for the "core" module.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Python
import atexit, os

# Custom
import remfm


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

        remfm.core._get_mtime(fname)


def test_remote_name():
    '''
    Test the remote naming scheme.
    '''

    # XROOTD
    assert remfm.core._is_xrootd('root://my-site//')

    assert not remfm.core._is_xrootd('my-site')

    s, p = remfm.core._split_remote('root://my-site//path/to/file')
    assert s == 'my-site' and p == 'path/to/file'

    # SSH
    assert remfm.core._is_ssh('username@server')

    assert not remfm.core._is_ssh('username-server')

    s, p = remfm.core._split_remote('user@my-site:path/to/file')
    assert s == 'user@my-site' and p == 'path/to/file'
