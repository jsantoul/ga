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
        
        

    #------ OpenfiscaPluginMixin API ---------------------------------------------
    
    def apply_plugin_settings(self, options):
        """
        Apply configuration file's plugin settings
        """
                
        if 'data_file' in options:
            NotImplementedError
       
        if 'use_default' in options:     
            from src.lib.utils import of_import
            default_profiles_filename = of_import("","DEFAULT_PROFILES_FILENAME", self.simulation.country)
            self.simulation.load_profiles(default_profiles_filename)
            self.refresh_plugin()
            
            
    #------ OpenfiscaPluginWidget API ---------------------------------------------

    def get_plugin_title(self):
        """
        Return plugin title
        Note: after some thinking, it appears that using a method
        is more flexible here than using a class attribute
        """
        return _("Population Data Explorer")

    
    def get_plugin_icon(self):
        """
        Return plugin icon (QIcon instance)
        Note: this is required for plugins creating a main window
              (see OpenfiscaPluginMixin.create_mainwindow)
              and for configuration dialog widgets creation
        """
        return get_icon('OpenFisca22.png')
            
    def get_plugin_actions(self):
        """
        Return a list of actions related to plugin
        Note: these actions will be enabled when plugin's dockwidget is visible
              and they will be disabled when it's hidden
        """
        pass

    
    def register_plugin(self):
        """
        Register plugin in OpenFisca's main window
        """
        self.simulation = self.main.simulation
        self.main.add_dockwidget(self)

    def refresh_plugin(self):
        '''
        Update Survey dataframes
        '''
        self.starting_long_process(_("Refreshing population explorer dataframe ..."))
        self.clear()
#        self.view.set_dataframe(self.simulation.profiles.reset_index())
        self.ending_long_process(_("Population explorer dataframe updated"))
    
    def closing_plugin(self, cancelable=False):
        """
        Perform actions before parent main window is closed
        Return True or False whether the plugin may be closed immediately or not
        Note: returned value is ignored if *cancelable* is False
        """
        return True

        
 