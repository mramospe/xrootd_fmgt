'''
Test functions for the "core" module.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Python
import os
import pytest
import tempfile

# Custom
import hep_rfm


def test_copy_file():
    '''
    Tests for the "copy_file" function.
    '''
    with tempfile.TemporaryDirectory() as td:

        p1 = os.path.join(td, 'file1.txt')
        p2 = os.path.join(td, 'file2.txt')

        with open(p1, 'wt') as f1:
            f1.write('something')

        pp1 = hep_rfm.protocol_path(p1)
        pp2 = hep_rfm.protocol_path(p2)

        hep_rfm.copy_file(pp1, pp2, wdir=td)

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
