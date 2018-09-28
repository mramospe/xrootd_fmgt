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


def test_hep_rfm_table( tmpdir ):
    '''
    Test function for the "hep-rfm-table" script.
    '''
    # Add file in the current directory
    file1_path = tmpdir.join('file1.txt')
    file2_path = tmpdir.join('file2.txt')
    file3_path = tmpdir.join('file3.txt')
    file4_path = tmpdir.join('file4.txt')

    # Add file into a sub-directory as well
    subdir = tmpdir.mkdir('subdir')
    file5_path = subdir.join('file5.txt')
    file6_path = subdir.join('file6.txt')

    # Create a sub-sub-directory
    subsubdir = subdir.mkdir('subsubdir')
    file7_path = subsubdir.join('file7.txt')
    file8_path = subsubdir.join('file8.db') # Does not end on ".txt"

    table_path = tmpdir.join('table.txt')

    with file1_path.open('wb') as f:
        f.write(b'file1 text in binary')
    #
    # file2 is missing
    #
    with file3_path.open('wt') as f:
        f.write('file3 text')
    with file4_path.open('wt') as f:
        f.write('file4 text is a bit larger')
    with file5_path.open('wt') as f:
        f.write('file5 is in the sub-directory')
    with file6_path.open('wt') as f:
        f.write('file6 is in the sub-directory and has a larger text')
    with file7_path.open('wt') as f:
        f.write('file7 is in the sub-sub-directory')
    with file8_path.open('wt') as f:
        f.write('file8 is in the sub-sub-directory')

    cmds = (
        'hep-rfm-table {} create'.format(table_path),
        'hep-rfm-table {} add {} {}'.format(table_path, 'file1', file1_path),
        'hep-rfm-table {} add {} {} --bare'.format(table_path, 'file2', file2_path),
        'hep-rfm-table {} add_massive {} {}'.format(table_path, file3_path, file4_path),
        'hep-rfm-table {} update'.format(table_path),
        )

    for c in cmds:
        p = subprocess.Popen(c.split())
        assert p.wait() == 0

    # Add files in directory filtering by regular expression
    p = subprocess.Popen('hep-rfm-table {} add_from_dir {} --regex .*.txt$'.format(table_path, subdir).split())
    assert p.wait() == 0

    table = hep_rfm.Table.read(table_path.strpath)

    for f in table.values():
        f.marks.tmstp != hep_rfm.files.__default_tmstp__
        f.marks.fid   != hep_rfm.files.__default_fid__

    assert len(table) == 7

    # Add all files in the sub-directory
    p = subprocess.Popen('hep-rfm-table {} add_from_dir {}'.format(table_path, subdir).split())
    assert p.wait() == 0

    table = hep_rfm.Table.read(table_path.strpath)

    assert len(table) == 8

    # Recreate substructure on a different table
    new_table_path = tmpdir.join('table_clone.txt')

    p = subprocess.Popen('hep-rfm-table {} create'.format(new_table_path).split())
    assert p.wait() == 0

    p = subprocess.Popen('hep-rfm-table {} copy_scheme --reference {} --location {} --refpath {}'.format(new_table_path, table_path, tmpdir, tmpdir).split())
    assert p.wait() == 0

    old_table = hep_rfm.Table.read(table_path.strpath)
    new_table = hep_rfm.Table.read(new_table_path.strpath)

    assert len(table) == 8

    assert list(sorted(old_table.keys())) == list(sorted(new_table.keys()))

    for k, v in new_table.items():
        assert old_table[k].path == v.path
        assert v.marks.fid == hep_rfm.files.__default_fid__
        assert v.marks.tmstp == hep_rfm.files.__default_tmstp__

    # Commands that break
    break_cmds = (
        # Attempt to add a file that does not exist
        'hep-rfm-table {} add {} {}'.format(table_path, 'none', tmpdir.join('none.txt')),
        # Attempt to recreate the structure of one table in another with
        # colliding file names
        'hep-rfm-table {} copy_scheme --reference {} --location {} --refpath {}'.format(new_table_path, table_path, tmpdir, tmpdir),
    )

    for c in break_cmds:
        p = subprocess.Popen(c.split())
        assert p.wait() != 0
