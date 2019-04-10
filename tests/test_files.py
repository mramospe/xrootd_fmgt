import hep_rfm
import tempfile
import pytest
'''
Test functions for the "files" module.
'''

__author__ = ['Miguel Ramos Pernas']
__email__ = ['miguel.ramos.pernas@cern.ch']

# Python

# Local


def test_fileinfobase():
    '''
    Test for the "FileInfoBase" class.
    '''
    m = hep_rfm.FileMarks(0., 'fid')
    f = hep_rfm.FileInfoBase('dummy', 'my/path', m)

    # It is an inmutable object
    with pytest.raises(AttributeError):
        f.name = 'other'


def test_fileinfo():
    '''
    Test for the "FileInfo" class.
    '''
    f = hep_rfm.FileInfo('dummy', 'my/path')

    # It is an inmutable object
    with pytest.raises(AttributeError):
        f.name = 'new'

    assert f.marks.tmstp == hep_rfm.files.__default_tmstp__
    assert f.marks.fid == hep_rfm.files.__default_fid__
    assert f.is_bare()

    with tempfile.NamedTemporaryFile() as f:

        proxy = hep_rfm.FileInfo.from_name_and_path('dummy', f.name)

        assert proxy.name == 'dummy'
        assert proxy.protocol_path.path == f.name


def test_filemarksbase():
    '''
    Test for the "FileMarksBase" class.
    '''
    m = hep_rfm.FileMarks(0., 'fid')

    # It is an inmutable object
    with pytest.raises(AttributeError):
        m.fid = 'other'


def test_filemarks():
    '''
    Test for the "FileMarks" class.
    '''
    m = hep_rfm.FileMarks()

    assert m.tmstp == hep_rfm.files.__default_tmstp__
    assert m.fid == hep_rfm.files.__default_fid__

    # It is an inmutable object
    with pytest.raises(AttributeError):
        m.fid = 'other'

    m = hep_rfm.FileMarks(0., 'fid')
