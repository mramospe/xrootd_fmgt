'''
Test functions for the "protocols" module.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Custom
import hep_rfm


def test_is_remote():
    '''
    Test for the "is_remote" function.
    '''
    assert hep_rfm.is_remote('root://my-site//')
    assert hep_rfm.is_remote('username@server')
    assert not hep_rfm.is_remote('/local/path/file.txt')


def test_is_ssh():
    '''
    Test for the "is_ssh" function.
    '''
    assert not hep_rfm.is_ssh('root://my-site//')
    assert hep_rfm.is_ssh('username@server')
    assert not hep_rfm.is_ssh('/local/path/file.txt')

    s, p = hep_rfm.protocols.split_remote('user@my-site:path/to/file')
    assert s == 'user@my-site' and p == 'path/to/file'


def test_is_xrootd():
    '''
    Test for the "is_xrootd" function.
    '''
    assert hep_rfm.is_xrootd('root://my-site//')
    assert not hep_rfm.is_xrootd('username@server')
    assert not hep_rfm.is_xrootd('/local/path/file.txt')

    s, p = hep_rfm.protocols.split_remote('root://my-site//path/to/file')
    assert s == 'my-site' and p == '/path/to/file'
