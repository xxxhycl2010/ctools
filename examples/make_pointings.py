#! /usr/bin/env python
# ==========================================================================
# Generates pointing patterns for CTA observations
#
# Copyright (C) 2015-2016 Juergen Knoedlseder
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
import sys
import math
import gammalib


# ============================================================ #
# Get positions of pointings on sky for an interleaved pattern #
# ============================================================ #
def get_positions(xmin, xmax, ymin, ymax, step):
    """
    Get pointing positions for an interleaved pattern

    Get positions for a patch of interleaved pointings on the sky.
    The function does respect the latitude dependence of the
    pointing distance. The step parameter is for a latitude of
    zero.

    Parameters
    ----------
    xmin : float
        Minimum longitude (deg)
    xmax : float
        Maximum longitude (deg)
    ymin : float
        Minimum latitude (deg)
    ymax : float
        Maximum latitude (deg)
    step : float
        Pointing step size (deg)

    Returns
    -------
    positions : list of dict
        List of dictionaries with x and y positions
    """
    # Initialise positions
    positions = []

    # Determine ystep and number of pointing rows
    ystep   = step * math.sqrt(0.75)
    ny      = int((ymax-ymin)/ystep+1.5)
    rescale = (ymax-ymin)/(ystep*(ny-1))
    ystep  *= rescale
    print('Number of rows ....: %d' % (ny))

    # Loop over rows
    y = ymin
    for row in range(ny):

        # Determine xstep and number of pointings in row. The xstep increases
        # with the cosine of the latitude so that the distance of the step
        # is invariant of latitude.
        xstep   = step / math.cos(gammalib.deg2rad * y)
        nx      = int((xmax-xmin)/xstep+1.5)
        rescale = (xmax-xmin)/(xstep*(nx-1))
        xstep  *= rescale

        # Set x offset. For every second row the x position is displace by
        # half a step size.
        if row % 2 == 0:
            x = xmin
        else:
            x = xmin + 0.5 * xstep

        # Append pointings
        for pnt in range(nx):
            positions.append({'x': x, 'y': y})
            x += xstep
            if x >= 360.0:
                x -= 360.0

        # Increment y
        y += ystep

    # Return positions
    return positions


# ====================== #
# Setup patch on the sky #
# ====================== #
def set_patch(lmin=-30.0, lmax=30.0, bmin=-1.5, bmax=+1.5,
              separation=3.0, hours=100.0,
              site=None, caldb='prod2', lst=True, autodec=0.0):
    """
    Setup pointing patch on the sky

    Parameters
    ----------
    lmin : float, optional
        Minimum Galactic Longitude (deg)
    lmax : float, optional
        Maximum Galactic Longitude (deg)
    bmin : float, optional
        Minimum Galactic Latitude (deg)
    bmax : float, optional
        Maximum Galactic Latitude (deg)
    separation : float, optional
        Pointing separation (deg)
    hours : float, optional
        Total observation duration (h)
    site : str, optional
        Array site (one of 'Automatic', 'South', 'North')
    lst : bool, optional
        Use LSTs
    autodec : float, optional
        Declination for switching automatically between South and North site

    Returns
    -------
    obsdef : list of dict
        List of pointing definitions
    """
    # Initialise observation definition
    obsdef = []

    # Get pointing positions
    pointings = get_positions(lmin, lmax, bmin, bmax, separation)

    # Determine number of pointings and pointing duration
    n_pnt    = len(pointings)
    duration = hours*3600.0/float(n_pnt)

    # Observing time collectors
    exposure_south = 0.0
    exposure_north = 0.0

    # Set observations
    for pnt in pointings:

        # Set positions and duration
        obs = {'lon': pnt['x'], 'lat': pnt['y'], 'duration': duration}

        # Optionally add-in site dependent IRF
        if site != None:

            # If automatic site switching is requested then set the North
            # IRF for declinations greater or equal than "autodec" and the
            # South IRF for declination smaller than "autodec".
            if site == 'Automatic':
                pos = gammalib.GSkyDir()
                pos.lb_deg(pnt['x'], pnt['y'])
                dec = pos.dec_deg()
                if (dec >= autodec):
                    obs_site = 'North'
                else:
                    obs_site = 'South'

            # ... otherwise use the specified site, North or South
            else:
                obs_site = site

            # Set IRF
            irf = set_irf(obs_site, obs, caldb, lst=lst)

            # Set IRF information
            obs['caldb'] = caldb
            obs['irf']   = irf

            # Add up exposure for a given site
            if obs_site == 'North':
                exposure_north += duration
            else:
                exposure_south += duration

        # Append observation
        obsdef.append(obs)

    # Dump statistics
    print('Number of pointings: %d (%.2f s)' % (n_pnt,duration))
    print('South array .......: %.2f hours (%.2f%%)' %
          (exposure_south/3600.0,
           100.0*exposure_south/(exposure_south+exposure_north)))
    print('North array .......: %.2f hours (%.2f%%)' %
          (exposure_north/3600.0,
           100.0*exposure_north/(exposure_south+exposure_north)))

    # Return observation definition
    return obsdef


# ================================== #
# Setup Instrument Response Function #
# ================================== #
def set_irf(site, obs, caldb, lst=True):
    """
    Setup Instrument Response Function

    Parameters
    ----------
    site : str
        Array site (either 'South' or 'North')
    obs : dict
        Dictionary with pointing information
    caldb : str
        Calibration database
    lst : bool, optional
        Use LSTs

    Returns
    -------
    irf : str
        IRF name
    """
    # Handle 'prod2'
    if caldb == 'prod2':
        if site == 'North':
            irf = 'North_50h'
        else:
            irf = 'South_50h'

    # Handle 'prod3'
    elif caldb == 'prod3':

        # Compute Right Ascension and Declination of pointing
        pnt = gammalib.GSkyDir()
        pnt.lb_deg(obs['lon'], obs['lat'])
        ra  = pnt.ra_deg()
        dec = pnt.dec_deg()

        # Set geographic latitude of array
        if site == 'North':
            geolat = +28.7569
        else:
            geolat = -24.58

        # Compute best possible zenith angle
        zenith = abs(dec - geolat)

        # Set IRF
        if site == 'North':
            irf = 'North_50h'
        else:
            irf = 'South_50h'
        if zenith < 30.0:
            irf += '_z20'
        else:
            irf += '_z40'

    # ... otherwise return an empty string
    else:
        irf = ''

    # Return IRF
    return irf


# =========================== #
# Setup Galactic plane survey #
# =========================== #
def set_gps(separation=3.0, bmin=-1.3, bmax=1.3, caldb='prod2', lst=True):
    """
    Setup Galactic plane survey

    Parameters
    ----------
    separation : float, optional
        Pointing separation (deg)
    bmin : float, optional
        Minimum Galactic Latitude (deg)
    bmax : float, optional
        Maximum Galactic Latitude (deg)
    caldb : str, optional
        Calibration database name
    lst : bool, optional
        Use LSTs

    Returns
    -------
    obsdef : list of dict
        List of pointing definitions
    """
    # Initialise observation definition
    obsdef = []

    # Add inner region South
    obsdef.extend(set_patch(lmin=-60.0, lmax=60.0, bmin=bmin, bmax=bmax,
                            separation=separation, hours=780,
                            site='South', caldb=caldb, lst=lst))

    # Add Vela & Carina region
    obsdef.extend(set_patch(lmin=240.0, lmax=300.0, bmin=bmin, bmax=bmax,
                            separation=separation, hours=180,
                            site='South', caldb=caldb, lst=lst))

    # Add 210-240 region
    obsdef.extend(set_patch(lmin=210.0, lmax=240.0, bmin=bmin, bmax=bmax,
                            separation=separation, hours=60,
                            site='South', caldb=caldb, lst=lst))

    # Add Cygnus, Perseus
    obsdef.extend(set_patch(lmin=60.0, lmax=150.0, bmin=bmin, bmax=bmax,
                            separation=separation, hours=450,
                            site='North', caldb=caldb, lst=lst))

    # Add Anticentre
    obsdef.extend(set_patch(lmin=150.0, lmax=210.0, bmin=bmin, bmax=bmax,
                            separation=separation, hours=150,
                            site='North', caldb=caldb, lst=lst))

    # Return observation definition
    return obsdef


# ========================== #
# Setup Extragalactic survey #
# ========================== #
def set_extgal(separation=3.0, caldb='prod2', lst=True):
    """
    Setup Extragalactic survey.

    Parameters
    ----------
    separation : float, optional
        Pointing separation (deg)
    caldb : str, optional
        Calibration database name
    lst : bool, optional
        Use LSTs

    Returns
    -------
    obsdef : list of dict
        List of pointing definitions
    """
    # Initialise observation definition
    obsdef = []

    # Set patch
    obsdef.extend(set_patch(lmin=-90.0, lmax=90.0, bmin=+5.0, bmax=+88.0,
                            separation=separation, hours=1000,
                            site='Automatic', caldb=caldb, lst=lst,
                            autodec=10.0))

    # Return observation definition
    return obsdef


# ========================= #
# Setup Galactic centre KSP #
# ========================= #
def set_gc(caldb='prod2', lst=True):
    """
    Setup Galactic centre KSP.

    Parameters
    ----------
    caldb : str, optional
        Calibration database name
    lst : bool, optional
        Use LSTs

    Returns
    -------
    obsdef : list of dict
        List of pointing definitions
    """
    # Initialise observation definition
    obsdef = []

    # Central wobble
    obsdef.extend(set_patch(lmin=-0.5, lmax=0.5, bmin=-0.5, bmax=0.5,
                            separation=0.1, hours=525,
                            site='South', caldb=caldb, lst=lst))

    # Extended region
    obsdef.extend(set_patch(lmin=-10.0, lmax=10.0, bmin=-10.0, bmax=10.0,
                            separation=1.5, hours=300,
                            site='South', caldb=caldb, lst=lst))

    # Return observation definition
    return obsdef


# ============= #
# Setup LMC KSP #
# ============= #
def set_lmc(hours=250.0, caldb='prod2', lst=True):
    """
    Setup LMC KSP.

    Parameters
    ----------
    hours : float, optional
        Total observation duration (h)
    caldb : str, optional
        Calibration database name
    lst : bool, optional
        Use LSTs

    Returns
    -------
    obsdef : list of dict
        List of pointing definitions
    """
    # Initialise observation definition
    obsdef = []

    # Set LMC centre
    centre = gammalib.GSkyDir()
    centre.radec_deg(80.0, -69.0)

    # Set offset angle and number of pointings
    offset = 1.0 # degrees
    n_pnt  = 12

    # Prepare computations
    dphi     = 360.0/n_pnt
    duration = hours*3600.0/float(n_pnt)

    # Loop over pointings
    for ipnt in range(n_pnt):

        # Compute pointing direction
        pnt = centre.copy()
        pnt.rotate_deg(ipnt*dphi, offset)
        lon = pnt.l_deg()
        lat = pnt.b_deg()

        # Set positions and duration
        obs = {'lon': lon, 'lat': lat, 'duration': duration}

        # Set IRF
        irf = set_irf('South', obs, caldb, lst=lst)

        # Add IRF
        obs['caldb'] = caldb
        obs['irf']   = irf

        # Append observation
        obsdef.append(obs)

    # Dump statistics
    print('Number of pointings: %d (%.2f s)' % (n_pnt,duration))

    # Return observation definition
    return obsdef


# ======================================= #
# Write observation definition dictionary #
# ======================================= #
def write_obsdef(filename, obsdef):
    """
    Write observation definition file

    Parameters
    ----------
    filename : str
        Observation definition file name
    obsdef : list of dict
        List of pointing definitions
    """
    # Open file
    file = open(filename, 'w')

    # Write header
    file.write('ra,dec,duration,caldb,irf\n')

    # Loop over pointings
    for obs in obsdef:

        # If we have lon,lat then convert into RA,Dec
        if 'lon' in obs and 'lat' in obs:
            lon = obs['lon']
            lat = obs['lat']
            dir = gammalib.GSkyDir()
            dir.lb_deg(lon,lat)
            ra  = dir.ra_deg()
            dec = dir.dec_deg()
        else:
            ra  = obs['ra']
            dec = obs['dec']

        # Write information
        file.write('%8.4f,%8.4f,%.4f,%s,%s\n' %
                   (ra, dec, obs['duration'], obs['caldb'], obs['irf']))

    # Close file
    file.close()

    # Return
    return


# ============== #
# Make pointings #
# ============== #
def make_pointings():
    """
    Make pointings
    """
    # Initialise flags
    need_help = False

    # Test for command line arguments
    if (len(sys.argv) > 1):
        if sys.argv[1] == '-h':
            need_help = True
        else:
            obsname = sys.argv[1]
    else:
        need_help = True

    # Print help if needed and exit
    if need_help:
        print('Usage: make_pointing.py [OPTIONS]')
        print('     -h       Display this usage message')
        print('     gps      Galactic plane survey (2 row scheme)')
        print('     gps3     Galactic plane survey (3 row scheme)')
        print('     extgal   Extragalactic survey')
        print('     gc       Galactic centre survey')
        print('     lmc      LMC survey')
        sys.exit()

    # Set calibration database
    caldb = 'prod3'
    lst   = True

    # Galactic plane survey
    if obsname == 'gps':
        obsdef = set_gps(caldb=caldb, lst=lst)
        write_obsdef('gps.dat', obsdef)
    elif obsname == 'gps3':
        obsdef = set_gps(separation=1.5, caldb=caldb, lst=lst)
        write_obsdef('gps3.dat', obsdef)

    # Extragalactic survey
    elif obsname == 'extgal':
        obsdef = set_extgal(caldb=caldb, lst=lst)
        write_obsdef('extgal.dat', obsdef)

    # Galactic centre
    elif obsname == 'gc':
        obsdef = set_gc(caldb=caldb, lst=lst)
        write_obsdef('gc.dat', obsdef)

    # LMC
    elif obsname == 'lmc':
        obsdef = set_lmc(caldb=caldb, lst=lst)
        write_obsdef('lmc.dat', obsdef)

    # Invalid pattern
    else:
        print('Unknown option "' + obsname + '"')

    # Return
    return


# ======================== #
# Main routine entry point #
# ======================== #
if __name__ == '__main__':

    # Make pointings
    make_pointings()
