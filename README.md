# lut_combiner

Simple application to view .tif files form microscopy, assign different lookup tables (lut) and combine the images
Run with loader.py

Using PySide2, pyqtgraph, matplotlib and https://github.com/cleterrier/ChrisLUTs

# Usage
Pre-compiled for windows, for mac, linux run loader.py in python and install required packages (all listed in loader.py)

![](example.png?raw=true)

Drag-and-drop .tif images to the images on the left and select the colormap of your choice using the dropdown menu (top right).
Save images (as .jpg and .png) using the save button (path listed top left).


The exe is compiled in python3.10 using pyinstaller with the following packages/versions:
python -m pip list
Package                   Version
------------------------- ---------
altgraph                  0.17.2
colorspacious             1.1.2
colorstamps               0.1.2
cycler                    0.11.0
fonttools                 4.37.1
future                    0.18.2
kiwisolver                1.4.4
matplotlib                3.5.3
numpy                     1.23.3
packaging                 21.3
pefile                    2022.5.30
Pillow                    9.2.0
pyinstaller               5.4.1
pyinstaller-hooks-contrib 2022.10
pyparsing                 3.0.9
pyqtgraph                 0.12.4
PySide2                   5.15.2.1
python-dateutil           2.8.2
pywin32-ctypes            0.2.0
scipy                     1.9.1
shiboken2                 5.15.2.1
six                       1.16.0
tifffile                  2022.8.12
