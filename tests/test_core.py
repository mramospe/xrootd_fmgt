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
    source = hep_rfm.protocol_path('non-existing-source')
    target = hep_rfm.protocol_path('non-existing-target')

    with pytest.raises(RuntimeError):
        hep_rfm.copy_file(source, target)

    f = tempfile.NamedTemporaryFile()

    source = hep_rfm.protocol_path(f.name)
    target = hep_rfm.protocol_path('no-user@no-server.com:/path/to/file', 'ssh')

    with pytest.raises(hep_rfm.exceptions.MakeDirsError):
        hep_rfm.copy_file(source, target)


def test_rfm_hash():
    '''
    Test for the "rfm_hash" function.
    '''
    with tempfile.NamedTemporaryFile() as f:
        h = hep_rfm.rfm_hash(f.name)
