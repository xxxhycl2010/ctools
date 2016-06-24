#! /usr/bin/env python
# ==========================================================================
# Perform stacked in-memory analysis of simulated CTA data
#
# Copyright (C) 2014-2016 Juergen Knoedlseder
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ==========================================================================
import gammalib
import ctools
from cscripts import obsutils


# ================== #
# Setup observations #
# ================== #
def setup_observations(pattern='four', ra=83.63, dec=22.01, offset=1.5,
                       emin=0.1, emax=100.0, rad=5.0, duration=180.0,
                       deadc=0.95, caldb='prod2', irf='South_0.5h'):
    """
    Returns an observation container

    Parameters
    ----------
    pattern : str, optional
        Pointing pattern, either 'single' or 'four'
    ra : float, optional
        Right Ascension of pattern centre (deg)
    dec : float, optional
        Declination of pattern centre (deg)
    offset : float, optional
        Offset between observations of pattern (deg)
    emin : float, optional
        Minimum energy (TeV)
    emax : float, optional
        Maximum energy (TeV)
    rad : float, optional
        ROI radius used for analysis (deg)
    duration : float, optional
        Duration of one CTA observation (s)
    deadc : float, optional
        Deadtime correction factor
    caldb : str, optional
        Calibration database path
    irf : str, optional
        Instrument response function

    Returns
    -------
    obs : `~gammalib.GObservations`
        Observation container
    """
    # Set list of observations
    obs_def_list = obsutils.set_obs_patterns(pattern,
                                             ra=ra,
                                             dec=dec,
                                             offset=offset)

    # Get observation container
    obs = obsutils.set_obs_list(obs_def_list,
                                duration=duration,
                                emin=emin,
                                emax=emax,
                                rad=rad,
                                caldb=caldb,
                                irf=irf)

    # Return observation container
    return obs


# =========== #
# Setup model #
# =========== #
def setup_model(obs, model='data/crab.xml'):
    """
    Setup model for analysis

    Parameters
    ----------
    obs : `~gammalib.GObservations`
        Observation container
    model : str, optional
        Model definition XML file

    Returns
    -------
    obs : `~gammalib.GObservations`
        Observation container
    """
    # Append model from file to observation container
    obs.models(gammalib.GModels(model))

    # Return observation container
    return obs


# ================================ #
# Simulation and analysis pipeline #
# ================================ #
def run_pipeline(obs, ra=83.63, dec=22.01, emin=0.1, emax=100.0,
                 enumbins=20, nxpix=200, nypix=200, binsz=0.02,
                 coordsys='CEL', proj='CAR', debug=False):
    """
    Simulation and stacked analysis pipeline

    Parameters
    ----------
    obs : `~gammalib.GObservations`
        Observation container
    ra : float, optional
        Right Ascension of counts cube centre (deg)
    dec : float, optional
        Declination of Region of counts cube centre (deg)
    emin : float, optional
        Minimum energy (TeV)
    emax : float, optional
        Maximum energy (TeV)
    enumbins : int, optional
        Number of energy bins
    nxpix : int, optional
        Number of pixels in X axis
    nypix : int, optional
        Number of pixels in Y axis
    binsz : float, optional
        Pixel size (deg)
    coordsys : str, optional
        Coordinate system
    proj : str, optional
        Coordinate projection
    debug : bool, optional
        Debug function
    """
    # Simulate events
    sim = ctools.ctobssim(obs)
    sim['debug']     = debug
    sim.run()

    # Bin events into counts map
    bin = ctools.ctbin(sim.obs())
    bin['ebinalg']  = 'LOG'
    bin['emin']     = emin
    bin['emax']     = emax
    bin['enumbins'] = enumbins
    bin['nxpix']    = nxpix
    bin['nypix']    = nypix
    bin['binsz']    = binsz
    bin['coordsys'] = coordsys
    bin['proj']     = proj
    bin['xref']     = ra
    bin['yref']     = dec
    bin['debug']    = debug
    bin.run()

    # Create exposure cube
    expcube = ctools.ctexpcube(sim.obs())
    expcube['incube']   = 'NONE'
    expcube['ebinalg']  = 'LOG'
    expcube['emin']     = emin
    expcube['emax']     = emax
    expcube['enumbins'] = enumbins
    expcube['nxpix']    = nxpix
    expcube['nypix']    = nypix
    expcube['binsz']    = binsz
    expcube['coordsys'] = coordsys
    expcube['proj']     = proj
    expcube['xref']     = ra
    expcube['yref']     = dec
    expcube['debug']    = debug
    expcube.run()

    # Create PSF cube
    psfcube = ctools.ctpsfcube(sim.obs())
    psfcube['incube']   = 'NONE'
    psfcube['ebinalg']  = 'LOG'
    psfcube['emin']     = emin
    psfcube['emax']     = emax
    psfcube['enumbins'] = enumbins
    psfcube['nxpix']    = 10
    psfcube['nypix']    = 10
    psfcube['binsz']    = 1.0
    psfcube['coordsys'] = coordsys
    psfcube['proj']     = proj
    psfcube['xref']     = ra
    psfcube['yref']     = dec
    psfcube['debug']    = debug
    psfcube.run()

    # Create background cube
    bkgcube = ctools.ctbkgcube(sim.obs())
    bkgcube['incube']   = 'NONE'
    bkgcube['ebinalg']  = 'LOG'
    bkgcube['emin']     = emin
    bkgcube['emax']     = emax
    bkgcube['enumbins'] = enumbins
    bkgcube['nxpix']    = 10
    bkgcube['nypix']    = 10
    bkgcube['binsz']    = 1.0
    bkgcube['coordsys'] = coordsys
    bkgcube['proj']     = proj
    bkgcube['xref']     = ra
    bkgcube['yref']     = dec
    bkgcube['debug']    = debug
    bkgcube.run()

    # Attach background model to observation container
    bin.obs().models(bkgcube.models())

    # Set Exposure and Psf cube for first CTA observation
    # (ctbin will create an observation with a single container)
    bin.obs()[0].response(expcube.expcube(), psfcube.psfcube(), bkgcube.bkgcube())

    # Perform maximum likelihood fitting
    like = ctools.ctlike(bin.obs())
    like['debug'] = True # Switch this always on for results in console
    like.run()

    # Return
    return


# ======================== #
# Main routine entry point #
# ======================== #
if __name__ == '__main__':

    # Dump header
    print('********************************************')
    print('*      CTA stacked analysis pipeline       *')
    print('********************************************')

    # Setup observations
    obs = setup_observations()

    # Setup model
    obs = setup_model(obs)

    # Run analysis pipeline
    run_pipeline(obs)
