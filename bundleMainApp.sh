#!/usr/bin/env bash
#
# Copyright 2016 Jeff Trevino


#first back
if ! [ -d build ]
then
    mkdir build
    cp nCoda.icns build/
    cp nCoda.py build/
    cp setup.py build/
    cp electron_main_production.js build/
    cp production_requirements.txt build/
    cp package.json build/
    cd build # -> macOS/build/
    virtualenv backend_venv
    source backend_venv/bin/activate
    pip install -r production_requirements.txt
    mkdir programs
    cd programs # -> macOS/build/programs/
    git clone https://github.com/nCoda/ShelfExtender.git ShelfExtender
    git clone https://github.com/nCoda/hgdemo_config.git hgdemo_config
    cd ShelfExtender && pip install . && cd ..
    cd hgdemo_config && python -m shelfex && cd ..
    cp -r hgdemo_config/repo hgdemo
    cd .. # -> macOS/build/

else
    cp nCoda.icns build/
    cp nCoda.py build/
    cp setup.py build/
    cp electron_main_production.js build/
    cp production_requirements.txt build/
    cp package.json build/
    rm -rf build/build
    rm -rf build/dist
    rm -rf build/nCoda.dmg
    cd build # -> macOS/build/
    source backend_venv/bin/activate
fi

if ! [ -d dist ]
then
    python setup.py py2app
fi

# and then front
if ! [ -d julius ]
then
    git clone --recursive https://github.com/nCoda/julius.git julius
    cd julius && npm install && cd .. # -> macOS/build/
fi
# build Electron app

cd julius && node_modules/.bin/browserify js/ncoda-init.js --outfile js/ncoda-compiled.js && cd ..
cd julius && node_modules/.bin/lessc css/ncoda/main.less css/ncoda/main.css && cd ..
cp package.json julius/
pwd
mv electron_main_production.js julius/js/electron_main.js
rm -rf julius/nCoda-darwin-x64
cd julius && electron-packager . --icon=../nCoda.icns && cd ..
cp -r dist/nCoda.app julius/nCoda-darwin-x64/nCoda.app/Contents/Resources/
cd ..
# wd: macOS/
mkdir dist && cd dist # -> macOS/dist
hdiutil create -srcfolder ../build/julius/nCoda-darwin-x64/nCoda.app nCoda.dmg
deactivate
cd .. # -> macOS/
