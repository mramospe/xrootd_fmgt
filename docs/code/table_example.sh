#!/bin/bash
#
# Reproduce the example to be shown in the documentation.
#
mkdir rfm
cd rfm
hep-rfm-table -h
hep-rfm-table create table.db
ls
hep-rfm-table display table.db
echo "My first table file" >> file1.txt
hep-rfm-table add table.db file1 file1.txt
hep-rfm-table display table.db
echo "This is the second file" >> file2.txt
echo "This is the third file" >> file3.txt
hep-rfm-table add-massive table.db file2.txt file3.txt
hep-rfm-table display table.db
mkdir -p subdir/subsubdir
echo "This is the fourth file" >> subdir/file4.txt
echo "This is the fifth file" >> subdir/subsubdir/file5.txt
echo "This is the sixth file" >> subdir/subsubdir/file6.dt
hep-rfm-table add-from-dir table.db . --regex .*.txt
hep-rfm-table display table.db
hep-rfm-table add-from-dir table.db .
hep-rfm-table display table.db
hep-rfm-table remove table.db --files table
hep-rfm-table display table.db
mkdir files
mv subdir *.txt files/.
hep-rfm-table add-from-dir table.db files
hep-rfm-table display table.db
hep-rfm-table create rtable.db
mkdir rfiles
hep-rfm-table replicate rtable.db table.db rfiles `realpath files`
hep-rfm-table display rtable.db
cd ..
rm -r rfm
