'''
Main classes and functions to manage files using the ssh protocol.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Custom
from hep_rfm import protocols
from hep_rfm.exceptions import CopyFileError, MakeDirsError

# Python
import logging, multiprocessing, os, subprocess, socket, warnings


__all__ = [
    'copy_file',
    'FileProxy',
    'getmtime',
    'make_directories',
    'sync_proxies'
    ]


class FileProxy:
    '''
    Object to store the path to a set of files, linked together, where one is
    used to update the others.
    '''
    def __init__( self, source, *targets ):
        '''
        Build a proxy to a file.

        :param source: path to the file to use as a reference.
        :type source: str
        :param targets: path to some other locations to put the target files.
        :type targets: list(str)
        '''
        if len(targets) == 0:
            raise ValueError('At least one target file path must be specified')

        self.source  = source
        self.targets = list(targets)

        for t in self.targets:
            if protocols.is_xrootd(t):
                # The xrootd protocol does not allow to preserve the
                # metadata when copying files.
                warnings.warn('Target "{}" uses xrootd protocol, metadata '\
                                  'will not be updated. The file will always '\
                                  'be updated.'.format(t), Warning)

    def _parallel_copy_worker( self, queue ):
        '''
        Method to copy the source into a target on a parallelized environment.

        :param queue: queue this function is attached to.
        :type queue: multiprocessing.JoinableQueue
        '''
        target = queue.get()
        self.copy_target(target)
        queue.task_done()

    def copy_target( self, target, **kwargs ):
        '''
        Method to copy the source into a single target. This allows to manage
        targets even if they are not present within this class.

        :param target: path to a target file.
        :type target: str
        :param kwargs: extra arguments to :func:`copy_file`.
        :type kwargs: dict

        .. seealso: :func:`copy_file`, :func:`make_directories`
        '''
        make_directories(target)

        copy_file(self.source, target, **kwargs)

    def path( self, xrdav=False ):
        '''
        Get the most accessible path to one of the files in this class.

        :param xrdav: whether the xrootd protocol is available in root.
        :type xrdav: bool
        :returns: path to the file.
        :rtype: str
        '''
        host = socket.getfqdn()

        all_paths = list(self.targets)
        all_paths.append(self.source)

        path = None
        for s in all_paths:

            if protocols.is_ssh(s):

                server, sepath = _split_remote(s)

                if server.endswith(host):
                    path = sepath
                    break

            elif protocols.is_xrootd(s):
                if xrdav:
                    path = s
                    break
            else:
                path = s
                break

        if path is not None:
            logging.getLogger(__name__).info('Using path "{}"'.format(path))
            return path

        raise RuntimeError('Unable to find an available path')

    def set_username( self, uname, host=None ):
        '''
        Assign the user name "uname" to the source and targets with
        host equal to "host", and which do not have a user name yet.

        :param source: path to a file.
        :type source: str
        :param uname: user name.
        :type uname: str
        :param host: host name.
        :type host: str or None
        '''
        self.source = _set_username(self.source, uname, host)
        for i, t in enumerate(self.targets):
            self.targets[i] = _set_username(t, uname, host)

    def sync( self, para_targets=False, **kwargs ):
        '''
        Synchronize the target files using the source file.

        :param para_targets: number of processes to be dedicated to \
        synchronize the source with the targets. By default (0) no \
        parallelization is done.
        :type para_targets: int
        :param kwargs: extra arguments to :func:`copy_file`.
        :type kwargs: dict
        '''
        if para_targets:

            queue = multiprocessing.JoinableQueue()

            # Prevent from creating extra processes which might end up
            # as zombies
            para_targets = min(para_targets, len(self.targets))

            for i in range(para_targets):
                p = multiprocessing.Process(target=self._parallel_copy_worker,
                                            args=(queue,))
                p.start()

            for target in self.targets:
                queue.put(target)

            queue.join()
        else:
            for target in self.targets:
                self.copy_target(target, **kwargs)


def copy_file( source, target, force=False ):
    '''
    Main function to copy a file from a source to a target. The copy is done
    if the modification time of both files do not coincide. If "force" is
    specified, then the copy is done independently on this.

    :param force: if set to True, the files are copied even if they are \
    up to date.
    :type force: bool
    '''
    itmstp = getmtime(source)

    if itmstp == None:
        raise RuntimeError('Unable to synchronize file "{}", the '\
                               'file does not exist'.format(source))

    logger = logging.getLogger(__name__)

    if getmtime(target) != itmstp or force:

        # Copy the file

        dec = protocols._remote_protocol(source, target)
        if dec == protocols.__different_protocols__:
            # Copy to a temporal file
            if protocols.is_remote(source):
                _, path = _split_remote(source)
            else:
                path = source

            tmp = '/tmp/' + os.path.basename(path)

            copy_file(source, tmp)
            copy_file(tmp, target)
        else:

            logger.info('Trying to get file from "{}"'.format(source))

            if dec == protocols.__ssh_protocol__:
                proc = _process('scp', '-q', '-p', source, target)
            elif dec == protocols.__xrootd_protocol__:
                proc = _process('xrdcp', '-f', '-s', source, target)
            else:
                proc = _process('cp', '-p', source, target)

            logger.info('Output will be copied into "{}"'.format(target))

            if proc.wait() != 0:
                _, stderr = proc.communicate()
                raise CopyFileError(source, target, stderr)

            if dec == protocols.__xrootd_protocol__ and not protocols.is_xrootd(target):
                # Update the modification time since xrdcp does not
                # preserve it.
                os.utime(target, (os.stat(target).st_atime, itmstp))

            logger.info('Successfuly copied file')

    else:
        logger.info('File "{}" is up to date'.format(target))


def getmtime( path ):
    '''
    Get the modification time for the file in "path". Only the integer part of
    the modification time is used.

    :param path: path to the input file.
    :type path: str
    :returns: modification time.
    :rtype: int or None
    '''
    if protocols.is_remote(path):

        server, sepath = _split_remote(path)

        if protocols.is_ssh(path):
            proc = _process('ssh', '-X', server, 'stat', '-c%Y', sepath)
        else:
            proc = _process('xrd', server, 'stat', sepath)
    else:
        proc = _process('stat', '-c%Y', path)

    if proc.wait() != 0:
        return None

    tmpstp = proc.stdout.read()
    if protocols.is_xrootd(path):
        tmpstp = tmpstp[tmpstp.find('Modtime:') + len('Modtime:'):]

    return int(tmpstp)


def make_directories( target ):
    '''
    Make the directories for the given target in case they do not exist already.

    :param target: path to a target file.
    :type target: str
    '''
    if protocols.is_remote(target):

        server, sepath = _split_remote(target)

        dpath = os.path.dirname(sepath)

        if protocols.is_xrootd(target):
            proc = _process('xrd', server, 'mkdir', dpath)
        else:
            proc = _process('ssh', '-X', server, 'mkdir', '-p', dpath)

    else:

        dpath = os.path.dirname(target)

        proc = _process('mkdir', '-p', dpath if dpath != '' else './')

    if proc.wait() != 0:
        _, stderr = proc.communicate()
        raise MakeDirsError(target, stderr)


def _process( *args ):
    '''
    Create a subprocess object with a defined "stdout" and "stderr",
    using the given commands.

    :param args: set of commands to call.
    :type args: tuple
    :returns: subprocess applying the given commands.
    :rtype: subprocess.Popen
    '''
    return subprocess.Popen( args,
                             stdout = subprocess.PIPE,
                             stderr = subprocess.PIPE)


def _set_username( source, uname, host=None ):
    '''
    Return a modified version of "source" in case it contains the
    given host. If no host is provided, then the user name will be
    set unless "source" has already defined one.

    :param source: path to a file.
    :type source: str
    :param uname: user name.
    :type uname: str
    :param host: host name.
    :type host: str or None
    :returns: modified version of "source".
    :rtype: str
    '''
    if source.startswith('@'):

        if host is None:
            return uname + source
        else:
            if source[1:].startswith(host):
                return uname + source

    return source


def _split_remote( path ):
    '''
    Split a path related to a remote file in site and true path.

    :param path: path to the input file.
    :type path: str
    :returns: site and path to the file in the site.
    :rtype: str, str
    '''
    if protocols.is_ssh(path):
        return path.split(':')
    else:
        rp = path.find('//', 7)
        return path[7:rp], path[rp + 2:]


def _parallel_sync_worker( queue, **kwargs ):
    '''
    Function to synchronize a FileProxy object on a parallelized environment.

    :param queue: queue this function is attached to.
    :type queue: multiprocessing.JoinableQueue
    :param kwargs: extra arguments to :meth:`FileProxy.syn`.
    :type kwargs: dict
    '''
    proxy = queue.get()
    proxy.sync(**kwargs)
    queue.task_done()


def sync_proxies( proxies, para_proxies=False, **kwargs ):
    '''
    Synchronize a given list of proxies. This function allows to fully
    parallelize all the processes.

    :param proxies: file proxies to synchronize.
    :type proxies: collection(FileProxy)
    :param para_proxies: number of processes allowed to parallelize the \
    synchronization of all the proxies. By default it is set to 0, so no \
    parallelization  is done (0).
    :type para_proxies: int
    :param kwargs: extra arguments to :meth:`FileProxy.sync`.
    :type kwargs: dict

    .. seealso: :meth:`FileProxy.sync`
    '''
    if para_proxies:

        queue = multiprocessing.JoinableQueue()

        # Prevent from creating extra processes which might end up
        # as zombies
        para_proxies = min(para_proxies, len(proxies))

        for i in range(para_proxies):
            p = multiprocessing.Process(target=_parallel_sync_worker,
                                        args=(queue,),
                                        kwargs=kwargs)
            p.start()

        for p in proxies:
            queue.put(p)

        queue.join()

    else:
        for p in proxies:
            p.sync(**kwargs)
