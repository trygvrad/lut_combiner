#!/usr/bin/env python3


from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import  QColorDialog #QTreeWidgetItem
import pyqtgraph
import os
import sys
import numpy as np
import threading
import pathlib
import tifffile
import datetime
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        pyqtgraph.setConfigOption('background', 'W')
        #set theme:
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        elif __file__:
            application_path = os.path.dirname(__file__)
        path = 'set_theme.py'
        if not os.path.exists(path):
            path = str(application_path) + '/set_theme.py'
        if os.path.exists(path):
            with open(path) as f:
                code = compile(f.read(), path, 'exec')
                exec(code, globals(), locals())

        super(MainWindow, self).__init__(*args, **kwargs)
        #Load the UI Page

        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        elif __file__:
            application_path = os.path.dirname(__file__)

        i = 0
        if os.path.exists('lut_combiner.ui'):
            path = 'lut_combiner.ui'
        else:
            while not os.path.exists(str(application_path) + '/lut_combiner.ui'):
                application_path = application_path + '/..'
                i+=1
                if i>10:
                    break
            path = str(application_path) + '/lut_combiner.ui'

        uic.loadUi(path, self)

        self.setObjectName("MainWindow")

        colors = [
            (0, 0, 0),
            (230,0,0),
            (240,240,0),
            (255, 255, 255)
        ]
        colors = [
            (0, 0, 0),
            (255, 255, 255)
        ]
        # color maps
        cmap = pyqtgraph.ColorMap(pos=np.linspace(0.0, 1.0, 2), color=colors)
        #cmap = pyqtgraph.colormap.getFromMatplotlib('viridis')

        for img in  [self.img_0, self.img_1, self.img_2, self.composite]:
            img.setColorMap(cmap)
            img.ui.roiBtn.hide()
            img.ui.menuBtn.hide()
            img.has_img = False
        self.composite.ui.histogram.hide()
        self.img_0.getHistogramWidget().sigLevelsChanged.connect(self.update_composite_slot)
        self.img_1.getHistogramWidget().sigLevelsChanged.connect(self.update_composite_slot)
        self.img_2.getHistogramWidget().sigLevelsChanged.connect(self.update_composite_slot)
        self.updating_colors = False


        # hide colorbar
        #self.img_0.getHistogramWidget().gradient.hide()
        #self.img_0.ui.histogram.layout.setSpacing(0)



        def dragEnterEvent(ev):
            ev.accept()

        #self.path.dropEvent = self.do_drop_event_0
        self.img_0.setAcceptDrops(True)
        self.img_0.dropEvent = self.do_drop_event_0
        self.img_0.dragEnterEvent = dragEnterEvent

        self.img_1.setAcceptDrops(True)
        self.img_1.dropEvent = self.do_drop_event_1
        self.img_1.dragEnterEvent = dragEnterEvent

        self.img_2.setAcceptDrops(True)
        self.img_2.dropEvent = self.do_drop_event_2
        self.img_2.dragEnterEvent = dragEnterEvent

        self.img_2.hide()

        ###################### mpl plot
        import matplotlib.backends.backend_qt5agg
        import matplotlib.figure
        self.canvas = matplotlib.backends.backend_qt5agg.FigureCanvas(matplotlib.figure.Figure(figsize=(1, 1)))
        self.verticalLayout_3.addWidget(self.canvas)
        self.mpl_fig = self.canvas.figure
        ###################### cmap_selector
        self.LUTs = {}
        for file in os.listdir('ChrisLUTs'):
            if '.lut' in str(file):
                with open(f'ChrisLUTs/{file}','r') as f:
                    try:
                        arr = np.zeros((256,3), dtype = int)
                        for i, line in enumerate(f):
                            i-=1
                            if i < 0 or i > 255:
                                continue
                            else:
                                arr[i,:] = np.array([int(v) for v in line.split()])[1:]
                    except:
                        arr = np.fromfile(f'ChrisLUTs/{file}', dtype='uint8').reshape((3,256)).T
                    key = str(file).split('.')[0]
                    self.LUTs[key] = np.array(arr, dtype = int)
        #self.cmap_selector.addItem('ChrisLUTs 3color')
        #self.cmap_selector.addItem('ChrisLUTs 3color1')
        self.cmap_selector.addItem('Blue-Orange')
        self.cmap_selector.addItem('Green-Magenta')
        self.cmap_selector.addItem('Purple-Green')
        self.cmap_selector.addItem('Red-Green')
        self.cmap_selector.addItem('Red-Blue')
        self.cmap_selector.addItem('Blue-Green')
        self.cmap_selector.addItem('Custom')
        self.cmap_selector.addItem('2 Color custom')
        self.cmap_selector.addItem('Blue-Orange-Purple')
        self.cmap_selector.addItem('Orange-Purple-Fresh')
        self.cmap_selector.activated.connect(self.cmap_changed_slot)
        self.invert_check.stateChanged.connect(self.cmap_changed_slot)
        ###################### cmap_selector end

        send_queue, return_queue = queue.Queue(), queue.Queue()
        self.rimt = rimt(send_queue, return_queue).rimt
        self.rimt_executor = RimtExecutor(send_queue, return_queue)
        self.files = []
        self.locked = False

        if len(sys.argv)>1:
            file = sys.argv[1]
            self.new_file(file)

        self.save_button.clicked.connect(self.save_clicked)
        self.color_0_button.clicked.connect(self.color_0_button_clicked)
        self.color_1_button.clicked.connect(self.color_1_button_clicked)

        self.label.setText(' By Marie Curie fellow Trygve M. R'+chr(int('00E6', 16))+'der. Use at own risk. MIT lisence. https://github.com/trygvrad/lut_combiner')
        #self.save_image_button.clicked.connect(self.save_clicked)
        if 0: # modify the histogram to hide stuff
            try:
                pyqtgraph.fn # <--- old versions of pyqtgraph will fail on this line
                histogram_width = 50
                self.img_0.ui.gridLayout.setColumnMinimumWidth(3,-(106-histogram_width)) # hack with negative width to get correct placement of histogram with a low width
                # 116 to also remove colorbar
                self.img_0.ui.histogram.vb.setMaximumWidth(histogram_width)
                #self.img_0.ui.histogram.axis.hide()
                self.img_0.ui.histogram.axis.setWidth(0)
                self.img_0.ui.histogram.axis.setStyle(tickLength = -histogram_width)
                self.img_0.ui.histogram.axis.setStyle(tickTextOffset = -histogram_width+10)
                self.img_0.ui.histogram.axis.setStyle(tickTextOffset = -histogram_width+10)

                # self.img_0.ui.histogram.vb.setLogMode('x',True) # should be possible in pyqtgraph >= 0.12.4
                self.img_0.ui.histogram.axis.setPen(pyqtgraph.fn.mkPen((0, 0, 0, 50)))
                self.img_0.ui.histogram.axis.setTextPen(pyqtgraph.fn.mkPen((98, 98, 98, 255)))

                self.img_0.ui.histogram.region.setBrush(pyqtgraph.fn.mkBrush((0, 0, 0, 100)))
                self.img_0.ui.histogram.region.setHoverBrush(pyqtgraph.fn.mkBrush((100, 100, 100, 100)))
                self.img_0.ui.histogram.region.lines[0].setPen(pyqtgraph.fn.mkPen((0, 90, 150, 255)))
                self.img_0.ui.histogram.region.lines[1].setPen(pyqtgraph.fn.mkPen((0, 90, 150, 255)))

                self.img_0.ui.histogram.plots[0].setBrush((0, 0, 0))
                #self.img_0.ui.histogram.axis.setStyle(tickTextOffset = 3)
            except:
                None

        self.cmap_changed_slot(0)

        ### saving
        self.date_today=str(datetime.date.today())
        self.output_int = 1
        while (os.path.exists(f'output/{self.date_today}/{self.output_int}.png')):
            self.output_int += 1
        self.path.setText(f'output/{self.date_today}/{self.output_int}')

    def save_clicked(self,event):
        file = self.path.text()
        os.makedirs('/'.join(file.split('/')[:-1]), exist_ok = True)
        if hasattr(self, 'RGB'):
            import matplotlib.pyplot
            matplotlib.pyplot.imsave(file+'.png', self.RGB.astype(np.uint8))
            matplotlib.pyplot.imsave(file+'.jpg', self.RGB.astype(np.uint8))
            self.mpl_fig.savefig(file+'_stamp.png', transparent=True)

            if file == f'output/{self.date_today}/{self.output_int}':
                self.output_int += 1
                self.path.setText(f'output/{self.date_today}/{self.output_int}')

        '''print(file)
        try:
            self.new_file(file)
            self.label.setText(' By Marie Curie fellow Trygve M. R'+chr(int('00E6', 16))+'der for use in the group of Hugh Simons at DTU. Use at own risk. MIT lisence. https://github.com/trygvrad/lut_combinerer')
        except Exception as e:
            self.label.setText(str(e))
            self.label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            print(e)'''


    def color_0_button_clicked(self,event):
        c = QColorDialog.getColor(QColor(*self.color_0), self)
        self.color_0 = np.array([c.red(), c.green(), c.blue()])
        self.cmap_changed_slot(0)
    def color_1_button_clicked(self,event):
        c = QColorDialog.getColor(QColor(*self.color_1), self)
        self.color_1 = np.array([c.red(), c.green(), c.blue()])
        self.cmap_changed_slot(0)
    #def save_clicked(self,event):
    #    None


    def do_drop_event_0(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        file = files[0]
        self.new_file(file, self.img_0)

    def do_drop_event_1(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        file = files[0]
        self.new_file(file, self.img_1)

    def do_drop_event_2(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        file = files[0]
        self.new_file(file, self.img_2)

    def new_file(self,file, target_img):
        formats = ['tif','TIF','tiff','TIFF']
        if file.split('.')[-1] in formats :
            tiff = tifffile.imread(file)
            if len(tiff.shape)>2: # need a better fix for image stacks
                tiff = tiff[0]
            target_img.img = tiff
            target_img.getImageItem().setImage(tiff,
                    levels = [np.percentile(tiff, 0.1),np.percentile(tiff, 99.9)],
                    axisOrder = 'row-major')
        target_img.has_img = True
        self.update_composite()
        if np.sum([self.img_0.has_img, self.img_1.has_img, self.img_2.has_img]) == 1:
            v0 = target_img.getView()
            for v in [self.img_0.getView(), self.img_1.getView(), self.img_2.getView()]:#, self.composite.getView()]:
                if not v==v0:
                    v.setXLink(v0)
                    v.setYLink(v0)

    def update_composite(self):
        self.updating_colors = False
        if (self.img_0.has_img and self.img_1.has_img):
            imgs = []
            for i, img in enumerate([self.img_0, self.img_1]):
                levels = img.getHistogramWidget().getLevels()
                imgs.append(np.array(255*(img.img-levels[0])/(levels[1]-levels[0]), dtype = int))
                imgs[-1][imgs[-1]>255] = 255
                imgs[-1][ imgs[-1]<0 ] = 0
            if self.num_colors == 2:
                self.RGB = self.stamp[imgs[0], imgs[1]]
                self.composite.getImageItem().setImage(self.RGB, axisOrder = 'row-major')
            else:
                if self.img_2.has_img:
                    img = self.img_2
                    levels = img.getHistogramWidget().getLevels()
                    imgs.append(np.array(255*(img.img-levels[0])/(levels[1]-levels[0]), dtype = int))
                    imgs[-1][imgs[-1]>255] = 255
                    imgs[-1][ imgs[-1]<0 ] = 0
                    self.RGB = self.stamp_not_inv[0][imgs[0]] + self.stamp_not_inv[1][imgs[1]]  + self.stamp_not_inv[2][imgs[2]]
                    if self.invert_check.isChecked():
                        self.RGB = 255-self.RGB
                    self.RGB[self.RGB>255] = 255
                    self.RGB[self.RGB<0 ] = 0

                    self.composite.getImageItem().setImage(self.RGB, axisOrder = 'row-major')


    def get_xy(self):
        x = np.ones((256,256), dtype = int)*np.arange(256)[np.newaxis,:]
        y = np.ones((256,256), dtype = int)*np.arange(256)[:,np.newaxis]
        return x, y

    def get_stamp(self):
        cmap = self.cmap_selector.currentText()
        self.color_0_button.hide()
        self.color_1_button.hide()
        self.img_2.hide()
        self.num_colors = 2
        if cmap == 'Blue-Orange':
            im0, im1 = self.get_xy()
            stamp = np.zeros((*im0.shape,3), dtype = int)
            stamp[:,:,0] = im0
            stamp[:,:,2] = im1
            stamp[:,:,1] = 0.5*(stamp[:,:,0]+stamp[:,:,2])
        if cmap == 'Green-Magenta':
            im0, im1 = self.get_xy()
            stamp = np.zeros((*im0.shape,3), dtype = int)
            stamp[:,:,0] = im0
            stamp[:,:,1] = im1
            stamp[:,:,2] = 0.5*(stamp[:,:,0]+stamp[:,:,1])
        if cmap == 'Purple-Green':
            im0, im1 = self.get_xy()
            stamp = np.zeros((*im0.shape,3), dtype = int)
            stamp[:,:,1] = im0
            stamp[:,:,2] = im1
            stamp[:,:,0] = 0.5*(stamp[:,:,1]+stamp[:,:,2])
        if cmap == 'Red-Green':
            im0, im1 = self.get_xy()
            stamp = np.zeros((*im0.shape,3), dtype = int)
            stamp[:,:,0] = im0
            stamp[:,:,1] = im1
        if cmap == 'Red-Blue':
            im0, im1 = self.get_xy()
            stamp = np.zeros((*im0.shape,3), dtype = int)
            stamp[:,:,0] = im0
            stamp[:,:,2] = im1
        if cmap == 'Blue-Green':
            im0, im1 = self.get_xy()
            stamp = np.zeros((*im0.shape,3), dtype = int)
            stamp[:,:,1] = im0
            stamp[:,:,2] = im1
        if cmap == 'Custom':
            im0, im1 = self.get_xy()
            self.color_0_button.show()
            c0_comp = np.array([255,255,255], dtype = int) - self.color_0
            L0_a = np.array(np.arange(256)[:,np.newaxis]*self.color_0[np.newaxis,:]/255.0, dtype = int)
            L0_b = np.array(np.arange(256)[:,np.newaxis]*c0_comp[np.newaxis,:]/255.0, dtype = int)
            stamp = (L0_a[im0] + L0_b[im1]).swapaxes(0,1)
        if cmap == '2 Color custom':
            im0, im1 = self.get_xy()
            self.color_0_button.show()
            self.color_1_button.show()
            c0_comp = np.array([255,255,255], dtype = int) - self.color_0
            L0_a = np.array(np.arange(256)[:,np.newaxis]*self.color_0[np.newaxis,:]/255.0, dtype = int)
            L0_b = np.array(np.arange(256)[:,np.newaxis]*c0_comp[np.newaxis,:]/255.0, dtype = int)
            stamp_0 = (L0_a[im0] + L0_b[im1]).swapaxes(0,1)

            c1_comp = np.array([255,255,255], dtype = int) - self.color_1
            L1_a = np.array(np.arange(256)[:,np.newaxis]*self.color_1[np.newaxis,:]/255.0, dtype = int)
            L1_b = np.array(np.arange(256)[:,np.newaxis]*c1_comp[np.newaxis,:]/255.0, dtype = int)
            stamp_1 = (L1_a[im0] + L1_b[im1])

            stamp = stamp_1
            ti = np.tril_indices(stamp.shape[0])
            stamp[ti] = stamp_0[ti]
        if cmap == 'Blue-Orange-Purple':
            self.num_colors = 3
            self.img_2.show()
            self.lut_0 = self.LUTs['BOP blue']
            self.lut_1 = self.LUTs['BOP orange']
            self.lut_2 = self.LUTs['BOP purple']
            stamp = [self.lut_0, self.lut_1, self.lut_2]
        if cmap == 'Orange-Purple-Fresh':
            self.num_colors = 3
            self.img_2.show()
            self.lut_0 = self.LUTs['OPF orange']
            self.lut_1 = self.LUTs['OPF purple']
            self.lut_2 = self.LUTs['OPF fresh']
            stamp = [self.lut_0, self.lut_1, self.lut_2]
        #if cmap == 'ChrisLUTs 3color':
        #    stamp = self.LUTs['3color-BMR'][im0] + self.LUTs['3color-YGC'][im1]
        #if cmap == 'ChrisLUTs 3color1':
        #    stamp = self.LUTs['3color-RMB'][im0] + self.LUTs['3color-CGY'][im1]
        if self.num_colors == 2:
            stamp[stamp<0] = 0
            stamp[stamp>255] = 255
            if self.invert_check.isChecked():
                stamp = 255 - stamp
        if self.num_colors == 3:
            self.stamp_not_inv = stamp
            if self.invert_check.isChecked():
                stamp = [255-stamp[0], 255-stamp[1], 255-stamp[2]]
        return stamp

    @QtCore.pyqtSlot(object)
    def update_composite_slot(self, *args):
        if self.updating_colors == False:
            self.updating_colors = True
            QtCore.QTimer.singleShot(250, self.update_composite)

    def cmap_changed_slot(self, i):
        cmap = self.cmap_selector.currentText()
        self.mpl_fig.clf()
        self.stamp = self.get_stamp()
        if self.num_colors == 2:
            self.mpl_ax = self.mpl_fig.subplots()
            self.mpl_ax.imshow(self.stamp, origin = 'lower')
            self.mpl_ax.set_xticks([])
            self.mpl_ax.set_yticks([])
            self.img_0.setColorMap(pyqtgraph.ColorMap(pos=np.linspace(0.0, 1.0, 256), color=self.stamp[:,0]))
            self.img_1.setColorMap(pyqtgraph.ColorMap(pos=np.linspace(0.0, 1.0, 256), color=self.stamp[0,:]))
            #self.mpl_fig.tight_layout()
        else: # self.num_colors == 3:
            self.mpl_ax = self.mpl_fig.subplots(1,3)
            for ax in self.mpl_ax:
                ax.set_xticks([])
                ax.set_yticks([])
            self.mpl_ax[0].imshow(self.stamp[0][:,np.newaxis,:]*np.ones((256,20,3), dtype = int), origin = 'lower')
            self.img_0.setColorMap(pyqtgraph.ColorMap(pos=np.linspace(0.0, 1.0, 256), color=self.stamp[0]))
            self.mpl_ax[1].imshow(self.stamp[1][:,np.newaxis,:]*np.ones((256,20,3), dtype = int), origin = 'lower')
            self.img_1.setColorMap(pyqtgraph.ColorMap(pos=np.linspace(0.0, 1.0, 256), color=self.stamp[1]))
            self.mpl_ax[2].imshow(self.stamp[2][:,np.newaxis,:]*np.ones((256,20,3), dtype = int), origin = 'lower')
            self.img_2.setColorMap(pyqtgraph.ColorMap(pos=np.linspace(0.0, 1.0, 256), color=self.stamp[2]))

        self.mpl_fig.canvas.draw()
        self.update_composite()

        cmap = self.cmap_selector.currentText()
        if not (cmap == 'Custom' or cmap == '2 Color custom'):
            if self.num_colors == 2:
                self.color_0 = self.stamp[255, 0]
                self.color_1 = self.stamp[0, 255]

import queue
import functools
class rimt():
    def __init__(self, send_queue, return_queue):
        self.send_queue = send_queue
        self.return_queue = return_queue
        self.main_thread = threading.currentThread()

    def rimt(self, function, *args, **kwargs):
        if threading.currentThread() == self.main_thread:
            return function(*args, **kwargs)
        else:
            self.send_queue.put(functools.partial(function, *args, **kwargs))
            return_parameters = self.return_queue.get(True)  # blocks until an item is available
        return return_parameters


class RimtExecutor():
    def __init__(self, send_queue, return_queue):
        self.send_queue = send_queue
        self.return_queue = return_queue

    def execute(self):
        for i in [0]:
            try:
                callback = self.send_queue.get(False)  # doesn't block
                #print('executing')
            except:  # queue.Empty raised when queue is empty (python3.7)
                break
            try:
                #self.return_queue.put(None)
                return_parameters = callback()
                QtCore.QCoreApplication.processEvents()
                self.return_queue.put(return_parameters)
            except Exception as e:
                return_parameters = None
                traceback.print_exc()
                print(e)
        QtCore.QTimer.singleShot(10, self.execute)

from pyqtgraph import Point
def paint(self, p, *args):
    '''
    this is a version of pyqtgraph.graphicsItems.HistogramLUTItem.HistogramLUTItem
    that when called does not add the diagonal lines connecting the colorbar to the histogram
    overload using "setattr(pyqtgraph.graphicsItems.HistogramLUTItem.HistogramLUTItem,'paint', paint)"
    before the ui is loaded
    '''
    if self.levelMode != 'mono':
        return
    pen = self.region.lines[0].pen
    rgn = self.getLevels()
    p1 = self.vb.mapFromViewToItem(self, Point(self.vb.viewRect().center().x(), rgn[0]))
    p2 = self.vb.mapFromViewToItem(self, Point(self.vb.viewRect().center().x(), rgn[1]))
    gradRect = self.gradient.mapRectToParent(self.gradient.gradRect.rect())
    p.setRenderHint(QtGui.QPainter.Antialiasing)
    '''
    for pen in [fn.mkPen((0, 0, 0, 100), width=3), pen]:
        p.setPen(pen)
        p.drawLine(p1 + Point(0, 5), gradRect.bottomLeft())
        p.drawLine(p2 - Point(0, 5), gradRect.topLeft())
        p.drawLine(gradRect.topLeft(), gradRect.topRight())
        p.drawLine(gradRect.bottomLeft(), gradRect.bottomRight())
    '''

if __name__ == "__main__":
    # remoce lines to colorbar from plot
    setattr(pyqtgraph.graphicsItems.HistogramLUTItem.HistogramLUTItem,'paint', paint)
    #
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    QtCore.QTimer.singleShot(30, main_window.rimt_executor.execute) #<- must be run after the event loop has started (.show()?)
    sys.exit(app.exec_())
