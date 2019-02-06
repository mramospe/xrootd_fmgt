'''
Object and functions to define and work with tables of files.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Local
from hep_rfm import protocols
from hep_rfm.core import copy_file
from hep_rfm.fields import construct_from_fields
from hep_rfm.files import FileInfo
from hep_rfm.version import __version__
from hep_rfm.parallel import JobHandler, Worker

# Python
import json
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

    def add_table( self, path, protocol = None ):
        '''
        Add a new table to the list of tables.
        The path is automatically transformed into the corresponding
        :class:`ProtocolPath` instance.

        :param path: path to the new table.
        :type path: str
        '''
        pp = protocols.protocol_path(path, protocol)

        self.tables.append(pp)

    def available_table( self, modifiers = None, allow_protocols = None ):
        '''
        Get the path to the first available table.
        The behavior is similar to that of :class:`hep_rfm.available_path`.

        :param modifiers: modifiers to be applied in the set of paths.
        :type modifiers: dict
        :param allow_protocols: possible protocols to consider.
        :type allow_protocols: container(str)
        :returns: path to the first available table.
        :rtype: str

        .. seealso:: :func:`available_path`
        '''
        return protocols.available_path(self.tables, modifiers, allow_protocols)

    def update( self, parallelize = False, wdir = None, modifiers = None ):
        '''
        Update the different tables registered within this manager.

        :param parallelize: number of processes allowed to parallelize the \
        synchronization of all the proxies. By default it is set to 0, so no \
        parallelization  is done.
        :type parallelize: int
        :param wdir: where to create the temporary directory. The option \
        is passed to :class:`tempfile.TemporaryDirectory` as "dir".
        :type wdir: str
        :param modifiers: information to modify the path of this class. For \
        more information on its structure, see the definition of \
        :func:`hep_rfm.ProtocolPath.with_modifiers` for each protocol.
        :type modifiers: dict
        :raises RuntimeError: if a file is missing for any of the tables.

        .. seealso:: :class:`hep_rfm.Table`, :func:`hep_rfm.copy_file`
        '''
        kwargs = {'wdir': wdir, 'modifiers': modifiers}

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

            fpath = protocols.LocalPath(
                os.path.join(tmp.name, 'table_{}.txt'.format(i)))

            copy_file(n, fpath, **kwargs)

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

                    logging.getLogger(__name__).error('Table in "{}" does not have file "{}"'.format(tu.protocol_path.path, name))

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
        # Synchronize files and tables.
        #
        sync_files, sync_tables = [], []

        # Get the list of sources/targets to process from the update tables
        for u in update_tables:

            sync_files += u.changes()

            if u.needs_update():
                sync_tables.append((u.tmp_path, u.path))

        if len(sync_files):
            logging.getLogger(__name__).info('Starting to synchronize files')
        else:
            logging.getLogger(__name__).info('All files are up to date')

        # Do not swap "sync_files" and "sync_tables". First we must modify the
        # files and, in the last step, update the information in the tables.
        if parallelize:

            func = lambda obj, **kwargs: copy_file(*obj, **kwargs)

            for lst in (sync_files, sync_tables):

                lock = multiprocessing.Lock()

                handler = JobHandler()

                for i in lst:
                    handler.put(i)

                kwargs['loglock'] = lock

                for i in range(parallelize):
                    Worker(handler, func, kwargs=kwargs)

                handler.process()
        else:
            for i in sync_files + sync_tables:
                copy_file(*i, **kwargs)


class Table(dict):

    def __init__( self, files = None, description = '', version = __version__ ):
        '''
        Create a table storing the information about files.

        :param files: files to store in the table.
        :type files: collection(FileInfo)
        :param description: string to explain the contents of the table.
        :type description: str

        .. seealso:: :class:`hep_rfm.Manager`, :func:`hep_rfm.copy_file`
        '''
        super(Table, self).__init__()

        if files is None:
            files = []

        self.description = description
        self.version     = version

        for f in files:
            self[f.name] = f

    @construct_from_fields(['description', 'files', 'version'], required=['files'])
    def from_fields( cls, **fields ):
        '''
        Build the class from a set of fields, which might or not
        coincide with those in the class constructor.

        :param fields: dictionary of fields to process.
        :type fields: dict
        :returns: built table.
        :rtype: Table
        '''
        return cls(**fields)

    @classmethod
    def read( cls, path ):
        '''
        Build a table from the information in the file at the given local path.

        :param path: path to the text file storing the table.
        :type path: str
        :returns: built table.
        :rtype: Table
        '''
        with open(path, 'rt') as fi:

            data = fi.read()

            if data:
                fields = json.loads(data)
            else:
                fields = {}

            fields['files'] = [FileInfo.from_fields(**fs) for fs in fields.get('files', {}).values()]

        return cls.from_fields(**fields)

    def updated( self, parallelize = False ):
        '''
        Return an updated version of this table, checking again all the
        properties of the files within it.

        :param parallelize: number of processes allowed to parallelize the \
        synchronization of all the proxies. By default it is set to 0, so no \
        parallelization  is done.
        :type parallelize: int
        :returns: updated version of the table.
        :rtype: Table
        '''
        if parallelize:

            handler = JobHandler()

            for f in self.values():
                handler.put(f)

            func = lambda f, q: q.put(f.updated())

            queue = multiprocessing.Queue()

            for i in range(parallelize):
                Worker(handler, func, args=(queue,))

            handler.process()

            output = [queue.get() for _ in range(len(self))]

            queue.close()
        else:
            output = [f.updated() for f in self.values()]

        return self.__class__(output)

    def write( self, path ):
        '''
        Write this table in the following location.
        Must be a local path.

        :param path: where to write this table to.
        :type path: str
        '''
        dct = {
            'version'     : __version__,
            'description' : self.description,
            'files'       : {n: f.info() for n, f in sorted(self.items())},
        }
        with open(path, 'wt') as f:
            f.write(json.dumps(dct, indent=4, sort_keys=True))


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
        self.table    = Table.read(tmp_path.path)
        self._changes = []

    def changes( self ):
        '''
        Returns the changes to apply.

        :returns: changes to apply (input and output paths).
        :rtype: list(tuple(str, str))
        '''
        return list(map(lambda t: (t[0].protocol_path, t[1].protocol_path), self._changes))

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

            self.table[tgt.name] = FileInfo(tgt.name, tgt.protocol_path, src.marks)

        self.table.write(self.tmp_path.path)
