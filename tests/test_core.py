import hep_rfm
import tempfile
import pytest
import os
'''
Test functions for the "core" module.
'''

__author__ = ['Miguel Ramos Pernas']
__email__ = ['miguel.ramos.pernas@cern.ch']

# Python

# Custom


def test_copy_file(tmpdir):
    '''
    Tests for the "copy_file" function.
    '''
    p1 = tmpdir.join('file1.txt')
    p2 = tmpdir.join('file2.txt')

    p1.write('something')

    pp1 = hep_rfm.protocol_path(p1.strpath)
    pp2 = hep_rfm.protocol_path(p2.strpath)

    hep_rfm.copy_file(pp1, pp2, wdir=tmpdir.strpath)

    source = hep_rfm.protocol_path('non-existing-source')
    target = hep_rfm.protocol_path('non-existing-target')

    with pytest.raises(RuntimeError):
        hep_rfm.copy_file(source, target)

    f = tempfile.NamedTemporaryFile()

    source = hep_rfm.protocol_path(f.name)
    target = hep_rfm.protocol_path(
        'no-user@no-server.com:/path/to/file', 'ssh')

    with pytest.raises(hep_rfm.exceptions.MakeDirsError):
        hep_rfm.copy_file(source, target)


def test_rfm_hash():
    '''
    Test for the "rfm_hash" function.
    '''
    with tempfile.NamedTemporaryFile() as f:
        h = hep_rfm.rfm_hash(f.name)
