'''
Test the scripts under the "scripts" directory.
'''

__author__ = ['Miguel Ramos Pernas']
__email__  = ['miguel.ramos.pernas@cern.ch']

# Python
import os
import subprocess

# Local
import hep_rfm


def process( strfunc, code = 0 ):
    '''
    Execute a string on a new process and check that the output code
    is equal to "code"
    '''
    p = subprocess.Popen(strfunc.split())
    assert p.wait() == code


def with_file_schema( func ):
    '''
    Decorator to create a shema of directories with files to process.
    '''
    def wrapper( tmpdir ):
        '''
        Internal wrapper.
        '''
        files = {}

        # Add file in the current directory
        files['file1'] = tmpdir.join('file1.txt')
        files['file2'] = tmpdir.join('file2.txt')
        files['file3'] = tmpdir.join('file3.txt')
        files['file4'] = tmpdir.join('file4.txt')

        # Add file into a sub-directory as well
        subdir = tmpdir.mkdir('subdir')
        files['file5'] = subdir.join('file5.txt')
        files['file6'] = subdir.join('file6.txt')

        # Create a sub-sub-directory
        subsubdir = subdir.mkdir('subsubdir')
        files['file7'] = subsubdir.join('file7.txt')
        files['file8'] = subsubdir.join('file8.db') # Does not end on ".txt"

        table_path = tmpdir.join('table.txt')

        with files['file1'].open('wb') as f:
            f.write(b'file1 text in binary')
        #
        # file2 is missing
        #
        with files['file3'].open('wt') as f:
            f.write('file3 text')
        with files['file4'].open('wt') as f:
            f.write('file4 text is a bit larger')
        with files['file5'].open('wt') as f:
            f.write('file5 is in the sub-directory')
        with files['file6'].open('wt') as f:
            f.write('file6 is in the sub-directory and has a larger text')
        with files['file7'].open('wt') as f:
            f.write('file7 is in the sub-sub-directory')
        with files['file8'].open('wt') as f:
            f.write('file8 is in the sub-sub-directory')

        func(tmpdir, table_path, files)

    return wrapper


def with_table_created( func ):
    '''
    Decorator for test functions that need the table to be created.
    '''
    @with_file_schema
    def wrapper( tmpdir, table_path, files ):
        '''
        Internal wrapper.
        '''
        process('hep-rfm-table create {}'.format(table_path))

        func(tmpdir, table_path, files)

    return wrapper


def with_table_filled( func ):
    '''
    Decorator for test functions that need the table to be created
    and filled.
    '''
    @with_table_created
    def wrapper( tmpdir, table_path, files ):
        '''
        Internal wrapper.
        '''
        process('hep-rfm-table add_from_dir {} {}'.format(table_path, tmpdir))

        func(tmpdir, table_path, files)

    return wrapper


@with_table_filled
def test_hep_rfm_table_breaking_commands( tmpdir, table_path, files ):
    '''
    Test function for the "hep-rfm-table" script with modes that break.
    '''
    # Need to re-create a table
    new_table_path = tmpdir.join('table_replica.txt')

    process('hep-rfm-table create {}'.format(new_table_path))

    process('hep-rfm-table replicate {} {} {} {} --collisions omit'.format(new_table_path, table_path, tmpdir, tmpdir))

    incpath = table_path.strpath[table_path.strpath.find('/', 1):]

    # Commands that break
    break_cmds = (
        # Attempt to add a file that does not exist
        'hep-rfm-table add {} {} {}'.format(table_path, 'none', tmpdir.join('none.txt')),
        # Attempt to recreate the structure of one table in another with
        # colliding file names
        'hep-rfm-table replicate {} {} {} {}'.format(new_table_path, table_path, tmpdir, tmpdir),
        # Refpath must be absolute
        'hep-rfm-table replicate {} {} {} {}'.format(new_table_path, incpath, tmpdir, tmpdir),
    )

    for c in break_cmds:
        p = process(c, code=1)


@with_table_created
def test_hep_rfm_table_from_dir( tmpdir, table_path, files ):
    '''
    Test modes of the "hep-rfm-table" script that massively add files from a
    directory.
    '''
    # Add files in directory filtering by regular expression
    process('hep-rfm-table add_from_dir {} {} --regex .*.txt$'.format(table_path, tmpdir))

    table = hep_rfm.Table.read(table_path.strpath)

    for f in table.values():
        f.marks.tmstp != hep_rfm.files.__default_tmstp__
        f.marks.fid   != hep_rfm.files.__default_fid__

    assert len(table) == 7

    # Add all files in the sub-directory
    process('hep-rfm-table add_from_dir {} {}'.format(table_path, tmpdir.join('subdir')))

    table = hep_rfm.Table.read(table_path.strpath)

    assert len(table) == 8


@with_file_schema
def test_hep_rfm_table_general( tmpdir, table_path, files ):
    '''
    Test basic modes of the "hep-rfm-table" script.
    '''
    cmds = (
        'hep-rfm-table create {}'.format(table_path),
        'hep-rfm-table add {} {} {}'.format(table_path, 'file1', files['file1']),
        'hep-rfm-table add {} {} {} --bare'.format(table_path, 'file2', files['file2']),
        'hep-rfm-table add_massive {} {} {}'.format(table_path, files['file3'], files['file4']),
        'hep-rfm-table update {}'.format(table_path),
        'hep-rfm-table remove {} --files {} {}'.format(table_path, 'file1', 'file2'),
        'hep-rfm-table remove {} --regex {}'.format(table_path, 'file(3|4)'),
        'hep-rfm-table display {}'.format(table_path),
        )

    for c in cmds:
        p = process(c)

    table = hep_rfm.Table.read(table_path.strpath)

    assert len(table) == 0


@with_table_filled
def test_hep_rfm_table_replicate( tmpdir, table_path, files ):
    '''
    Test function for the "hep-rfm-table" script with modes that use another
    table as a reference.
    '''
    # Recreate substructure on a different table
    new_table_path = tmpdir.join('table_replica.txt')

    process('hep-rfm-table create {}'.format(new_table_path))

    process('hep-rfm-table replicate {} {} {} {}'.format(new_table_path, table_path, tmpdir, tmpdir))

    old_table = hep_rfm.Table.read(table_path.strpath)
    new_table = hep_rfm.Table.read(new_table_path.strpath)

    assert len(new_table) == 8

    assert list(sorted(old_table.keys())) == list(sorted(new_table.keys()))

    for k, v in new_table.items():
        assert old_table[k].protocol_path == v.protocol_path
        assert v.marks.fid == hep_rfm.files.__default_fid__
        assert v.marks.tmstp == hep_rfm.files.__default_tmstp__

    # Replace all entries previously added
    process('hep-rfm-table replicate {} {} {} {} --collisions replace'.format(new_table_path, table_path, tmpdir, tmpdir))

    # Omit collisions
    process('hep-rfm-table replicate {} {} {} {} --collisions omit'.format(new_table_path, table_path, tmpdir, tmpdir))
