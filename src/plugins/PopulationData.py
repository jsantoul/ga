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
from PyQt4.QtGui import (QWidget, QDockWidget, QVBoxLayout, QApplication, QCursor)
from PyQt4.QtCore import SIGNAL, Qt, QVariant
from core.qthelpers import OfSs
from pandas import DataFrame
from pandas.sandbox.qtpandas import DataFrameWidget




class PopulationDataWidget(QDockWidget):
    def __init__(self, parent = None):
        super(PopulationDataWidget, self).__init__(parent)
        self.setStyleSheet(OfSs.dock_style)
        # Create geometry
        self.setObjectName("Population")
        self.setWindowTitle(u"Population")
        self.dockWidgetContents = QWidget()
        

        self.view = DataFrameWidget(DataFrame(), parent = self.dockWidgetContents)

        verticalLayout = QVBoxLayout(self.dockWidgetContents)
        verticalLayout.addWidget(self.view)
        self.setWidget(self.dockWidgetContents)

        # Initialize attributes
        self.parent = parent    
        self.data = DataFrame() 
    
    def set_dataframe(self, dataframe = None, name = None):
        '''
        Sets the current dataframe
        '''
        if name is not None:
            self.data = self.dataframes[name]
        if dataframe is not None:
            self.data = dataframe
            
                         
        
    def update_view(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        
        df = self.data.copy()
        if not isinstance(df, DataFrame): 
            print 'Not dataframe'
            df = DataFrame(df)
            
        self.view.dataModel.setDataFrame(df)
        self.view.dataModel.signalUpdate()
        
        QApplication.restoreOverrideCursor()
        
                
    def clear(self):
        self.view.clear()
        self.data = None
        self.datatables_choices = []
        self.dataframes = {}
        