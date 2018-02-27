'''
Test function for the "core" module.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Python
import atexit, os

# Custom
import hep_remfm


def _create_dummy_file():
    '''
    Create a dummy file.
    '''
    make_fname = lambda i: 'dummy_{}.txt'.format(i)
    fname = 'dummy_0.txt'

    i = 0
    while os.path.exists(fname):
        i += 1
        fname = make_fname(i)

    atexit.register(lambda: os.remove(fname))

    return open(fname, 'wt')


def test_get_mtime():
    '''
    Create a file and get the modification time.
    '''
    with _create_dummy_file() as f:
        hep_remfm.core._get_mtime(f.name)


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


def test_file_proxy():
    '''
    Test the behaviours of the FileProxy class.
    '''
    sf = _create_dummy_file()
    tf = _create_dummy_file()

    fp = hep_remfm.FileProxy(sf.name, tf.name)
    fp.sync()

    assert hep_remfm.core._get_mtime(sf.name) == hep_remfm.core._get_mtime(tf.name)
