#!/bin/bash
#
# Reproduce the example to be shown in the documentation.
#
mkdir rfm
cd rfm
hep-rfm-table -h
hep-rfm-table table.db create
echo "My first table file" >> file1.txt
hep-rfm-table table.db add file1 file1.txt
hep-rfm-table table.db display
echo "This is the second file" >> file2.txt
echo "This is the third file" >> file3.txt
hep-rfm-table table.db add_massive file2.txt file3.txt
hep-rfm-table table.db display
mkdir -p subdir/subsubdir
echo "This is the fourth file" >> subdir/file4.txt
echo "This is the fifth file" >> subdir/subsubdir/file5.txt
echo "This is the sixth file" >> subdir/subsubdir/file6.dt
hep-rfm-table table.db add_from_dir . --regex .*.txt
hep-rfm-table table.db display
hep-rfm-table table.db add_from_dir .
hep-rfm-table table.db display
hep-rfm-table table.db remove table
hep-rfm-table table.db display
mkdir files
mv subdir *.txt files/.
hep-rfm-table table.db add_from_dir files
hep-rfm-table table.db display
cd ..
rm -r rfm
