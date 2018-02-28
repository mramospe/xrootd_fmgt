'''
Test functions for the "core" module.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Python
import atexit, os, pytest, time

# Custom
import hep_rfm


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

    open(fname, 'wt').close()

    return fname


def test_getmtime():
    '''
    Create a file and get the modification time.
    '''
    f = _create_dummy_file()
    hep_rfm.getmtime(f)


def test_file_proxy():
    '''
    Test the behaviours of the FileProxy class.
    '''
    sf = _create_dummy_file()

    # Add 2 seconds of delay between the creation of the two files
    time.sleep(2)

    tf = _create_dummy_file()

    assert str(hep_rfm.getmtime(sf)) != str(hep_rfm.getmtime(tf))

    fp = hep_rfm.FileProxy(sf, tf)
    fp.sync()

    assert str(hep_rfm.getmtime(sf)) == str(hep_rfm.getmtime(tf))

    # Test warning when using xrootd protocol on target files
    with pytest.warns(Warning):
        fp = hep_rfm.FileProxy('/path/to/file', 'root://server//path/to/file')
