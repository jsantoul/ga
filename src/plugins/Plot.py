# -*- coding:utf-8 -*-
# Copyright © 2012 Clément Schaff, Mahdi Ben Jelloul

"""
openFisca, Logiciel libre de simulation du système socio-fiscal français
Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

This file is part of openFisca.

    openFisca is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    openFisca is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with openFisca.  If not, see <http://www.gnu.org/licenses/>.
"""
from PyQt4.QtGui import (QWidget, QDockWidget, QLabel, QVBoxLayout, QApplication, QCursor)
from PyQt4.QtCore import Qt
from core.qthelpers import OfSs
from pandas import DataFrame
from widgets.matplotlibwidget import MatplotlibWidget


# 

class PlotWidget(QDockWidget):
    def __init__(self, parent = None):
        super(PlotWidget, self).__init__(parent)
        self.setStyleSheet(OfSs.dock_style)
        # Create geometry
        self.setObjectName("PlotWidget")
        self.setWindowTitle(u"Graphique")
        self.dockWidgetContents = QWidget()
        
        self.graph = MatplotlibWidget(self.dockWidgetContents)
        
        verticalLayout = QVBoxLayout(self.dockWidgetContents)
        verticalLayout.addWidget(self.graph)
        self.setWidget(self.dockWidgetContents)

        # Initialize attributes
        self.parent = parent    
        self.data = DataFrame() 
    

    def refresh(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        self.plot()
        QApplication.restoreOverrideCursor()


    def plot(self):
        '''
        Plots the Lorenz Curve
        '''        
        axes = self.graph.axes
        data = self.data
        
        axes.clear()
        

        act = data.xs([0,0], level =['sex','age']).reset_index()
         
        print act['dsct'] 
        
        df = data.pv_percap('educ')
                
        df = df.xs([0,0], level =['sex','age']).reset_index()
        print df
        x = df['year']
        y = df[0]/act['dsct']
        
        
        label = None 
        axes.plot(x,y, linewidth = 2, label = label)
                
        axes.legend(loc= 2, prop = {'size':'medium'})
#        axes.set_xlim([0,1])
#        axes.set_ylim([0,1])   


    def set_dataframe(self, dataframe = None, name = None):
        '''
        Sets the current dataframe
        '''
        if name is not None:
            self.data = self.dataframes[name]
        if dataframe is not None:
            self.data = dataframe
                                
    def clear(self):
        self.data = None
