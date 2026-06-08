import zlib
import pandas as pd
import numpy as np
import argparse as ap
from pyparsing import pyparsing_common, OneOrMore
import os, shutil, sys

def process_one_tape(mf_mt_number,endf_file):

    energy_list = []
    xs_list = []

    float_type = pyparsing_common.number
    number_list = OneOrMore(float_type)
    line_num = 0

    for line in endf_file:
        if line[71:75] ==mf_mt_number:
            line_num += 1
            if line_num==3:
                num_entries = line[8:11]
            elif line_num >=3:
                line_list = number_list.parse_string(line[1:67],parse_all=True).as_list()
                for energy,xs in zip(line_list[::2],line_list[1::2]):
                    energy_list.append(energy)
                    xs_list.append(xs)

    return energy_list,xs_list

def generate_g4ndl_file(energies, crosssections, num_entries):
    rewrite = open('total_xs_G4_format_new.txt','w')

    rewrite.write('  0\n')
    rewrite.write('  0\n')
    rewrite.write('  '+str(num_entries)+'\n')

    line_entries = 0

    for energy,xs in zip(energies,crosssections):
        eString = '%E' % energy
        xsString = '%E' % xs
        string = eString+' '+xsString+' '
        
        line_entries += 1
        if line_entries == 3:
            string += '\n'
            line_entries = 0
        
        if (string != 'NAN'):
            rewrite.write(string)
    rewrite.close()


def process_endf_tape(input_file, elements, output_dir):
    shutil.copy(input_file,"PREPRO_Input/ENDFB.IN")
    
    #### Step 1: Process the JENDL File using the PREPRO commands
    # This is done via the bash script "prepro.sh"
    os.system('./prepro.sh')


    #### Step 2: Start processing the PREPRO output
    ENDF_out =  open('DICTIN.OUT','r').readlines() #'DICTIN.OUT' should be the last output file from PREPRO reformatting
    isotope_line = ENDF_out[5].split()
    
    element_symbol = isotope_line[0].split('-')[1]
    atomic_weight = int(ENDF_out[5][7:11])
    
    element_name = elements['Element'].loc[element_symbol]
    atomic_num = elements['AtomicNumber'].loc[element_symbol]

    MT_nums = []

    start_reading = False
    for line in ENDF_out:
        if line[71:75] =='1451':
            if line[65] =='1' or line[65] =='0':
                if start_reading:
                    mfmt_num = line[:60].split()
                    if float(mfmt_num[0]) < 1000:
                        MT_nums.append(int(mfmt_num[1]))
            if line[1:66] == '**************** Program DICTIN (VERSION 2023-1) ****************':
                start_reading = True
    
    #print(MT_nums)
    # Assume that the total non-elastic cross section is unavailable
    # Collect MT3 MF numbers for summing to calculate the total non-elastic, 
    # folloiwng ENDF sum rules.

    summing = True
    summing_MTs = [4,5,16,27,11,17,22,23,24,25,26,28,29,30,31,32,33,34,35,36,37,41,42,44,45,152,153,154,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,183,184,185,186,187,188,189,190,194,195,196,198,199,200]
    MT_MF_nums = ['3'+ (3-len(str(mt)))*' ' + str(mt) for mt in MT_nums if (mt in summing_MTs) ]
    
    # Only include MT-201 if MT-4 is not available. 
    # These are redundant as MT-201 is a special MT number.
    if ('3  4' not in MT_MF_nums) and (201 in MT_nums):
        MT_MF_nums.append('3201')
    

    # If the total non-elastic (MT-3) xs is available, use that instead
    if 3 in MT_nums:
        MT_MF_num = '3  3'
        summing = False

    reaction_energy_lists = []
    reaction_xs_lists = []

    if summing:
        for MT_MF_number in MT_MF_nums:
            print('Processing MT MF Number:',MT_MF_number)
            one_rx_energy, one_rx_xs = process_one_tape(MT_MF_number,ENDF_out)
            reaction_energy_lists.append(one_rx_energy)
            reaction_xs_lists.append(one_rx_xs)

    else:
        print('Processing MT MF Number:',MT_MF_num)
        one_rx_energy, one_rx_xs = process_one_tape(MT_MF_num,ENDF_out)
        reaction_energy_lists.append(one_rx_energy)
        reaction_xs_lists.append(one_rx_xs)

    # Find the longest MT number, ie. whichever reaction has the most entries
    dense_energy_vals = []
    num_entries = 0
    for nrg_list in reaction_energy_lists:
        if len(nrg_list) > num_entries:
            dense_energy_vals = nrg_list
            num_entries = len(nrg_list)
    
    # Calculate the total cross section as the sum of the individual reactions,
    # with values linearly interpolated when not provided in the cross section.
    total_xs_vals = np.zeros_like(dense_energy_vals)
    for reaction_xs, reaction_energy in zip(reaction_xs_lists,reaction_energy_lists):
        interped_xs = np.interp(dense_energy_vals,reaction_energy,reaction_xs)
        total_xs_vals += interped_xs

    # Generate the human readable Geant4-Nuclear-Data-Libraries (G4NDL) formatted 
    # data file from the total cross sections
    generate_g4ndl_file(dense_energy_vals,total_xs_vals,num_entries)

    humanReadable_filename = str(atomic_num)+'_'+str(atomic_weight)+'.csv'
    shutil.copy('total_xs_G4_format_new.txt',os.path.join(output_dir,humanReadable_filename))

    # Compress the file to the zlib format necessary
    # for G4 data file conventions.

    with open('total_xs_G4_format_new.txt','rb') as input:
        uncomp = input.read()
        input.close()

    z = zlib.compress(uncomp)

    Name_Of_XS = 'total_xs_data_J.z' #This must be in the format A_Z_ElementName.z for replacing G4NDL files
                                #I have added a J to prevent overwriting previous files

    with open(Name_Of_XS,'wb') as output:
        output.write(z)
        output.close()

    ### Rename the processed file to the correct name
    output_folder = output_dir
    g4format_name = str(atomic_num)+"_"+str(atomic_weight)+"_"+element_name+".z"
    g4format_dest = os.path.join(output_folder,g4format_name)
    shutil.move('total_xs_data_J.z',g4format_dest)

    #### Last step: Clean up transient files

    os.system('rm total_xs_G4_format_new.txt')
    os.system('rm DICTIN.OUT')

    print('G4NDL Formatted File for '+element_symbol+'-'+str(atomic_weight)+' written to:',g4format_dest)

    #---------------------------------------------------------------#

def load_element_names():
    element_table_df = pd.read_csv("PeriodicTableofElements.csv",header=0,sep=',',index_col=2)
    return element_table_df

if __name__ =="__main__":
    parser = ap.ArgumentParser()
    parser.add_argument("-inp", "--input-directory",required=True,type=str,help="Path to input directory containing the ENDF formatted TENDL files.")
    parser.add_argument("-out", "--output-directory",required=True,type=str,help="Path to output directory where Geant4 *.z files will be written.")
    parser.add_argument("-i","--isotope",required=False,type=str,help="Specific isotope to process")
    parser.add_argument("-aw","--atomic-weight",required=False,type=int,help="Atomic weight of the isotope (for TENDL)")
    parser.add_argument("-fn","--file-name",required=False,type=str,help="Filename for individual input file")
    
    args = parser.parse_args()
    
    process_folder = True
    input_directory = args.input_directory
    output_directory = args.output_directory

    elements = load_element_names()

    # if a specific isotope is specified, only process that one
    if args.isotope:
        process_folder = False
        if not args.file_name:
            # Assume we want the proton incident TENDL file of a specific isotope
            file_name = "p-"+args.isotope+str(args.atomic_weight).zfill(3)+".tendl"
        else:
            file_name = args.file_name
        file_path = os.path.join(input_directory,file_name)
        process_endf_tape(file_path,elements,output_directory)
    
    # otherwise, process everything in the specified directory
    # If there are non-files in there, this will break.
    # The os package appears to not recognize *.tendl files as files so the 
    # "isfile" type check will skip all tendl files is implemented 
    # ... a bit of a problem for processing the TENDL database
    else:
        file_paths = [os.path.join(input_directory,f) for f in os.listdir(input_directory)]
        print(file_paths)
        
        for file_path in file_paths:
            process_endf_tape(file_path,elements,output_directory)
        
        print("\n****************PROCESSING COMPLETE****************************\n")
        print("All files processed. Zipped files written to:", output_directory+'/')
        print("\n***************************************************************\n")

    