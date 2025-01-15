The purpose of this code is to allow a user to convert an ENDF6 file (or any ENDF as PREPRO takes all ENDF file formats) to a zip archive which Geant4 can read in for the ParticleHP module.

Prerequisites:
PREPRO installed
python with zlib, and pandas

To Run:

1. Copy your ENDF file to the PREPRO_Inputs/
2. Rename the file to ENDFB.IN
3. Edit the output file name in compressFile.py to the correct isotope
4. Run the jendl2g4.sh script from the main directory

The output file X_Y_XXX.z will be in the main directory.

Voila! You now have a file which can be copied into your G4TENDL data directory and will be used in any G4 codes running the ParticleHP module!
