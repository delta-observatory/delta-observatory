# Acknowledgments

The public repositories and the example exports use the data and software below.
Keep these statements with any publication or redistribution of the data products.

## Data

**TESS.** This work includes data collected by the TESS mission. Funding for the TESS mission is provided by NASA's Science Mission Directorate.

**MAST.** The TESS data were obtained from the Mikulski Archive for Space Telescopes (MAST) at the Space Telescope Science Institute.
STScI is operated by the Association of Universities for Research in Astronomy, Inc., under NASA contract NAS5-26555.
The light curves belong to the MAST collection "TESS Light Curves - All Sectors", [doi:10.17909/t9-nmc8-f686](https://doi.org/10.17909/t9-nmc8-f686).

**NASA Exoplanet Archive.** This research has made use of the NASA Exoplanet Archive, which is operated by the California Institute of Technology, under contract with the National Aeronautics and Space Administration under the Exoplanet Exploration Program.
The reference planet values come from the Planetary Systems Table, [doi:10.26133/NEA12](https://doi.org/10.26133/NEA12).
Each observation label in the application names the publication of its reference values.

**Star catalogue of the sky display.** The display uses star positions, magnitudes, and colours from XHIP: Anderson, E., and Francis, C. 2012, Astronomy Letters, 38, 331 (VizieR V/137D).
This research has made use of the VizieR catalogue access tool, CDS, Strasbourg, France.

## Software and assets

**Lightkurve.** This research made use of Lightkurve, a Python package for Kepler and TESS data analysis (Lightkurve Collaboration, 2018).

**Astropy.** This research made use of Astropy, a community-developed core Python package for Astronomy (Astropy Collaboration, 2013, 2018, 2022). The `tess-bls` method uses its `BoxLeastSquares` implementation.

**d3-celestial.** The star and constellation files of the sky display come from d3-celestial 0.7.35, Copyright (c) 2015, Olaf Frohn, under the BSD 3-Clause licence.
The frontend keeps the licence text in `public/sky/LICENSE-d3-celestial`.

**Fonts.** The interface loads IBM Plex Sans and IBM Plex Mono from Google Fonts under the SIL Open Font License 1.1. The repositories do not include the font files.

## Dependency licences

The repositories contain source code only. They do not include their dependencies.
The worker uses `fitsio` (GPL-2.0-or-later). The API and the worker use `psycopg` (LGPL-3.0).
A published container image would contain these packages. It must then include their licence texts and offer their source.
