'''
Define some exceptions to be raised when executing subprocesses.
'''

__author__ = ['Miguel Ramos Pernas']
__email__ = ['miguel.ramos.pernas@cern.ch']


__all__ = ['AbstractMethodError', 'ProcessError',
           'CopyFileError', 'MakeDirsError']


class AbstractMethodError(Exception):

    def __init__(self):
        '''
        Define an error for base classes with abstract methods.
        '''
        super(AbstractMethodError, self).__init__(
            'Attempt to call abstract class method')


class MustOverrideError(Exception):

    def __init__(self, cls, parent, method):
        '''
        Define an error to be raised when a class must override a method and it
        does not.

        :param cls: class that must override the method.
        :type cls: class
        :param parent: parent class where it must inherit from.
        :type parent: class
        :param method: method that must be overriding.
        :type method: method
        '''
        cn = cls.__name__
        mn = method.__name__
        pn = parent.__name__
        msg = 'Class "{}" must override method "{}" from class "{}"'.format(
            cn, mn, pn)

        super(MustOverrideError, self).__init__(msg)


class ProcessError(RuntimeError):

    def __init__(self, msg, stderr):
        '''
        Define an error to be raised when a subprocess call fails.
        The message and "stderr" from the subprocess call must be provided.

        :param msg: message to display.
        :type msg: str
        :param stderr: error output from a subprocess call.
        :type stderr: str
        '''
        RuntimeError.__init__(self, '{}\nstderr:\n{}'.format(msg, stderr))


class CopyFileError(ProcessError):

    def __init__(self, ipath, opath, stderr):
        '''
        Define an error to be raised when copying a file.
        Build the class with the path to the input and output files.

        :param ipath: path to the input file.
        :type ipath: str
        :param opath: path to the output file.
        :type opath: str
        :param stderr: error output from a subprocess call.
        :type stderr: str
        '''
        msg = 'Problem copying file:\ninput: "{}"\noutput: "{}"'.format(
            ipath, opath)

        ProcessError.__init__(self, msg, stderr)


class MakeDirsError(ProcessError):

    def __init__(self, target, stderr):
        '''
        Error to be displayed when failing making directories.
        Provide the path to the target and the error output.

        :param target: path to the target.
        :type target: str
        :param stderr: error output from a subprocess call.
        :type stderr: str
        '''
        msg = 'Problem creating directories for "{}"'.format(target)

        ProcessError.__init__(self, msg, stderr)
