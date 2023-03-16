from pymeasure.display.Qt import QtWidgets
from pymeasure.display.widgets import TabWidget


class ScatterPlotWidget(TabWidget, QtWidgets.QSplitter):


	def __init__(self):
		self.xdd = "inside"