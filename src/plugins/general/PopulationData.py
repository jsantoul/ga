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
from src.gui.qt.QtGui import (QWidget, QDockWidget, QLabel, QHBoxLayout, QVBoxLayout, QGroupBox, QButtonGroup)
from src.gui.qt.QtCore import SIGNAL, Signal, Qt
from src.gui.qthelpers import OfSs
from src.gui.config import get_icon
#from pandas.sandbox.qtpandas import DataFrameWidget
from src.gui.qthelpers import DataFrameViewWidget 

from src.plugins import OpenfiscaPluginWidget, PluginConfigPage
from src.gui.baseconfig import get_translation
_ = get_translation('src')


class PopulationExplorerConfigPage(PluginConfigPage):
    def __init__(self, plugin, parent):
        PluginConfigPage.__init__(self, plugin, parent)
        self.get_name = lambda: _("Population data explorer")
        
    def setup_page(self):
        """
        Setup the page of the survey widget
        """
        
        population_group = QGroupBox(_("Alternatives population data")) 
        population_bg = QButtonGroup(self)
        population_label = QLabel(_("Location of population data")) 

        country_default_radio = self.create_radiobutton(_("Use country default population data"),
                                                    'use_default', False,
                                                    tip = _("Use country default population data"),
                                                    
                                button_group = population_bg)
        population_radio = self.create_radiobutton(_("The following file"),  # le fichier suivant",
                                               'enable', True,
                                               _("population data file for micrsosimulation"), # "Fichier de données pour la microsimulation",
                                               button_group=population_bg)
        population_file = self.create_browsefile("", 'data_file',
                                             filters='*.h5')
        
        self.connect(country_default_radio, SIGNAL("toggled(bool)"),
                     population_file.setDisabled)
        self.connect(population_radio, SIGNAL("toggled(bool)"),
                     population_file.setEnabled)
        population_file_layout = QHBoxLayout()
        population_file_layout.addWidget(population_radio)
        population_file_layout.addWidget(population_file)

        population_layout = QVBoxLayout()
        population_layout.addWidget(population_label)
        population_layout.addWidget(country_default_radio)
        population_layout.addLayout(population_file_layout)
        population_group.setLayout(population_layout)

        vlayout = QVBoxLayout()
        vlayout.addWidget(population_group)
        vlayout.addStretch(1)
        self.setLayout(vlayout)

class PopulationExplorerWidget(OpenfiscaPluginWidget):    
    """
    Population data explorer Widget
    """
    CONF_SECTION = 'population'
    CONFIGWIDGET_CLASS = PopulationExplorerConfigPage
    LOCATION = Qt.LeftDockWidgetArea
    FEATURES = QDockWidget.DockWidgetClosable | \
               QDockWidget.DockWidgetFloatable | \
               QDockWidget.DockWidgetMovable
    DISABLE_ACTIONS_WHEN_HIDDEN = False
    sig_option_changed = Signal(str, object)

    def __init__(self, parent = None):
        super(PopulationExplorerWidget, self).__init__(parent)
        self.setStyleSheet(OfSs.dock_style)
        # Create geometry
        self.setObjectName( _("Population data explorer"))
        self.dockWidgetContents = QWidget()

        self.view = DataFrameViewWidget(self.dockWidgetContents)

        verticalLayout = QVBoxLayout(self.dockWidgetContents)
        verticalLayout.addWidget(self.view)
        self.setLayout(verticalLayout)

        # Initialize attributes
        self.parent = parent    
        self.initialize_plugin() # To run the suitable inherited API methods

        # Initialize attributes
        self.parent = parent    
        self.data = None
    
    def set_dataframe(self, dataframe = None, name = None):
        '''
        Sets the current dataframe
        '''
        if name is not None:
            self.data = self.dataframes[name]
        if dataframe is not None:
            self.data = dataframe
                            
    def clear(self):
        self.view.clear()
        self.data = None
        self.datatables_choices = []
        self.dataframes = {}
        