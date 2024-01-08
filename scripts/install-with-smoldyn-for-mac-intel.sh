#!/bin/bash

# The following script serves as a utility for installing this repository with the Smoldyn requirement on a Intel Mac

set -e

# set installation parameters
dist_url=https://www.smoldyn.org/smoldyn-2.72-mac-Intel.tgz
tarball_name=smoldyn-2.72-mac.tgz
dist_dir=${tarball_name%.tgz}

# uninstall existing version
pip uninstall smoldyn || return

# download the appropriate distribution from smoldyn
wget $dist_url

# extract the source from the tarball
tar -xzvf $tarball_name

# delete the tarball
rm $tarball_name

# install smoldyn from the source
cd $dist_dir
sudo -H ./install.sh

# install the repo
cd ..
pip install -e .


