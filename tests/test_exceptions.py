'''
Test functions for the "exceptions" module.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Python
import pytest

# Local
import hep_rfm

def test_processerror():
    '''
    Test for the "ProcessError" class.
    '''
    with pytest.raises(hep_rfm.ProcessError):
        raise hep_rfm.ProcessError('message', 'stderr')


def test_copyfileerror():
    '''
    Test for the "Copyfileerror" class.
    '''
    with pytest.raises(hep_rfm.CopyFileError):
        raise hep_rfm.CopyFileError('ipath', 'opath', 'stderr')


def test_makedirserror():
    '''
    Test for the "MakeDirsError" class.
    '''
    with pytest.raises(hep_rfm.MakeDirsError):
        raise hep_rfm.MakeDirsError('target', 'stderr')
