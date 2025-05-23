import zlib
import pandas as pd

ENDF_out =  open('DICTIN.OUT','r').readlines() #'DICTIN.OUT' should be the last output file from PREPRO reformatting
total_xs = open('total_xs_data.txt','w')

MT_MF_num = '3201' # set this to whichever MT and MF number corresponds with the reaction you want
line_num = 0
num_entries = 0

for line in ENDF_out:
    if line[71:75] ==MT_MF_num:
        line_num += 1
        if line_num==3:
            num_entries = line[8:11]
        total_xs.write(line[1:67]+'\n')
total_xs.close()

rewrite = open('totat_xs_G4_format.txt','w')

columns_df = pd.read_table('total_xs_data.txt',delim_whitespace=True,names=['1','2','3','4','5','6'],skiprows=3)

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

with open('totat_xs_G4_format.txt','rb') as input:
    uncomp = input.read()
    input.close()

z = zlib.compress(uncomp)

Name_Of_XS = '4_9_Beryllium_J.z' #This must be in the format A_Z_ElementName.z for replacing TENDL files
                               #I have added a J to prevent overwriting previous files

with open(Name_Of_XS,'wb') as output:
    output.write(z)
    output.close()