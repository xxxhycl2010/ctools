#! /usr/bin/env python
# ==========================================================================
# This Python script creates the node section of the NodeFunction using
# logarithmically spaced energy bins. The intensity scale is set to the
# HESS Crab intensity (assuming a power law).
#
# Copyright (C) 2012-2014 Juergen Knoedlseder
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
#from gammalib import *
import sys
import math


# ============== #
# Write one node #
# ============== #
def write_node(file, energy, scale):
    """
    Writes one node to XML file.
    """
    # Convert to strings
    str_energy = str(energy)
    str_scale  = str(scale)

    # Write start tag
    file.write('      <node>\n')

    # Write energy
    file.write('        <parameter scale="1e6"   name="Energy"')
    file.write('    min="'+str_energy+'"   max="'+str_energy+'"')
    file.write(' value="'+str_energy+'"')
    file.write(' free="0"/>\n')

    # Write intensity
    file.write('        <parameter scale="'+str_scale+'"   name="Intensity"')
    file.write(' min="1e-5"   max="1e5"')
    file.write(' value="1.0"')
    file.write(' free="1"/>\n')

    # Write end tag
    file.write('      </node>\n')

    # Return
    return


# ============ #
# Create nodes #
# ============ #
def create_nodes(emin, emax, enumbins):
    """
    Create nodes (energies in TeV).
    """
    # Open file
    file = open("nodes.xml", "w")

    # Set node boundaries
    elogmin = math.log10(float(emin))
    elogmax = math.log10(float(emax))
    elogbin = (elogmax - elogmin)/(float(enumbins)-1.0)

    # Fill arrays
    for i in range(int(enumbins)):

        # Compute energy
        energy = math.pow(10.0, i*elogbin+elogmin)

        # Compute scale (HESS Crab spectrum)
        scale = 3.45e-17 * math.pow(energy, -2.63)

        # Write node
        write_node(file, energy, scale)

        # Debug
        #sys.stdout.write(energy)
        #sys.stdout.write(math.pow(10.0, int(math.log10(scale))-1.0)±"\n")

    # Close file
    file.close()

    # Return
    return


# ======================= #
# Main script entry point #
# ======================= #
if __name__ == '__main__':
    """
    Compute nodes.
    """
    # Check command line
    usage = "Usage: cta_make_nodes emin emax enumbins"
    if len(sys.argv) < 3:
        sys.stdout.write(usage+"\n")
        sys.exit()

    # Extract parameters
    emin     = sys.argv[1]
    emax     = sys.argv[2]
    enumbins = sys.argv[3]

    # Create nodes
    create_nodes(emin, emax, enumbins)
