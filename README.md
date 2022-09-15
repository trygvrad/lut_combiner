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

PySide2                   5.15.2.1, 
pyqtgraph                 0.12.4, 
numpy                     1.23.3, 
matplotlib                3.5.3,
tifffile                  2022.8.12
