'''
Test functions for the "protocols" module.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Python
import os
import pytest

# Custom
import hep_rfm


def test_available_path( tmpdir ):
    '''
    Test for the "available_path" function.
    '''
    lp = tmpdir.join('file.txt').strpath

    local_path = hep_rfm.protocol_path(lp)

    with open(local_path.path, 'wt') as f:
        f.write('something')

    xr = 'root://my-site//file.txt'
    xrootd_path = hep_rfm.protocol_path(xr, 'xrootd')

    paths = [xrootd_path, local_path]

    p = hep_rfm.available_path(paths)
    assert p.path == lp

    p = hep_rfm.available_path(paths, use_xrd=True)
    assert p.path == xr

    with pytest.raises(RuntimeError):
        hep_rfm.available_path(paths[:-1])


def test_available_local_path( tmpdir ):
    '''
    Test for the "available_local_path" function.
    '''
    local_path = hep_rfm.protocol_path(tmpdir.join('file.txt').strpath)

    with open(local_path.path, 'wt') as f:
        f.write('something')

    nlocal_path = hep_rfm.protocol_path('non-existing-file.txt')
    xrootd_path = hep_rfm.protocol_path('root://my-site//file.txt', 'xrootd')
    ssh_path    = hep_rfm.protocol_path('user@host:/file.txt', 'ssh')

    assert hep_rfm.available_local_path(local_path)
    assert not hep_rfm.available_local_path(nlocal_path)
    assert hep_rfm.available_local_path(xrootd_path, use_xrd=True)
    assert not hep_rfm.available_local_path(xrootd_path)
    assert not hep_rfm.available_local_path(ssh_path)


def test_protocol_path():
    '''
    Test for the "protocol_path" function.
    '''
    for path, protocol in (
            ('/local/path/file.txt', 'local'),
            ('root://my-site//file.txt', 'xrootd'),
            ('user@host:/file.txt', 'ssh'),
            ):
        p = hep_rfm.protocol_path(path, protocol)


def test_protocolpath():
    '''
    Test for the "ProtocolPath" class.
    '''
    path = '/local/path/file.txt'

    pp1 = hep_rfm.ProtocolPath(path)

    assert pp1.path == path

    pp2 = hep_rfm.ProtocolPath(path)

    assert pp1 == pp2


def test_localpath( tmpdir ):
    '''
    Test for the "LocalPath" class.
    '''
    path = tmpdir.join('subdir/file.txt')
    pp = hep_rfm.protocol_path(path.strpath)

    assert pp.pid == 'local'
    assert pp.path == path
    assert not pp.is_remote

    pp.mkdirs()

    assert os.path.isdir(os.path.dirname(pp.path))


def test_register_protocol():
    '''
    Test for the "register_protocol" decorator.
    '''
    @hep_rfm.register_protocol('special-protocol')
    class SpecialPath(hep_rfm.ProtocolPath):
        def check_path( path ):
            return False

    assert SpecialPath('/local/file.txt').pid == 'special-protocol'

    with pytest.raises(RuntimeError):
        # Does not inherit from ProtocolPath
        @hep_rfm.register_protocol('another-protocol')
        class AnotherPath(object):
            pass

    with pytest.raises(ValueError):
        # There is already a protocol path with that name
        @hep_rfm.register_protocol('special-protocol')
        class SpecialPath(hep_rfm.ProtocolPath):
            pass


def test_remotepath():
    '''
    Test for the "RemotePath" class.
    '''
    path = 'user@host:/file.txt'

    pp = hep_rfm.RemotePath(path)

    assert pp.path == path


def test_remote_paths():
    '''
    Test for the "is_remote" method in ProtocolPath classes.
    '''
    remotes = (
        hep_rfm.protocol_path('root://my-site//', 'xrootd'),
        hep_rfm.protocol_path('username@server', 'ssh'),
        )

    for r in remotes:
        assert r.is_remote

    assert not hep_rfm.protocol_path('/local/path/file.txt').is_remote


def test_remote_protocol():
    '''
    Test for the "remote_protocol" function.
    '''
    local  = hep_rfm.protocol_path('/local/path/file.txt')
    ssh    = hep_rfm.protocol_path('user@host:/file.txt', 'ssh')
    xrootd = hep_rfm.protocol_path('root://server//file.txt', 'xrootd')

    assert hep_rfm.remote_protocol(local, local) == 'local'
    assert hep_rfm.remote_protocol(local, ssh) == 'ssh'
    assert hep_rfm.remote_protocol(local, xrootd) == 'xrootd'
    assert hep_rfm.remote_protocol(ssh, xrootd) == None


def test_sshpath():
    '''
    Test for the "is_ssh" function.
    '''
    assert hep_rfm.protocol_path('username@server', 'ssh').pid == 'ssh'

    pp = hep_rfm.protocol_path('user@my-site:path/to/file', 'ssh')

    s, p = pp.split_path()
    assert s == 'user@my-site' and p == 'path/to/file'

    with pytest.raises(ValueError):
        hep_rfm.protocol_path('/local/file.txt', 'ssh')


def test_xrootdpath():
    '''
    Test for the "XRootDPath" protocol path.
    '''
    assert hep_rfm.protocol_path('root://my-site//', 'xrootd').pid == 'xrootd'

    pp = hep_rfm.protocol_path('root://my-site//path/to/file', 'xrootd')

    s, p = pp.split_path()
    assert s == 'my-site' and p == '/path/to/file'

    with pytest.raises(ValueError):
        hep_rfm.protocol_path('/local/file.txt', 'xrootd')
