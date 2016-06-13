#! /usr/bin/env python
# ==========================================================================
# This scripts performs unit tests for the cssens script.
#
# Copyright (C) 2016 Juergen Knoedlseder
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
import os
import gammalib
import cscripts


# ============================ #
# Test class for cssens script #
# ============================ #
class Test(gammalib.GPythonTestSuite):
    """
    Test class for cssens script.

    This test class makes unit tests for the cssens script by using it
    from the command line and from Python.
    """
    
    # Constructor
    def __init__(self):
        """
        Constructor.
        """
        # Call base class constructor
        gammalib.GPythonTestSuite.__init__(self)

        # Return
        return

    # Set test functions
    def set(self):
        """
        Set all test functions.
        """
        # Set test name
        self.name('cssens')

        # Append tests
        self.append(self._test_cmd, 'Test cssens on command line')
        self.append(self._test_python, 'Test cssens from Python')

        # Return
        return

    # Test cssens on command line
    def _test_cmd(self):
        """
        Test cssens on the command line.
        """
        # Kluge to set the command (installed version has no README file)
        if os.path.isfile('README'):
            cssens = '../cscripts/cssens.py'
        else:
            cssens = 'cssens'

        # Setup cssens command
        cmd = cssens+' inmodel="data/crab.xml"'+ \
                     ' srcname="Crab" caldb="prod2" irf="South_0.5h"' + \
                     ' duration=1800.0 rad=3.0 emin=1.0 emax=10.0 bins=1'+ \
                     ' outfile="cssens_cmd1.dat"'+ \
                     ' logfile="cssens_cmd1.log" chatter=1'

        # Execute cssens, make sure we catch any exception
        try:
            rc = os.system(cmd+' >/dev/null 2>&1')
        except:
            pass

        # Check if execution was successful
        self.test_assert(rc == 0,
                         'Successful cssens execution on command line')

        # Check result file
        self._check_result_file('cssens_cmd1.dat')

        # Setup cssens command
        cmd = cssens+' inmodel="model_that_does_not_exist.xml"'+ \
                     ' srcname="Crab" caldb="prod2" irf="South_0.5h"' + \
                     ' duration=1800.0 rad=3.0 emin=1.0 emax=10.0 bins=1'+ \
                     ' outfile="cssens_cmd2.dat"'+ \
                     ' logfile="cssens_cmd2.log" chatter=2'

        # Execute cssens, make sure we catch any exception
        try:
            rc = os.system(cmd+' >/dev/null 2>&1')
        except:
            pass

        # Check if execution failed
        self.test_assert(rc != 0,
                         'Failure of cssens execution on command line')

        # Return
        return

    # Test cssens from Python
    def _test_python(self):
        """
        Test cssens from Python.
        """
        # Set-up cssens
        sens = cscripts.cssens()
        sens['inobs']    = 'NONE'
        sens['inmodel']  = 'data/crab.xml'
        sens['srcname']  = 'Crab'
        sens['caldb']    = 'prod2'
        sens['irf']      = 'South_0.5h'
        sens['outfile']  = 'cssens_py1.dat'
        sens['duration'] = 1800.0
        sens['rad']      = 3.0
        sens['emin']     = 1.0
        sens['emax']     = 10.0
        sens['bins']     = 1
        sens['logfile']  = 'cssens_py1.log'
        sens['chatter']  = 2

        # Run cssens script
        sens.logFileOpen()   # Make sure we get a log file
        sens.run()
        sens.save()

        # Check pull distribution file
        self._check_result_file('cssens_py1.dat')

        # Return
        return

    # Check result file
    def _check_result_file(self, filename):
        """
        Check result file.
        """
        # Open result file as CSV file
        results = gammalib.GCsv(filename, ',')

        # Check dimensions
        self.test_value(results.nrows(), 2, 'Check for 2 rows in sensitivity file')
        self.test_value(results.ncols(), 7, 'Check for 7 columns in sensitivity file')

        # Return
        return
