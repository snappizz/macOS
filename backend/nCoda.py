#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------------------------
# Program Name:           fujian
# Program Description:    An HTTP server that executes Python code.
#
# Filename:               fujian/__main__.py
# Purpose:                This starts everything.
#
# Copyright (C) 2015, 2016, 2017 Christopher Antila
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# --------------------------------------------------------------------------------------------------
'''
Main Fujian module.
'''
# from fujian import runner

import subprocess


_FUJIAN_COMMAND = ['python', '-m', 'fujian']
_JULIUS_COMMAND = [
    # '/usr/lib64/ncoda/node_modules/.bin/electron',
    '../Resources/app/node_modules/electron/cli.js',
    # '/usr/share/web-assets/julius/index.html',
    '../Resources/app/index.html'
]


def the_script():

    # hold the Popen instances
    subprocesses = []

    try:
        # start Fujian
        try:
            subprocesses.append(subprocess.Popen(_FUJIAN_COMMAND))
        except subprocess.CalledProcessError as cperr:
            print('Encountered the following error while starting Fujian:\n{}'.format(cperr))
            raise SystemExit(1)

        # start Julius
        try:
            subprocess.call(_JULIUS_COMMAND)
        except KeyboardInterrupt:
            pass

    finally:
        for each_instance in subprocesses:
            # NB: in Python 3, this would raise ProcessLookupError
            try:
                each_instance.terminate()
                each_instance.wait()
            except OSError:
                # that means the process already quit
                pass



if __name__ == '__main__':
    the_script()
else:
    print('Please start nCoda by running from the commandline.')