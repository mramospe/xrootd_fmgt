'''
Test function for the "core" module.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Custom
import xrootd_fmgt


def test_get_mtime():
    '''
    Create a file and get the modification time.
    '''
    make_fname = lambda i, 'dummy_{}.txt'.format(i)
    fname = 'dummy_0.txt'

    i = 0
    while os.path.exists(fname):
        i += 1
        fname = make_fname(i)

    with open(fname, 'wt') as f:
        xrootd_fmgt._get_mtime(fname(i))

    os.remove(fname)


def test_remote_name():
    '''
    Test the remote naming scheme.
    '''

    # XROOTD
    assert xrootd_fmgt._is_xrootd('root://my-site//')

    assert not xrootd_fmgt._is_xrootd('my-site')

    s, p = xrootd_fmgt.split_remote('root://my-site//path/to/file')
    assert s == 'my-site' and p == 'path/to/file'

    # SSH
    assert xrootd_fmgt._is_ssh('username@server')

    assert not xrootd_fmgt._is_ssh('username-server')

    s, p = xrootd_fmgt.split_remote('user@my-site:path/to/file')
    assert s == 'user@my-site' and p == 'path/to/file'
