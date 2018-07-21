'''
Test functions for the "core" module.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Python
import pytest
import tempfile

# Custom
import hep_rfm


def test_copy_file():
    '''
    Tests for the "copy_file" function.
    '''
    with pytest.raises(RuntimeError):
        hep_rfm.copy_file('non-existing-source', 'non-existing-target')

    f = tempfile.NamedTemporaryFile()

    with pytest.raises(hep_rfm.exceptions.MakeDirsError):
        hep_rfm.copy_file(f.name, 'no-user@no-server.com:/path/to/file')


def test_make_directories():
    '''
    Test the "make_directories" function.
    '''
    with pytest.raises(hep_rfm.exceptions.MakeDirsError):
        fp = hep_rfm.make_directories('no-user@no-server.com:/path/to/file')


def test_rfm_hash():
    '''
    Test for the "rfm_hash" function.
    '''
    with tempfile.NamedTemporaryFile() as f:
        h = hep_rfm.rfm_hash(f.name)
