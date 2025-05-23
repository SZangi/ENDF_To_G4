#! /usr/bin/bash

mkdir PREPRO_Output
cp PREPRO_Input/* PREPRO_Output
cd PREPRO_Output

endf2c
cp LINEAR_1.INP LINEAR.INP
linear
recent
cp LINEAR_2.INP LINEAR.INP
rm LINEAR.OUT
linear
fixup
dictin
rm *.INP

cp DICTIN.OUT ../DICTIN.OUT
cd ../

python3 compressFile.py
rm 'total_xs_data.txt'
rm 'DICTIN.OUT'
