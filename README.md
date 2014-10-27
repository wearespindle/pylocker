Setup
=====
You need opencv with python(2) bindings and i3lock(linux).
Mac: https://jjyap.wordpress.com/2014/05/24/installing-opencv-2-4-9-on-mac-osx-with-python-support/
Archlinux: pacman -S opencv 

 cd ~/projects
 git clone git@github.com:VoIPGRID/pylocker.git
 cd pylocker
 virtualenv2 --system-site-packages .
 pip install -r requirements
 ./pylocker.py --locktime 10 --treshold 10 --locker i3lock

If it doesn't work, check whether you can do an 'import cv' within the python shell.
