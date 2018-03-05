'''
Define some exceptions to be raised when executing subprocesses.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']


__all__ = []


class ProcessError(RuntimeError):
    '''
    Define an error to be raised when a subprocess call fails.
    '''
    def __init__( self, msg, stderr ):
        '''
        The message and "stderr" from the subprocess call must be provided.

        :param msg: message to display.
        :type msg: str
        :param stderr: error output from a subprocess call.
        :type stderr: str
        '''
        RuntimeError.__init__(self, '{}\nstderr:\n{}'.format(msg, stderr))


class CopyFileError(ProcessError):
    '''
    Define an error to be raised when copying a file.
    '''
    def __init__( self, ipath, opath, stderr ):
        '''
        Build the class with the path to the input and output files.

        :param ipath: path to the input file.
        :type ipath: str
        :param opath: path to the output file.
        :type opath: str
        :param stderr: error output from a subprocess call.
        :type stderr: str
        '''
        msg = 'Problem copying file:\ninput: "{}"\noutput: "{}"'.format(ipath, opath)

        ProcessError.__init__(self, msg, stderr)


class MakeDirsError(ProcessError):
    '''
    Error to be displayed when failing making directories.
    '''
    def __init__( self, target, stderr ):
        '''
        Provide the path to the target and the error output.

        :param target: path to the target.
        :type target: str
        :param stderr: error output from a subprocess call.
        :type stderr: str
        '''
        msg = 'Problem creating directories for "{}"'.format(target)

        ProcessError.__init__(self, msg, stderr)
