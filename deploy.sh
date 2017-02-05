#!/bin/bash

GH_REPO="@github.com/nCoda/macOS.git"

FULL_REPO="https://$DEPLOY_TOKEN$GH_REPO"

git add nCoda.dmg
git commit -m "deployed to github pages"
git push $FULL_REPO main