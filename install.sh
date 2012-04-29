#! /bin/bash

#cd src/singlet && sudo python setup.py build && cd ../../
mkdir -p /usr/share/unity/lenses/tasks-lens
cp -u tasks-lens.lens /usr/share/unity/lenses/tasks-lens
cp -u icons/lens-icon.svg /usr/share/unity/lenses/tasks-lens
cp -u icons/tow*.png /usr/share/unity/lenses/tasks-lens

