# -*- coding:utf-8 -*-
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

"""

"""

import platform


from PyQt4.QtCore import (SIGNAL, SLOT, Qt, QSettings, QVariant, QSize, QPoint, 
                          PYQT_VERSION_STR, QT_VERSION_STR, QLocale)
from PyQt4.QtGui import (QMainWindow, QWidget, QGridLayout, QMessageBox, QKeySequence,
                         QApplication, QCursor, QPixmap, QSplashScreen, QColor,
                         QActionGroup, QStatusBar)
from pandas import HDFStore


from Config import CONF, VERSION, ConfigDialog,  PathConfigPage
from core.cohorte import Cohorts
from core.qthelpers import create_action, add_actions, get_icon

from widgets.PopulationData import PopulationDataWidget
from widgets.ProfilesData import ProfilesDataWidget
from widgets.Parameters import ParametersWidget
from widgets.Plot import PlotWidget


class MainWindow(QMainWindow):
    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        self.dirty = False

        self.setObjectName("MainWindow")
        self.resize(800, 600)
        self.setWindowTitle("GA")   # TODO
# TODO        app_icon = get_icon('OpenFisca22.png')
#        self.setWindowIcon(app_icon)
        self.setLocale(QLocale(QLocale.French, QLocale.France))
        self.setDockOptions(QMainWindow.AllowNestedDocks|QMainWindow.AllowTabbedDocks|QMainWindow.AnimatedDocks)

        self.centralwidget = QWidget(self)
        self.gridLayout = QGridLayout(self.centralwidget)
        self.setCentralWidget(self.centralwidget)
        self.centralwidget.hide()

        self.statusbar = QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)

        # Showing splash screen
        pixmap = QPixmap(':/images/splash.png', 'png')
        self.splash = QSplashScreen(pixmap)
        font = self.splash.font()
        font.setPixelSize(10)
        self.splash.setFont(font)
        self.splash.show()
        self.splash.showMessage("Initialisation...", Qt.AlignBottom | Qt.AlignCenter | 
                                Qt.AlignAbsolute, QColor(Qt.black))
#        if CONF.get('main', 'current_version', '') != __version__:
#            CONF.set('main', 'current_version', __version__)
            # Execute here the actions to be performed only once after
            # each update (there is nothing there for now, but it could 
            # be useful some day...
        
        self.start()
        
    def start(self, restart = False):
        '''
        Starts main process
        '''
        # Preferences
        self.general_prefs = [PathConfigPage]
        self.apply_settings()
        
        # Dockwidgets creation
        self.splash.showMessage("Creating widgets...", Qt.AlignBottom | Qt.AlignCenter | 
                                Qt.AlignAbsolute, QColor(Qt.black))

        self.create_dockwidgets()
        self.populate_mainwidow()
        
        #################################################################
        ## Menu initialization
        #################################################################
        self.splash.showMessage("Creating menubar...", Qt.AlignBottom | Qt.AlignCenter | 
                                Qt.AlignAbsolute, QColor(Qt.black))
        # Menu Fichier
        self.file_menu = self.menuBar().addMenu("Fichier")
        action_export_png = create_action(self, 'Exporter le graphique', icon = 'document-save png.png') #, triggered = None)
        action_export_csv = create_action(self, 'Exporter la table', icon = 'document-save csv.png') #, triggered = None)
        action_pref = create_action(self, u'Préférences', QKeySequence.Preferences, icon = 'preferences-desktop.png', triggered = self.edit_preferences)
        action_quit = create_action(self, 'Quitter', QKeySequence.Quit, icon = 'process-stop.png',  triggered = SLOT('close()'))
        
        file_actions = [action_export_png, action_export_csv,None, action_pref, None, action_quit]
        add_actions(self.file_menu, file_actions)


        # Menu Edit
        self.edit_menu = self.menuBar().addMenu(u"Édition")
        action_copy = create_action(self, 'Copier', QKeySequence.Copy, triggered = self.global_callback, data = 'copy')
        
        edit_actions = [None, action_copy]
        add_actions(self.edit_menu, edit_actions)


        # Menu Projection
        self.projection_menu = self.menuBar().addMenu(u"Projection")
#
        self.action_refresh_project_population  = create_action(self, u'Calculer les projections de population', shortcut = 'F9', icon = 'calculator_green.png', triggered = self.project_population)


        projection_actions = [self.action_refresh_project_population,  None ]
        add_actions(self.projection_menu, projection_actions)
        
        # Menu Help
        help_menu = self.menuBar().addMenu("&Aide")
        action_about = create_action(self, u"&About GA", triggered = self.helpAbout)
        action_help = create_action(self, "&Aide", QKeySequence.HelpContents, triggered = self.helpHelp)
        help_actions = [action_about, action_help]
        add_actions(help_menu, help_actions)
                
        # Display Menu
        view_menu = self.createPopupMenu()
        view_menu.setTitle("&Affichage")
        self.menuBar().insertMenu(help_menu.menuAction(),
                                  view_menu)
        
        
        # Toolbar
        self.main_toolbar = self.create_toolbar(u"Barre d'outil", 'main_toolbar')
        toolbar_actions = [action_export_png, action_export_csv, None, self.action_refresh_project_population,]
        add_actions(self.main_toolbar, toolbar_actions)
        
        # Window settings
        self.splash.showMessage("Restoring settings...", Qt.AlignBottom | Qt.AlignCenter | 
                                Qt.AlignAbsolute, QColor(Qt.black))
        settings = QSettings()
        size = settings.value('MainWindow/Size', QVariant(QSize(800,600))).toSize()
        self.resize(size)
        position = settings.value('MainWindow/Position', QVariant(QPoint(0,0))).toPoint()
        self.move(position)
        self.restoreState(settings.value("MainWindow/State").toByteArray())

        # Connectors

        self.connect(self._param_widget, SIGNAL('population_changed()'), self.refresh_population)
#        self.connect(self._param_widget, SIGNAL('rates_changed()'), self.refresh_cohorts)
        self.connect(self._param_widget, SIGNAL('state_proj_changed()'), self.refresh_cohorts)

        self.refresh_population()
        self.load_data()
        
        
        self.splash.showMessage("Loading survey data...", Qt.AlignBottom | Qt.AlignCenter | 
                                Qt.AlignAbsolute, QColor(Qt.black))
        self.splash.hide()
        return


    def create_toolbar(self, title, object_name, iconsize=24):
        toolbar = self.addToolBar(title)
        toolbar.setObjectName(object_name)
        toolbar.setIconSize( QSize(iconsize, iconsize) )
        return toolbar

    def create_dockwidgets(self):
        '''
        Creates dockwidgets
        '''
        self._population_widget = PopulationDataWidget(self)
        self._cohorts_widget   = PopulationDataWidget(self)
        self._profiles_widget   = ProfilesDataWidget(self)
        self._param_widget      = ParametersWidget(self)
        self._plot_widget       = PlotWidget(self)
        
        # TODO
        # plot population pyramides/expenses pyramides 
        # générational flow
    
    def populate_mainwidow(self):
        '''
        Creates all dockwidgets
        '''
        left_widgets = [self._profiles_widget, self._population_widget , self._cohorts_widget, self._plot_widget]
        first_left_widget = None
        for widget in left_widgets:
            self.addDockWidget(Qt.LeftDockWidgetArea, widget)
            if first_left_widget is None:
                first_left_widget = widget
            else:
                self.tabifyDockWidget(first_left_widget, widget)

        
    def global_callback(self):
        """Global callback"""
        widget = QApplication.focusWidget()
        action = self.sender()
        callback = unicode(action.data().toString())
        if hasattr(widget, callback):
            getattr(widget, callback)()


    def load_data(self):
        '''
        Loads population and profiles data 
        '''
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        try:
            profiles_file = CONF.get('paths', 'profiles_file')         
            store = HDFStore(profiles_file,'r')
            profiles = store['profiles']
            
        except Exception, e:
            self.population_loaded = False
            QMessageBox.warning(self, u"Impossible de lire les données de population", 
                                u"GA n'a pas réussi à lire les données de population. L'erreur suivante a été renvoyée:\n%s\n\nVous pouvez configuer le chemin vers le fichier de données  Fichier>Paramètres>Chemins>Fichier données population"%e)
            return False
        finally:
            store.close()
            QApplication.restoreOverrideCursor()
    
        self._input_profiles = profiles
        self.update_dataframe_views()
    
    
    
    
    def project_population(self):
        pass
    
    
    def refresh_cohorts(self):
        '''
        Refresh cohorts
        '''
        
        year_length = CONF.get('parameters', 'year_length')
        population = self.population
        profiles   = self._input_profiles
        cohorts    = Cohorts(data = population, columns = ['pop'])
        
        g = self._param_widget.get_grth()
        r = self._param_widget.get_dsct()
                
        # Prolongation of population scenario
        
        method = self._param_widget.population_prolong
        cohorts.prolong_population(year_length, method = method)
        cohorts.fill(profiles)
        
        cohorts.gen_dsct(r)
        cohorts.gen_grth(g)
        
        # Projection of net taxes
        if self._param_widget.taxes_proj == "head_g":
            cohorts.proj_tax(method = 'per_capita')
        elif self._param_widget.taxes_proj == "global_g":
            cohorts.proj_tax(method = 'global')

        self._cohorts_widget.set_dataframe(cohorts.reset_index())
        self._cohorts_widget.update_view()

        self._plot_widget.set_dataframe(cohorts)
        self._plot_widget.refresh()


        
        state = False
        if state is False:
            return
        
        # Prolongation of state expenses
        if self._param_widget.state_proj == "global_r":
            pass
        elif self._param_widget.state_proj == "global_g":
            pass
        elif self._param_widget.state_proj == "head_r":
            pass
        elif self._param_widget.state_proj == "head_g":
            pass

        
    def refresh_population(self):
        '''
        Refresh after population update
        '''
        population_file = CONF.get('paths', 'population_file')         
        store_pop = HDFStore(population_file,'r')
        self.population = store_pop[self._param_widget.population_name]
        store_pop.close()
        population = self.population.reset_index()
        self._population_widget.set_dataframe(population)
        self._population_widget.update_view()
        
    
    def update_dataframe_views(self):
        '''
        Updates population and profiles dataframe views
        '''
        
        self._profiles_widget.set_dataframe(self._input_profiles.reset_index())
        self._profiles_widget.update_view()
    
    def closeEvent(self, event):
        if self.okToContinue():
            settings = QSettings()
            settings.setValue('MainWindow/Size', QVariant(self.size()))
            settings.setValue('MainWindow/Position', QVariant(self.pos()))
            settings.setValue('MainWindow/State', QVariant(self.saveState()))
        else:
            event.ignore()
    
    def okToContinue(self):
        if self.dirty:
            reply = QMessageBox.question(self, 
                                         "OpenFisca",
                                         "Voulez-vous quitter ?",
                                         QMessageBox.Yes|QMessageBox.No)
            if reply == QMessageBox.No:
                return False
        return True
    
    def helpAbout(self):
        QMessageBox.about(self, u"About GA",
                          u''' <b>GA</b><sup>beta</sup> v %s
                          <p> Copyright &copy; 2011 Clément Schaff, Mahdi Ben Jelloul
                          Tout droit réservé
                          <p> License GPL version 3 ou supérieure
                          <p> Python %s - Qt %s - PyQt %s on %s'''
                          % (VERSION, platform.python_version(),
                          QT_VERSION_STR, PYQT_VERSION_STR, platform.system()))

    def helpHelp(self):
        QMessageBox.about(self, u"Aide GA",
                          u'''<p> L'aide n'est pas disponible pour le moment.  </a>
                          ''')

    def apply_settings(self):
        pass

    def edit_preferences(self):
        """Edit preferences"""
        dlg = ConfigDialog(self)
        for PrefPageClass in self.general_prefs:
            widget = PrefPageClass(parent = dlg, main=self)
            widget.initialize()
            dlg.add_page(widget)

        dlg.show()
        dlg.check_all_settings()
        dlg.exec_()
        
