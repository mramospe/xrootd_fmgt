'''
Object and functions to define and work with tables of files.
'''

__author__ = ['Miguel Ramos Pernas']
__email__ = ['miguel.ramos.pernas@cern.ch']


__all__ = ['Table', 'Manager']

import warnings
import tempfile
import os
import multiprocessing
import logging
import json
import itertools
import datetime
from hep_rfm.parallel import JobHandler, Worker
from hep_rfm.version import __version__
from hep_rfm.files import FileInfo
from hep_rfm.fields import construct_from_fields
from hep_rfm.core import copy_file
from hep_rfm import protocols


def _compute_changes(tables, most_recent):
    '''
    Compute the changes among a set of tables given the most recent version
    of each file.
    The output will be a list containing the changes for each table.
    The first entry for each change will correspond to the
    :class:`hep_rfm.FileInfo` instance related to the most recent
    version of the file, whilst the second will correspond to the version
    in the table.

    :param tables: tables to process.
    :type tables: colection(Table)
    :param most_recent: most recent version of the files.
    :type most_recent: collection(FileInfo)
    :returns: changes for each table.
    :rtype: list(tuple(FileInfo, FileInfo))
    '''
    changes_by_table = []

    for table in tables:

        changes = []

        for f in most_recent:
            sf = table[f.name]
            if f.newer_than(sf):
                changes.append((f, sf))

        changes_by_table.append(changes)

    return changes_by_table


def _filenames_from_tables(tables, sources):
    '''
    Get the file names from a given collection of tables, checking that
    all of them have the same entries.

    :param tables: tables to process.
    :type tables: collection(Table)
    :param sources: paths to the location of the tables. This is the path \
    that will be displayed in case :class:`RuntimeError` is raised. Must \
    be of the same length as "tables".
    :type sources: collection(str)
    :returns: reference names for the files in the tables.
    :rtype: set(str)
    :raises RuntimeError: if any of the tables containes a different set \
    of entries.
    '''
    names = set(itertools.chain.from_iterable(t.keys() for t in tables))

    name_error = False

    for table, source in zip(tables, sources):
        for name in names:

            if name not in table.keys():
                logging.getLogger(__name__).error(
                    'Table in "{}" does not have file "{}"'.format(source, name))
                name_error = True

    if name_error:
        raise RuntimeError('Missing files in some tables')

    return names


class Manager(object):

    def __init__(self):
        '''
        Represent a class to store tables in different local/remote hosts, being
        able to do updates among them.

        :ivar tables: paths to the stored tables.
        '''
        self.tables = []

        super(Manager, self).__init__()

    def add_table(self, path, protocol=None):
        '''
        Add a new table to the list of tables.
        The path is automatically transformed into the corresponding
        :class:`ProtocolPath` instance.

        :param path: path to the new table.
        :type path: str
        '''
        pp = protocols.protocol_path(path, protocol)

        self.tables.append(pp)

    def available_table(self, modifiers=None, allow_protocols=None):
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

    def update(self, parallelize=False, wdir=None, modifiers=None):
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

        # Copy the tables to a temporary directory to work with them,
        # and get the names of all the files

        logging.getLogger(__name__).info(
            'Copying tables to a temporary directory')

        source_tables = []
        tmp_tables = []
        tables = []

        tmpdir = tempfile.TemporaryDirectory()
        for i, n in enumerate(self.tables):

            fpath = protocols.LocalPath(
                os.path.join(tmpdir.name, 'table_{}.txt'.format(i)))

            copy_file(n, fpath, **kwargs)

            table = Table.read(fpath.path)

            source_tables.append(n)
            tmp_tables.append(fpath)
            tables.append(table)

        # Loop over the tables to get the more recent versions of the files

        logging.getLogger(__name__).info(
            'Determining most recent version of files')

        most_recent = []
        for name in _filenames_from_tables(tables, source_tables):
            mr = None
            for t in tables:
                f = t[name]
                if mr is None or f.newer_than(mr):
                    mr = f
            most_recent.append(mr)

        # Loop over the information with the more recent versions and mark the
        # the files to update in each table.
        changes_by_table = _compute_changes(tables, most_recent)

        #
        # Synchronize files and tables.
        #

        sync_files = [(f.protocol_path, s.protocol_path)
                      for f, s in itertools.chain.from_iterable(changes_by_table)]
        sync_tables = []

        # Get the list of sources/targets to process from the update tables
        for i, changes in enumerate(changes_by_table):

            if not len(changes):
                continue

            tmp = tmp_tables[i]
            source = source_tables[i]
            table = tables[i]

            sync_tables.append((tmp, source))

            # Change hash values and timestamps
            for src, tgt in changes:
                table[tgt.name] = FileInfo(
                    tgt.name, tgt.protocol_path, src.marks)

            table.write(tmp.path)

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

    def __init__(self, files=None, description='', last_update=None, version=None):
        '''
        Create a table storing the information about files.

        :param files: files to store in the table.
        :type files: dict(str, FileInfo)
        :param description: string to explain the contents of the table.
        :type description: str
        :param last_update: date and time of the last update of the table.
        :type last_update: str
        :param version: version of this package used to create the table.
        :type version: str

        :ivar description: string with a description of the values contained \
        in the table.
        :ivar last_update: data and time of the last update done to the \
        table. The value is only filled for tables read from a file. If the \
        table is created from scratch, then it is set to None.
        :ivar version: version of the package used to create the table. The \
        value is only filled for tables read from a file. If the table is \
        created from scratch, then it is set to None.

        .. note:: For tables built from a file, the version corresponds to that
           of the hep_rfm package used to create them, although the structure
           corresponds to that of the current. The information of the last update
           is set to None for just created tables, and it is set only for tables
           read from files.

        .. warning:: If a dictionary of files is provided in "files", then
           it is necessary for each key to be equal to the name of its related
           file.

        .. seealso:: :class:`hep_rfm.Manager`, :func:`hep_rfm.copy_file`
        '''
        super(Table, self).__init__(files or {})

        self.description = description
        self.last_update = last_update
        self.version = version

    @construct_from_fields(['description', 'files', 'last_update', 'version'], required=['files'])
    def from_fields(cls, **fields):
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
    def from_files(cls, files, description='', last_update=None, version=None):
        '''
        Build the class from a list of :class:`hep_rfm.FileInfo` instances.
        The names of the files are used as keys for the table.

        :param files: files to store in the table.
        :type files: collection(FileInfo)
        :param description: string to explain the contents of the table.
        :type description: str
        :param last_update: date and time of the last update of the table.
        :type last_update: str
        :param version: version of this package used to create the table.
        :type version: str
        '''
        return cls({f.name: f for f in files}, description, last_update, version)

    @classmethod
    def read(cls, path):
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

            fields['files'] = {n: FileInfo.from_fields(
                **fs) for n, fs in fields.get('files', {}).items()}

        return cls.from_fields(**fields)

    def updated(self, files=None, modifiers=None, parallelize=False):
        '''
        Return an updated version of this table, checking again all the
        properties of the files within it.

        :param files: files to update within the table. The returned table \
        will contain the same entries as the parent, but with the files \
        specified in "files" updated.
        :type files: collection(str)
        :param modifiers: information to modify the path of this class.
        :type modifiers: dict
        :param parallelize: number of processes allowed to parallelize the \
        synchronization of all the proxies. By default it is set to 0, so no \
        parallelization  is done.
        :type parallelize: int
        :returns: updated version of the table.
        :rtype: Table
        '''
        files = tuple(files or self.keys())

        if parallelize:

            handler = JobHandler()

            for f in files:
                handler.put(self[f])

            def func(f, q): return q.put(f.updated(modifiers=modifiers))

            queue = multiprocessing.Queue()

            for i in range(parallelize):
                Worker(handler, func, args=(queue,))

            handler.process()

            ufiles = tuple(queue.get() for _ in range(len(files)))

            queue.close()
        else:
            ufiles = tuple(self[f].updated(modifiers=modifiers) for f in files)

        # We must add the rest of the files in case "files" is provided
        ufiles += tuple(self[f] for f in set(self.keys()).difference(files))

        return self.__class__.from_files(ufiles, self.description, self.last_update, self.version)

    def write(self, path, backup=False):
        '''
        Write this table in the following location.
        Must be a local path.
        The current version of the package will be used.

        :param path: where to write this table to.
        :type path: str
        :param backup: if a table in "path" already exists and this \
        argument is set to True, then the previous file is renamed \
        to <filename>.backup before modifying it. If it is set to \
        a string, then that is used as file name to write the backup.
        :type backup: bool or str
        :raises IOError: if the output path exists and it does not correspond \
        to a file.
        '''
        dct = {
            'version': __version__,
            'description': self.description,
            'last_update': str(datetime.datetime.now()),
            'files': {n: f.info() for n, f in sorted(self.items())},
        }

        if os.path.exists(path) and not os.path.isfile(path):
            raise IOError(
                'Attempt to write a table to an existing path not corresponding to a file.')

        if backup:
            if not os.path.exists(path):
                warnings.warn(
                    'No previous table is present in the given path; backup has not been generated', Warning)
            else:
                if backup is True:
                    backup_name = path + '.backup'
                else:
                    backup_name = backup

                os.rename(path, backup_name)

        with open(path, 'wt') as f:
            f.write(json.dumps(dct, indent=4, sort_keys=True))
