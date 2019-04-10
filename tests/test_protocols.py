import hep_rfm
import socket
import pytest
import os
'''
Test functions for the "protocols" module.
'''

__author__ = ['Miguel Ramos Pernas']
__email__ = ['miguel.ramos.pernas@cern.ch']

# Python

# Custom


def test_available_path(tmpdir):
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
    assert p == lp

    p = hep_rfm.available_path(paths, allow_protocols=('xrootd',))
    assert p == xr

    # Test exceptions
    with pytest.raises(RuntimeError):
        hep_rfm.available_path(paths[:-1])

    # Test the function with modifiers
    host = socket.gethostname()
    remote_path = hep_rfm.protocol_path('user@{}:{}'.format(host, lp), 'ssh')
    p = hep_rfm.available_path([remote_path], modifiers={'ssh_hosts': [host]})
    assert p == lp


def test_available_working_path(tmpdir):
    '''
    Test for the "available_working_path" function.
    '''
    local_path = hep_rfm.protocol_path(tmpdir.join('file.txt').strpath)

    with open(local_path.path, 'wt') as f:
        f.write('something')

    nlocal_path = hep_rfm.protocol_path('non-existing-file.txt')
    xrootd_path = hep_rfm.protocol_path('root://my-site//file.txt', 'xrootd')
    ssh_path = hep_rfm.protocol_path('user@host:/file.txt', 'ssh')

    assert hep_rfm.available_working_path(local_path)
    assert not hep_rfm.available_working_path(nlocal_path)
    assert hep_rfm.available_working_path(
        xrootd_path, allow_protocols=('xrootd',))
    assert not hep_rfm.available_working_path(xrootd_path)
    assert not hep_rfm.available_working_path(ssh_path)


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

    assert pp1.__protocols__ is pp2.__protocols__

    lp1 = hep_rfm.LocalPath(path)

    assert lp1.__protocols__ is pp1.__protocols__

    lp2 = hep_rfm.LocalPath(path)

    assert lp1.pid is lp2.pid


def test_localpath(tmpdir):
    '''
    Test for the "LocalPath" class.
    '''
    path = tmpdir.join('subdir/file.txt')
    pp = hep_rfm.protocol_path(path.strpath)

    assert pp.pid == 'local'
    assert pp.path == path
    assert not hep_rfm.is_remote(pp)

    pp.mkdirs()

    assert os.path.isdir(os.path.dirname(pp.path))


def test_register_protocol():
    '''
    Test for the "register_protocol" decorator.
    '''
    @hep_rfm.register_protocol('special-protocol')
    class SpecialPath(hep_rfm.ProtocolPath):
        def copy(self, path):
            return process('cp', path, self.target)

        def mkdirs(self):
            dpath = os.path.dirname(self.path)
            return process('mkdir', '-p', dpath if dpath != '' else './')

    assert SpecialPath('/local/file.txt').pid == 'special-protocol'

    with pytest.raises(RuntimeError):
        # Does not inherit from ProtocolPath
        @hep_rfm.register_protocol('another-protocol-1')
        class AnotherPath1(object):
            pass

    with pytest.raises(ValueError):
        # There is already a protocol path with that name
        @hep_rfm.register_protocol('special-protocol')
        class SpecialPath(hep_rfm.ProtocolPath):
            pass

    #
    # Test missing overrides
    #
    with pytest.raises(hep_rfm.exceptions.MustOverrideError):
        # Some methods from ProtocolPath are missing
        @hep_rfm.register_protocol('another-protocol-2')
        class AnotherPath2(hep_rfm.ProtocolPath):
            pass

    with pytest.raises(hep_rfm.exceptions.MustOverrideError):
        # Some methods from RemotePath are missing
        @hep_rfm.register_protocol('another-protocol-3')
        class AnotherPath3(hep_rfm.RemotePath):
            def copy(self, path):
                return process('cp', path, self.target)

            def mkdirs(self):
                dpath = os.path.dirname(self.path)
                return process('mkdir', '-p', dpath if dpath != '' else './')


def test_remotepath():
    '''
    Test for the "RemotePath" class.
    '''
    path = 'user@host:/file.txt'

    pp = hep_rfm.RemotePath(path)

    assert pp.path == path


def test_is_remote():
    '''
    Test for the "is_remote" function.
    '''
    remotes = (
        hep_rfm.protocol_path('root://my-site//', 'xrootd'),
        hep_rfm.protocol_path('username@server', 'ssh'),
    )

    for r in remotes:
        assert hep_rfm.is_remote(r)

    assert not hep_rfm.is_remote(hep_rfm.protocol_path('/local/path/file.txt'))


def test_process(tmpdir):
    '''
    Test for the "process" function.
    '''
    path = tmpdir.join('example.txt').strpath

    p = hep_rfm.process('touch', path)
    assert p.wait() == 0

    assert os.path.isfile(path)


def test_remote_protocol():
    '''
    Test for the "remote_protocol" function.
    '''
    local = hep_rfm.protocol_path('/local/path/file.txt')
    ssh = hep_rfm.protocol_path('user@host:/file.txt', 'ssh')
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

    pp = hep_rfm.protocol_path('user@my-site:path/to/file.txt', 'ssh')

    s, p = pp.split_path()
    assert s == 'user@my-site' and p == 'path/to/file.txt'

    with pytest.raises(ValueError):
        hep_rfm.protocol_path('/local/file.txt', 'ssh')

    p = hep_rfm.SSHPath.join_path('user@my-site', 'path/to/file.txt')
    assert p == 'user@my-site:path/to/file.txt'

    pp = pp.with_modifiers({'ssh_usernames': {'my-site': 'other.user'}})
    assert pp.path == 'other.user@my-site:path/to/file.txt'

    pp = hep_rfm.protocol_path('@my-site:path/to/file.txt', 'ssh')
    pp = pp.with_modifiers({'ssh_usernames': {'my-site': 'user'}})
    assert pp.path == 'user@my-site:path/to/file.txt'

    host = socket.gethostname()

    pp = hep_rfm.protocol_path('user@{}:path/to/file.txt'.format(host), 'ssh')
    pp = pp.with_modifiers({'ssh_hosts': [host]})
    assert pp.path == 'path/to/file.txt'

    pp = hep_rfm.protocol_path('@my-site:path/to/file.txt', 'ssh')
    with pytest.raises(RuntimeError):
        pp.with_modifiers()


def test_xrootdpath():
    '''
    Test for the "XRootDPath" protocol path.
    '''
    assert hep_rfm.protocol_path('root://my-site//', 'xrootd').pid == 'xrootd'

    pp = hep_rfm.protocol_path('root://my-site//path/to/file', 'xrootd')

    s, p = pp.split_path()
    assert s == 'my-site' and p == '/path/to/file'

    pp = hep_rfm.protocol_path('root://my-site//path/to/file', 'xrootd')
    pp = pp.with_modifiers({'xrootd_servers': ['my-site']})
    assert pp.path == '/path/to/file'

    with pytest.raises(ValueError):
        hep_rfm.protocol_path('/local/file.txt', 'xrootd')

    for p in (
            hep_rfm.XRootDPath.join_path(
                'root://server', 'path/in/server/file.txt'),
            hep_rfm.XRootDPath.join_path(
                'root://server/', 'path/in/server/file.txt'),
            hep_rfm.XRootDPath.join_path(
                'root://server//', '/path/in/server/file.txt'),
    ):
        assert p == 'root://server//path/in/server/file.txt'
