# ParticleHP Data format notes

TLDR; The ParticleHP data is just a .z compressed version of the TENDL MF-3 MT-3 file with the ENDF tape number stripped out. Using the zlib package to compress that section of a TENDL file should just work.

ParticleHP uses inelastic cross-section data, usually contained in the MT-3 (z,non-elastic) section of the ENDF tape. If the MF-3 MT-3 tape does not exist (like in JENDL files), you can calculate what it would be based off of the ENDF summation rules, defined in secion 0.4.3.11 of the ENDF format manual. 

The specific format for a G4NDL file (the files that ParticleHP reads) would like the following for a data file with 50 entries:
```
    0 # dummy row
    0 # dummy row
    50 # number of entries
1.500000E+05 1.000000E-04 1.000000E+06 1.100000E+01 1.100000E+06 1.200000E+01
1.200000E+06 1.700000E+01 1.300000E+06 2.000000E+01 1.400000E+06 2.100000E+01
...             ...             ...         ...         ...         ...
...             ...             ...         ...         ...         ...
...             ...             ...         ...         ...         ...
4.900000E+06 1.000000E+02 5.000000E+06 2.000000E+02  

```

The data entries should be laid out in E, $\sigma$ pairs, going left to right with three pairs per row. Each value should be a string in %E5 format, seperated by a space.

Once the data is arranged in the proper format it should be zipped with standard zlib compression to a *.z file. Then, to get Geant4 to use the file, you should determine where the datafiles live from your $PARTICLEHPDATA variable, then navigate to first the correct indicent particle directory, ie. Proton, Alpha, etc. then to the "Inelastic/CrossSections" directory.

Once there, copy the zipped file you created into this directory, replacing the existing file (be sure to save a copy of the previous file if you want to use it again). After the new file has been copied over, Geant will use that instead, and you should be good to go!