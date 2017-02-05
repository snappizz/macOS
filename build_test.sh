#!/usr/bin/env bash
#
# Copyright 2016 Christopher Antila

echo "Running all the test suites"
cd julius
npm test
cd ..
py.test fujian
py.test lychee
py.test mercurial-hug