#!/usr/bin/env bash


# The following script serves as a utility for installing this repository with the Smoldyn requirement on a Silicon Mac

# set installation parameters
env_name="$1"
if [ "$env_name" == "" ]; then
  env_name=$(conda env list | grep '*' | awk '{print $1}')
fi

dist_url=https://www.smoldyn.org/smoldyn-2.73-mac.tgz
tarball_name=smoldyn-2.73-mac.tgz
dist_dir=${tarball_name%.tgz}

# uninstall existing version if needed
# conda run -n "$env_name" pip-autoremove smoldyn -y

# download the appropriate distribution from smoldyn
wget $dist_url

# extract the source from the tarball
tar -xzvf $tarball_name

# delete the tarball
rm $tarball_name

# install smoldyn from the source
cd $dist_dir || return

if sudo -H conda run -n "$env_name" ./install.sh; then
  cd ..
  # remove the smoldyn dist
  rm -r $dist_dir
  echo "Smoldyn successfully installed. Done."
else
  echo "Could not install smoldyn"
  exit 1
fi
