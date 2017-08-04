#!/usr/bin/env bash
#
# Copyright 2016 Christopher Antila

echo "Running all the test suites"
# wd: macOS/
cd build/programs
cd julius && npm test && cd ..
cd fujian && py.test && cd ..
# cd lychee && py.test && cd ..
cd mercurial-hug && py.test && cd ..
cd ../..