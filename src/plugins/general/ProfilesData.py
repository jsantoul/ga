# -*- coding:utf-8 -*-
# Copyright © 2012 Clément Schaff, Mahdi Ben Jelloul


from src.gui.qt.QtGui import (QWidget, QDockWidget, QLabel, QHBoxLayout, QVBoxLayout, QGroupBox, QButtonGroup)
from src.gui.qt.QtCore import SIGNAL, Signal, Qt
from src.gui.qthelpers import OfSs
from src.gui.config import get_icon
#from pandas.sandbox.qtpandas import DataFrameWidget
from src.gui.qthelpers import DataFrameViewWidget 

from src.plugins import OpenfiscaPluginWidget, PluginConfigPage
from src.gui.baseconfig import get_translation
_ = get_translation('src')


class ProfilesExplorerConfigPage(PluginConfigPage):
    def __init__(self, plugin, parent):
        PluginConfigPage.__init__(self, plugin, parent)
        self.get_name = lambda: _("Profiles data explorer")
        
    def setup_page(self):
        """
        Setup the page of the survey widget
        """
        
        profiles_group = QGroupBox(_("Alternatives profiles data")) 
        profiles_bg = QButtonGroup(self)
        profiles_label = QLabel(_("Location of profiles data")) 

        country_default_radio = self.create_radiobutton(_("Use country default profiles data"),
                                                    'use_default', False,
                                                    tip = _("Use country default profiles data"),
                                                    
                                button_group = profiles_bg)
        profiles_radio = self.create_radiobutton(_("The following file"),  # le fichier suivant",
                                               'enable', True,
                                               _("profiles data file for micrsosimulation"), # "Fichier de données pour la microsimulation",
                                               button_group=profiles_bg)
        profiles_file = self.create_browsefile("", 'data_file',
                                             filters='*.h5')
        
        self.connect(country_default_radio, SIGNAL("toggled(bool)"),
                     profiles_file.setDisabled)
        self.connect(profiles_radio, SIGNAL("toggled(bool)"),
                     profiles_file.setEnabled)
        profiles_file_layout = QHBoxLayout()
        profiles_file_layout.addWidget(profiles_radio)
        profiles_file_layout.addWidget(profiles_file)

        profiles_layout = QVBoxLayout()
        profiles_layout.addWidget(profiles_label)
        profiles_layout.addWidget(country_default_radio)
        profiles_layout.addLayout(profiles_file_layout)
        profiles_group.setLayout(profiles_layout)

        vlayout = QVBoxLayout()
        vlayout.addWidget(profiles_group)
        vlayout.addStretch(1)
        self.setLayout(vlayout)


class ProfilesExplorerWidget(OpenfiscaPluginWidget):    
    """
    Profiles data explorer Widget
    """
    CONF_SECTION = 'profiles'
    CONFIGWIDGET_CLASS = ProfilesExplorerConfigPage
    LOCATION = Qt.LeftDockWidgetArea
    FEATURES = QDockWidget.DockWidgetClosable | \
               QDockWidget.DockWidgetFloatable | \
               QDockWidget.DockWidgetMovable
    DISABLE_ACTIONS_WHEN_HIDDEN = False
    sig_option_changed = Signal(str, object)

    def __init__(self, parent = None):
        super(ProfilesExplorerWidget, self).__init__(parent)
        self.setStyleSheet(OfSs.dock_style)
        # Create geometry
        self.setObjectName( _("Profiles data explorer"))
        self.dockWidgetContents = QWidget()

        self.view = DataFrameViewWidget(self.dockWidgetContents)

        verticalLayout = QVBoxLayout(self.dockWidgetContents)
        verticalLayout.addWidget(self.view)
        self.setLayout(verticalLayout)

        # Initialize attributes
        self.parent = parent    
        self.initialize_plugin() # To run the suitable inherited API methods
    
                                
    def clear(self):
        self.view.reset()



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
        return _("Profiles Data Explorer")

    
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

#        self.action_compute = create_action(self, _('Compute aggregates'),
#                                                      shortcut = 'F10',
#                                                      icon = 'calculator_blue.png', 
#                                                      triggered = self.compute)
#        self.register_shortcut(self.action_compute, 
#                               context = 'Survey explorer',
#                                name = _('Compute survey simulation'), default = 'F10')
#
#        self.action_set_reform = create_action(self, _('Reform mode'), 
#                                                     icon = 'comparison22.png', 
#                                                     toggled = self.set_reform, 
#                                                     tip = u"Différence entre la situation simulée et la situation actuelle")
#
#        self.run_menu_actions = [self.action_compute, self.action_set_reform]
#        self.main.run_menu_actions += self.run_menu_actions        
#        self.main.survey_toolbar_actions += self.run_menu_actions 
#        
#        return self.run_menu_actions

    
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
        self.starting_long_process(_("Refreshing profiles explorer dataframe ..."))
        self.clear()
        self.view.set_dataframe(self.simulation.profiles.reset_index())
        self.ending_long_process(_("Profiles explorer dataframe updated"))
    
    def closing_plugin(self, cancelable=False):
        """
        Perform actions before parent main window is closed
        Return True or False whether the plugin may be closed immediately or not
        Note: returned value is ignored if *cancelable* is False
        """
        return True

        
