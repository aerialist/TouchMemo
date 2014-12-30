from __future__ import print_function
import sys, time
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import numpy as np
import serial

import ui_touchmemo

addr  = 'COM8'
baud  = 9600

imgSize = (640, 480)
xMin = yMin = zMin = 0
xMax = yMax = zMax = 3984
xRatio = float(imgSize[0])/xMax
yRatio = float(imgSize[1])/yMax
points = 100
xarray = []
yarray = []
zarray = []

class SerialReader(QThread):
	updated = pyqtSignal(str)
	def __init__(self):
		QThread.__init__(self)
		self.port = serial.Serial(addr,baud)
	
	def run(self):
		while True:
			line = self.port.readline()
			self.updated.emit(line)
			time.sleep(0.001)
		
	def __del__(self):
		self.port.close()


class MainWindow(QMainWindow, ui_touchmemo.Ui_MainWindow):
	def __init__(self, parent=None):
		super(MainWindow, self).__init__(parent)
		self.setupUi(self)
		
		self.label.setGeometry(QRect(0,0,imgSize[1],imgSize[0]))
		self.scrollAreaWidgetContents.setGeometry(QRect(0,0,imgSize[1],imgSize[0]))
		
		self.graphicsView.setGeometry(QRect(0,0,imgSize[1],imgSize[0]))
		self.scrollAreaWidgetContents_2.setGeometry(QRect(0,0,imgSize[1],imgSize[0]))
		self.graphicsScene = QGraphicsScene(self)
		self.graphicsScene.setSceneRect(0,0,imgSize[1],imgSize[0])
		self.graphicsView.setScene(self.graphicsScene)
		
		self._serialReader = SerialReader()
		self._serialReader.updated.connect(self.processLine)
		self.checkBox.toggled.connect(self.checkLiveUpdate)
		self.pushButton.clicked.connect(lambda: self.clearImg(update=True))

		self.COLORTABLE=[]
		for i in range(256): self.COLORTABLE.append(qRgb(i/4,i,i/2))
		self.gray_color_table = [qRgb(i, i, i) for i in range(255, -1, -1)]
	
		self.clearImg(update=True)		
		#self.img[0:30,:] = 225
		
		#QI=QImage(self.img.data, imgSize[0], imgSize[1], QImage.Format_Indexed8)
		#QI.setColorTable(self.COLORTABLE)
		#QI.setColorTable(self.gray_color_table)
		#self.label.setPixmap(QPixmap.fromImage(QI))
		
		#self.loadDummy()
		self.checkBox.setChecked(True)

	def checkLiveUpdate(self, chkbtn):
		if chkbtn:
			self._serialReader.start()
		else:
			self._serialReader.quit()

	def processLine(self, line):
		"""
		Receive QString line
		"""
		line = str(line)
		#print(line, end="")
		if str(line)[0] == '(':
			try:
				(x,y,z) = eval(line)
				xarray.append(x)
				yarray.append(y)
				zarray.append(z)
				xi, yi = self.calcPix(x,y)
				self.brushFillRect(xi, yi, size=4)
				self.updateImg()
			except:
				print("Not a point!")
	
	def clearImg(self, update=True):
		xarray = []
		yarray = []
		zarray = []
		self.img = np.zeros(imgSize, dtype='uint8')
		self.graphicsScene.clear()
		if update:
			self.updateImg()
		
	def updateImg(self):
		#self.img = np.ones(imgSize, dtype='uint8') * 225
		#self.img[51:80,:] = 150
		#x = np.random.randint(0, 640)
		#y = np.random.randint(0, 480)
		#self.img[x,y] = 225
		
		#img_flipped = np.flipud(np.fliplr(self.img))
		#img_flipped = np.require(img_flipped, np.uint8, 'C')
		#self.implot = self.ax.imshow(self.img)
		#self.implot.set_array(self.img)
		#self.implot.set_data(img_flipped)	# This works nice instead of imshow!!
		#self.fig.canvas.draw()	# This works better = faster!!
		#self.fig.savefig("temp.png")	# This forced the update!
		#return self.implot

		QI=QImage(self.img.data, imgSize[1], imgSize[0], self.img.strides[0], QImage.Format_Indexed8)
		#QI.setColorTable(self.COLORTABLE)
		QI.setColorTable(self.gray_color_table)
		self.label.setPixmap(QPixmap.fromImage(QI))
		#TODO: Use update rather than setPixmap every time
		#self.label.update()
		
		#self.qImg = QImage(img_flipped.data, imgSize[1], imgSize[0], img_flipped.strides[0], QImage.Format_Indexed8)
		#self.graphicsScene.clear()		
		#self.graphicsScene.addPixmap(QPixmap.fromImage(QI))
		if len(xarray) > 1:
			x1, y1 = self.calcPix(xarray[-2],yarray[-2])
			x2, y2 = self.calcPix(xarray[-1],yarray[-1])
			self.graphicsScene.addLine(y1, x1, y2, x2, QPen(Qt.black, 2, Qt.SolidLine))
		
	def loadDummy(self):
		""" load dummy data for testing """
		npzfile = np.load("data.npz")
		xnp = npzfile['xnp']
		ynp = npzfile['ynp']
		znp = npzfile['znp']
		
		self.clearImg()
		for i in range(len(xnp)):
			xi, yi = self.calcPix(xnp[i], ynp[i])
			self.brushFillRect(xi, yi)
		self.updateImg()

	def calcPix(self, x, y):
		"""
		take x, y and return imgXY
		"""
		#global xRatio, yRatio
		imgX = imgSize[0] - int(xRatio * x)
		imgY = imgSize[1] - int(yRatio * y)
		return (imgX, imgY)

	def brushFillRect(self, x, y, z=225, size=10):
		"""
		Simple rectanglular fill brush
		"""
		sizem = -1 * int(size/2)
		sizep = int(size/2) + 1
		for j in range(sizem, sizep):
			for k in range(sizem, sizep):
				try:
					self.img[x+j, y+k] = z
				except IndexError:
					pass
		
def main():
	app = QApplication(sys.argv)
	form = MainWindow()
	form.show()
	app.exec_()

main()