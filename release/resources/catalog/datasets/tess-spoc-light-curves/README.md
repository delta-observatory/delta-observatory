# TESS SPOC light curves

This desktop prototype supports local TESS SPOC 120-second light-curve files.
The application includes no observations, reference labels, or private experiment records.
[MAST](https://archive.stsci.edu/missions-and-data/tess) supplies the public TESS products.

## Import

1. Select **File → Import TESS light curves** in the desktop menu.
2. Select files whose names end in `_lc.fits`.

The desktop copies the selected files into its separate workspace.
The worker checks the FITS checksums, required columns, and time conventions.
Invalid files produce findings instead of valid observations.
The original files remain unchanged.

## Scientific limits

The `tess-bls` method is provisional.
Its default preparation can change transit depth.
The prototype does not establish completeness, false-alarm rates, or planet confirmation.
An engineering test with synthetic data checks execution only.
