#!/bin/bash
pip uninstall smoldyn
cd ~/Desktop/smoldyn-2.72-mac || return
sudo -H ./install.sh
cd ../uchc_work/repos/biosimulator-processes || return
pip install -e .
