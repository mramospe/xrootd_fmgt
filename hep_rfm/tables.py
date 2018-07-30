'''
Object and functions to define and work with tables of files.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Local
from hep_rfm import core
from hep_rfm import protocols
from hep_rfm.files import FileInfo
from hep_rfm.parallel import JobHandler, Worker

# Python
import logging
import multiprocessing
import os
import tempfile


__all__ = ['Table', 'Manager']


class Manager(object):

    def __init__( self ):
        '''
        Represent a class to store tables in different local/remote hosts, being
        able to do updates among them.

        :ivar tables: paths to the stored tables.
        '''
        self.tables = []

        super(Manager, self).__init__()

    def add_table( self, path ):
        '''
        Add a new table to the list of tables.

        :param path: path to the new table.
        :type path: str
        '''
        self.tables.append(path)

    def available_table( self, use_xrd = False ):
        '''
        Get the path to the first available table.

        :param use_xrd: whether to use the xrootd protocol if needed.
        :type use_xrd: bool
        :returns: path to the first available table.
        :rtype: str
        '''
        return protocols.available_path(self.tables, use_xrd)

    def update( self, parallelize = False, server_spec = None ):
        '''
        Update the different tables registered within this manager.

        :param parallelize: number of processes allowed to parallelize the \
        synchronization of all the proxies. By default it is set to 0, so no \
        parallelization  is done.
        :type parallelize: int
        :param server_spec: specification of user for each SSH server. Must \
        be specified as a dictionary, where the keys are the hosts and the \
        values are the user names.
        :type server_spec: dict
        :raises RuntimeError: if a file is missing for any of the tables.

        .. seealso:: :class:`hep_rfm.Table`, :func:`hep_rfm.copy_file`
        '''
        #
        # Determine the files to update
        #
        update_tables = []

        names = set()

        # Copy the tables to a temporary directory to work with them,
        # and get the names of all the files

        logging.getLogger(__name__).info('Copying tables to a temporary directory')

        tmp = tempfile.TemporaryDirectory()
        for i, n in enumerate(self.tables):

            fpath = os.path.join(tmp.name, 'table_{}.txt'.format(i))

            core.copy_file(n, fpath, server_spec=server_spec)

            tu = TableUpdater(n, fpath)

            update_tables.append(tu)

            names = names.union(tu.table.keys())

        # Loop over the tables to get the more recent versions of the files

        logging.getLogger(__name__).info('Determining most recent version of files')

        more_recent = {}

        name_error = False
        for name in names:
            for tu in update_tables:

                try:
                    f = tu.table[name]

                    if name not in more_recent or f.newer_than(more_recent[name]):
                        more_recent[name] = f

                except KeyError:

                    name_error = True

                    logging.getLogger(__name__).error('Table in "{}" does not have file "{}"'.format(tu.path, name))

        if name_error:
            raise RuntimeError('Missing files in some tables')

        # Loop over the information with the more recent versions and mark the
        # the files to update in each table.
        for f in more_recent.values():
            for u in update_tables:
                u.check_changed(f)

        # The update tables notify the tables to change their hash values and
        # timestamps
        for u in update_tables:
            u.update_table()

        #
        # Synchronize the files
        #
        inputs = []

        # Get the list of sources/targets to process from the update tables
        for u in update_tables:

            inputs += u.changes()

            if u.needs_update():
                inputs.append((u.tmp_path, u.path))

        if len(inputs):
            logging.getLogger(__name__).info('Starting to synchronize files')
        else:
            logging.getLogger(__name__).info('All files are up to date')

        kwargs = {'server_spec': server_spec}

        if parallelize:

            lock = multiprocessing.Lock()

            handler = JobHandler()

            for i in inputs:
                handler.put(i)

            func = lambda obj, **kwargs: core.copy_file(*obj, **kwargs)

            kwargs['loglock'] = lock

            for i in range(parallelize):
                Worker(handler, func, kwargs=kwargs)

            handler.process()
        else:
            for i in inputs:
                core.copy_file(*i, **kwargs)


class Table(dict):

    def __init__( self, files ):
        '''
        Create a table storing the information about files.

        :param files: files to store in the table.
        :type files: collection(FileInfo)

        .. seealso:: :class:`hep_rfm.Manager`, :func:`hep_rfm.copy_file`
        '''
        super(Table, self).__init__()

        for f in files:
            self[f.name] = f

    @classmethod
    def read( cls, path ):
        '''
        Build a table from the information in the file at the given path.

        :param path: path to the text file storing the table.
        :type path: str
        :returns: built table.
        :rtype: Table
        '''
        files = []
        with open(path, 'rt') as fi:

            for l in fi:

                fp = FileInfo.from_stream_line(l)

                files.append(fp)

        return cls(files)

    def updated( self ):
        '''
        Return an updated version of this table, checking again all the
        properties of the files within it.
        '''
        output = [f.updated() for f in self.values()]
        return self.__class__(output)

    def write( self, path ):
        '''
        Write this table in the following location.

        :param path: where to write this table to.
        :type path: str
        '''
        with open(path, 'wt') as fo:
            for _, f in sorted(self.items()):

                info = f.info()

                frmt = '{}'
                for i in range(len(info) - 1):
                    frmt += '\t{}'
                frmt += '\n'

                fo.write(frmt.format(*info))


class TableUpdater(object):

    def __init__( self, path, tmp_path ):
        '''
        Class to ease the procedure of updating tables.

        :param path: path where the information of the given table is holded.
        :type path: str
        :param tmp_path: path to the temporal input table.
        :type tmp_path: str

        :ivar path: path where the real input table is located.
        :ivar tmp_path: path to the temporal input table.
        :ivar table: table holding the information about the files.
        '''
        super(TableUpdater, self).__init__()

        self.path     = path
        self.tmp_path = tmp_path
        self.table    = Table.read(tmp_path)
        self._changes = []

    def changes( self ):
        '''
        Returns the changes to apply.

        :returns: changes to apply (input and output paths).
        :rtype: list(tuple(str, str))
        '''
        return list(map(lambda t: (t[0].path, t[1].path), self._changes))

    def check_changed( self, f ):
        '''
        Determine if a content of the table needs to be updated.

        :param f: information of the file to process.
        :type f: FileInfo
        '''
        sf = self.table[f.name]
        if f.newer_than(sf):
            self._changes.append((f, sf))

    def needs_update( self ):
        '''
        Return whether the associated table needs to be updated.

        :returns: whether the associated table needs to be updated.
        :rtype: bool
        '''
        return (self._changes != [])

    def update_table( self ):
        '''
        Update the table stored within this class.
        '''
        for src, tgt in self._changes:

            self.table[tgt.name] = FileInfo(tgt.name, tgt.path, src.marks)

        self.table.write(self.tmp_path)
