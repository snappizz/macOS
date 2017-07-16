#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Program Name:           ncbuild
# Program Description:    Script that builds the nCoda Electron app for Posix.
#
# Filename:               nc/ncbuild.py
# Purpose:                This builds and packages everything.
#
# Copyright (C) 2017 Jeff Treviño
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
# -----------------------------------------------------------------------------
'''
Main ncoda build script.
'''
from biplist import readPlist, writePlist
from sys import platform
from os import path
import time
from shutil import copyfile, copytree, rmtree
import os
import subprocess
# call a command line utiity to create an app in a reliable place
# package this app as a disk image using dmgbuild
# requires dmgbuild command line install to work

# programs/julius/node_modules/electron/dist/

# define globals -- assumed relative to macOS directory
PATH_TO_NCODA = os.path.join('dist', 'nCoda.app')
PATH_TO_JULIUS = 'julius'

PATH_TO_APP = os.path.join(
    PATH_TO_NCODA,
    'Contents',
    'Resources',
    'app'
    )


def bundle_electron_app_front_end():
    '''
    Copy files into the bundle's Contents/Resources/app directory.
    '''
    print('Bundling Julius.')
    # copy index.html into app directory
    copyfile(os.path.join(PATH_TO_JULIUS, 'index.html'), os.path.join(PATH_TO_APP, 'index.html'))
    # copyfile(os.path.join(PATH_TO_JULIUS, 'package.json'), os.path.join(PATH_TO_APP, 'package.json'))
    # include these Julius components:
    front_end_dirs = [
        'fonts',
        'js',
        'lib',
        'css',
        'node_modules'
        # os.path.join('node_modules', 'codemirror'),
        # os.path.join('node_modules', 'electron-devtools-installer'),
        # os.path.join('node_modules', 'electron'),
        ]
    # copy Julius dirs into app directory
    for fed in front_end_dirs:
        copytree(
            os.path.join(PATH_TO_JULIUS, fed),
            os.path.join(PATH_TO_APP, fed))

def set_values_for_plist(plist_path):
    print('Customizing PLists.')
    '''
    Given an input path to a valid OSX plist dict,
    customizes the plist's
    CFBundleDisplayName, CFBundleIdentifier and CFBundleName
    '''
    plist_dict = readPlist(plist_path)
    plist_dict['CFBundleDisplayName'] = 'nCoda'
    plist_dict['CFBundleIdentifier'] = 'org.nCoda.nCoda'
    plist_dict['CFBundleName'] = 'nCoda'
    plist_dict['CFBundleIconFile'] = 'ncoda.icns'
    writePlist(plist_dict, plist_path)


def customize_osx_app_bundle():
    '''
    Supplies a custom icon and swaps in custom PList values for app bundle.
    Changes CFBundleDisplayName, CFBundleIdentifier and CFBundleName,
    in both main and helper apps.
    '''
    print('Customizing OS X app bundle.')
    # Where is the helper app?
    # Where are the plists?
    main_plist_path = os.path.join(PATH_TO_NCODA, 'Contents', 'Info.plist')
    # add icon to bundle
    main_icon_path = os.path.join(
        PATH_TO_NCODA,
        'Contents',
        'Resources', 'nCoda.icns')
    copyfile('nCoda.icns', main_icon_path)
    # set plist values for plist file
    set_values_for_plist(main_plist_path)

def bundle_frontend_and_customize_app():
    '''
    Builds OS X Electron.app app bundle or Windows directory from contents of
    Julius and programs dev directories, by adding files to prebuilt Electron
    bin and customizing Plist files, then packages this as a.dmg file (Mac) or
    Installer (Windows).
    '''
    bundle_electron_app_front_end()
    customize_osx_app_bundle()
    time.sleep(0.25)

bundle_frontend_and_customize_app()
