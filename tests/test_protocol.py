'''
Test functions for the "protocols" module.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Custom
import hep_rfm


def test_remote_name():
    '''
    Test the remote naming scheme.
    '''

    # XROOTD
    assert hep_rfm.is_xrootd('root://my-site//')

    assert not hep_rfm.is_xrootd('my-site')

    s, p = hep_rfm.core.split_remote('root://my-site//path/to/file')
    assert s == 'my-site' and p == 'path/to/file'

    # SSH
    assert hep_rfm.is_ssh('username@server')

    assert not hep_rfm.is_ssh('username-server')

    s, p = hep_rfm.core.split_remote('user@my-site:path/to/file')
    assert s == 'user@my-site' and p == 'path/to/file'

    # Both
    assert hep_rfm.is_remote('username@server')
    assert hep_rfm.is_remote('root://my-site//path/to/file')
