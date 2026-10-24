"""Synthetic engineering input. This is not an observation or a scientific evaluation."""
import sys
from pathlib import Path
import numpy as np
from astropy.io import fits


def write_fixture(directory):
    directory.mkdir(parents=True, exist_ok=True)
    time = np.arange(16000, dtype=float) * 120 / 86400 + 1300
    phase = ((time - 1300.4 + 1.25) % 2.5) - 1.25
    flux = 10000 * (1 - 0.01 * (np.abs(phase) < 0.06))
    flux += np.random.default_rng(42).normal(0, 2, len(time))
    error = np.full(len(time), 2.0)
    primary = fits.PrimaryHDU()
    for key, value in {'OBJECT': 'SYNTHETIC DESKTOP CHECK', 'TICID': 0, 'SECTOR': 1, 'RA_OBJ': 0.,
                       'DEC_OBJ': 0., 'TESSMAG': 10., 'PROCVER': 'engineering-fixture', 'TELESCOP': 'TESS',
                       'CREATOR': 'SyntheticLightCurve', 'ORIGIN': 'Delta engineering fixture'}.items():
        primary.header[key] = value
    columns = [fits.Column(name=name, format='D', array=array) for name, array in (
        ('TIME', time), ('PDCSAP_FLUX', flux), ('PDCSAP_FLUX_ERR', error), ('SAP_FLUX', flux), ('SAP_FLUX_ERR', error))]
    columns.append(fits.Column(name='QUALITY', format='J', array=np.zeros(len(time), dtype=int)))
    table = fits.BinTableHDU.from_columns(columns)
    for key, value in {'TIMESYS': 'TDB', 'TIMEREF': 'SOLARSYSTEM', 'TIMEUNIT': 'd', 'BJDREFI': 2457000,
                       'BJDREFF': 0., 'TSTART': time[0], 'TSTOP': time[-1], 'TIMEDEL': 120 / 86400,
                       'CROWDSAP': 1., 'FLFRCSAP': 1.}.items():
        table.header[key] = value
    fits.HDUList([primary, table]).writeto(directory / 'synthetic_desktop_check_lc.fits', checksum=True)


if __name__ == '__main__':
    write_fixture(Path(sys.argv[1]))
