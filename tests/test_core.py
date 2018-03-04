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

    open(fname, 'wt').close()

    atexit.register(lambda: os.remove(fname))

    return fname


def test_copy_file():
    '''
    Tests for the "copy_file" function.
    '''
    with pytest.raises(RuntimeError):
        hep_rfm.copy_file('non-existing-source', 'non-existing-target')

    f = _create_dummy_file()

    with pytest.raises(hep_rfm.exceptions.CopyFileError):
        hep_rfm.copy_file(f, 'no-user@no-server.com:/path/to/file')


def test_file_proxy():
    '''
    Test the behaviours of the FileProxy class.
    '''
    with pytest.raises(ValueError):
        hep_rfm.FileProxy('/path/to/file')

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


def test_getmtime():
    '''
    Create a file and get the modification time.
    '''
    f = _create_dummy_file()
    hep_rfm.getmtime(f)


def test_make_directories():
    '''
    Test the "make_directories" function.
    '''
    with pytest.raises(hep_rfm.exceptions.MakeDirsError):
        fp = hep_rfm.make_directories('no-user@no-server.com:/path/to/file')
