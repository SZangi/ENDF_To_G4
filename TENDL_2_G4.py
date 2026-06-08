import zlib
import pandas as pd
import numpy as np
from pyparsing import pyparsing_common, OneOrMore
import os, shutil, sys


atomic_num = 74
atomic_weight = 186
symbol = 'W'
name = "Tungsten"

#### Step 0.5: Copy the tape we want to the file "ENDFB.IN"
file_name = "p-"+symbol+str(atomic_weight).zfill(3)+".tendl"
file_path = os.path.join("../LMNT/Tendl_data/",file_name)
print(file_path)


shutil.copy(file_path,"PREPRO_Input/ENDFB.IN")


#### Step 1: Process the JENDL File using the PREPRO commands
# This is done via the bash script "prepro.sh"
os.system('./prepro.sh')


#### Step 2: Start processing the PREPRO output
ENDF_out =  open('DICTIN.OUT','r').readlines() #'DICTIN.OUT' should be the last output file from PREPRO reformatting
total_xs = open('total_xs_data.txt','w')


MT_MF_num = '3  3' # set this to whichever MT and MF number corresponds with the reaction you want
line_num = 0
num_entries = 0


humanReadable_filename = str(atomic_num)+'_'+str(atomic_weight)+'pX.csv'
readable_file = open(humanReadable_filename,'+w')

float_type = pyparsing_common.number
number_list = OneOrMore(float_type)

for line in ENDF_out:
    if line[71:75] ==MT_MF_num:
        line_num += 1
        if line_num==3:
            num_entries = line[8:11]
            total_xs.write(line[1:67]+'\n')
        elif line_num >=3:
            line_list = number_list.parse_string(line[1:67],parse_all=True).as_list()
            tot_line = []
            for energy,xs in zip(line_list[::2],line_list[1::2]):
                readable_file.write(str(energy)+","+str(xs)+"\n")
                tot_xs = xs
                tot_line.append(energy)
                tot_line.append(tot_xs)
            tot_xs_string = ' '.join(f"{val:E}" for val in tot_line)
            total_xs.write(tot_xs_string+'\n')
        else:
            total_xs.write(line[1:67]+'\n')
total_xs.close()
readable_file.close()

rewrite = open('total_xs_G4_format.txt','w')

columns_df = pd.read_table('total_xs_data.txt',names=['1','2','3','4','5','6'],skiprows=3,delim_whitespace=True)

rewrite.write('  0\n')
rewrite.write('  0\n')
rewrite.write('  '+str(num_entries)+'\n')

for line in range(len(columns_df)):
    for column in columns_df.keys():
        string = '%E' % columns_df[column][line]
        if (string != 'NAN'):
            rewrite.write(string+' ')
    rewrite.write('\n')
rewrite.close()

## compress a file in any format to the zlib format necessary
# for G4 data file conventions.

with open('total_xs_G4_format.txt','rb') as input:
    uncomp = input.read()
    input.close()

z = zlib.compress(uncomp)

Name_Of_XS = 'total_xs_data_J.z' #This must be in the format A_Z_ElementName.z for replacing TENDL files
                               #I have added a J to prevent overwriting previous files

with open(Name_Of_XS,'wb') as output:
    output.write(z)
    output.close()


### Rename the processed file to the correct name
output_folder = "G4TENDL_25_P"
g4format_name = str(atomic_num)+"_"+str(atomic_weight)+"_"+name+".z"
g4format_dest = os.path.join(output_folder,g4format_name)
shutil.move('total_xs_data_J.z',g4format_dest)

#### Last step: Clean up transient files

os.system('rm total_xs_data.txt')
os.system('rm DICTIN.OUT')
