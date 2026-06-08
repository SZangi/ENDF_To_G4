import zlib
import pandas as pd
import numpy as np
from pyparsing import pyparsing_common, OneOrMore
import os, shutil, sys

atomic_num = 5
atomic_weight = 10
symbol = 'B'
name = "Boron"

#### Step 0.5: Copy the tape we want to the file "ENDFB.IN"
file_name = "a_"+str(atomic_num).zfill(3)+"-"+symbol+"-"+str(atomic_weight).zfill(3)+".dat"
file_path = os.path.join("../../xsdata/jendl5-a",file_name)
shutil.copy(file_path,"PREPRO_Input/ENDFB.IN")

#### Step 1: Process the JENDL File using the PREPRO commands
# This is done via the bash script "prepro.sh"
os.system('./prepro.sh')


#### Step 2: Start processing the PREPRO output
ENDF_out =  open('DICTIN.OUT','r').readlines() #'DICTIN.OUT' should be the last output file from PREPRO reformatting
total_xs = open('total_xs_data.txt','w')

## For carbon13, get ratio of total to a,n cross sections from TENDL,
#  as JENDL's cross section for "non-neutron producing" reactions
#  is about 10 times higher than that predicted by TENDL, at low E.
#  Because Geant predicts that for carbon all low E 
#  reactions are a,n reactions, if you use too high a total
#  cross-section, Geant will overproduce neutrons.
use_inelastic_ratio_flag = False
Oxygen_16_flag = False
line_num = 0

ratio_num_list = [6,5]
ratio_weight_list = [13,10]

if (atomic_num in ratio_num_list and atomic_weight in ratio_weight_list):
    ratio_path = "TENDL_Data/"
    ratio_name = str(atomic_weight)+str(symbol)+"_Tot_an_Ratio_TENDL.csv"
    tot_ine_ratio_df = pd.read_table(os.path.join(ratio_path,ratio_name),names=["Energy","Tot","A_N","Ratio"],header=0,index_col=False,delimiter=";")
    inelastic_E = np.array(tot_ine_ratio_df["Energy"])
    inelastic_ratio = np.array(tot_ine_ratio_df["Ratio"])
    use_inelastic_ratio_flag = True
# Otherwise, we have to trust that JENDL's non-neutron producing cross section is correct
elif (atomic_num == 8 and atomic_weight == 16):
    #Oxygen-16 has no (alpha,n) cross section as the threshold for the reaction is 
    # above 15 MeV, the upper range of data in the JENDL files. Here we instruct 
    # the code to directly write the total reaction cross-section to a Geant4 format file
    Oxygen_16_flag = True

else:
    MT_MF_num = '3  5' 
    inelastic_E = []
    inelastic_xs = []
    for line in ENDF_out:
        if line[71:75] ==MT_MF_num:
            line_num += 1
            if line_num >3:
                E0 = float(line[1:12])
                xs0 = float(line[12:23])
                try:
                    E1 = float(line[23:34])
                    xs1 = float(line[34:45])
                    E2 = float(line[45:56])
                    xs2 = float(line[56:67])
                except:
                    E1 = 0
                    xs1 = 0
                    E2 = 0
                    xs2 = 0

                for energy,xs in zip([E0,E1,E2],[xs0,xs1,xs2]):
                    if energy > 0:
                        inelastic_E.append(energy)
                        inelastic_xs.append(xs)

    inelastic_E = np.array(inelastic_E)
    inelastic_xs = np.array(inelastic_xs)
    inelastic_E = np.append(np.array([0]),inelastic_E)
    inelastic_xs = np.append(np.array([0]),inelastic_xs)


MT_MF_num = '3201' # set this to whichever MT and MF number corresponds with the reaction you want
line_num = 0
num_entries = 0

if Oxygen_16_flag:
    MT_MF_num = '3  5'

alpha_n_filename = str(atomic_num)+'_'+str(atomic_weight)+'an.csv'
if not Oxygen_16_flag:
    an_file = open(alpha_n_filename,'w')
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
                if use_inelastic_ratio_flag:
                    # If this is an isotope where we use the ratio
                    # of total reaction cross-section to (a,n) xs (such as 13C)
                    an_file.write(str(energy)+","+str(xs)+"\n")
                    inE_ratio = np.interp(energy,inelastic_E,inelastic_ratio)
                    tot_xs = inE_ratio*xs
                elif Oxygen_16_flag:
                    # If this is oxygen-16, just write the total cross-section 
                    # directly.
                    tot_xs = xs
                else:
                    an_file.write(str(energy)+","+str(xs)+"\n")
                    inE_xs = np.interp(energy,inelastic_E,inelastic_xs)
                    tot_xs = inE_xs + xs
                tot_line.append(energy)
                tot_line.append(tot_xs)
            tot_xs_string = ' '.join(f"{val:E}" for val in tot_line)
            total_xs.write(tot_xs_string+'\n')
        else:
            total_xs.write(line[1:67]+'\n')
total_xs.close()
an_file.close()

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
output_folder = "G4JENDL_A"
g4format_name = str(atomic_num)+"_"+str(atomic_weight)+"_"+name+".z"
g4format_dest = os.path.join(output_folder,g4format_name)
shutil.move('total_xs_data_J.z',g4format_dest)

#### Last step: Clean up transient files

os.system('rm total_xs_data.txt')
os.system('rm DICTIN.OUT')
