The purpose of this code is to allow a user to convert an ENDF6 file (or any ENDF as PREPRO takes all ENDF file formats) to a zip archive which Geant4 can read in for the ParticleHP module.

Prerequisites:
- PREPRO installed
- python with zlib, and pandas

To Run (New! Shiny! Smooth!):
1. Download your file from JENDL or TENDL (or other ENDF but will require inspecting the file to figure out what cross-section to use)
2. In the JENDL_2_G4.py or TENDL_2_G4.py script, change the isotope name and numbers, and file location to match your chosen isotope + file.
3. Specify the output directory.
4. Run!

Now you should have both a file name Z_A_Name.z in the output directory, and a file named Z_AprojectileX.csv. The *.z can be copied to your $G4PARTICLEHP/{Projectile}/CrossSection directory, and the *.csv is a single column list of the cross-section data you just wrote to a *.z file.

------------------------------------------------------------------------

To Run (Old, more manual):

1. Copy your ENDF file to the PREPRO_Inputs/
2. Rename the file to ENDFB.IN
3. Edit the output file name in compressFile.py to the correct isotope
4. Run the jendl2g4.sh script from the main directory

The output file X_Y_XXX.z will be in the main directory.

Voila! You now have a file which can be copied into your G4TENDL data directory and will be used in any G4 codes running the ParticleHP module!
