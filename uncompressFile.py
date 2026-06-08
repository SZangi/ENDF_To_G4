import os
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-n','--filename',required=True,help="Name of file to decompress")
    parser.add_argument('-o','--output',required=False,default='Output.txt',help="Name of decompressed file to make")

    args = parser.parse_args()
    filename = args.filename
    output_name = args.output
    if output_name == "Output.txt":
        output_name = filename[:-2]+'.txt'
    

    os.system('zlib-flate -uncompress < '+filename+' > '+output_name)