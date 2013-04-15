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


"""
    TODO choix de la méthode de projection de la population au delà des valeurs du scénario
"""
from src.gui.qt.QtGui import (QWidget, QDockWidget, QLabel, QVBoxLayout, QComboBox, QDoubleSpinBox, 
                         QApplication, QMessageBox)
from src.gui.qt.QtCore import SIGNAL, QVariant
from src.gui.qthelpers import OfSs
from pandas import HDFStore

from src.gui.qthelpers import MyComboBox, MyDoubleSpinBox
from src.gui.config import CONF


class ParametersWidget(QDockWidget):
    def __init__(self, parent = None):
        super(ParametersWidget, self).__init__(parent)
        self.setStyleSheet(OfSs.dock_style)
        # Create geometry
        self.setObjectName("Parameters")
        self.setWindowTitle(u"Configurer les paramètres")
        self.dockWidgetContents = QWidget()
        
        # Population 
        #  scenario selection
        self.population_choices= []
        self.population_combo = MyComboBox(self.dockWidgetContents, u'Choix du scénario de population', self.population_choices) 
        
        #  scenario prolongation
        self.population_prolong_choices= [(u'stable', 'stable'),
                                          (u'taux de croissance constant', 'constant')]
        self.population_prolong_combo = MyComboBox(self.dockWidgetContents, u'Choix du prolongement du scénario de population', self.population_prolong_choices) 
        
        # Population steady growth rate
        self.pop_grth = None
        self.pop_grth_spin = MyDoubleSpinBox(self.dockWidgetContents, u"Taux de croissance de la population", min_ = - 10, max_ = 10, step = .1, value = 2)   
        
        # Projection of net taxes (taxes - transfers)
        self.taxes_proj_choices =  [(u"Global/Taux de croissance", 'global_g'),
                                    (u"Par tête/taux de croissance", 'head_g')]
        self.taxes_proj_combo = MyComboBox(self.dockWidgetContents, u"Projection des prélèvements nets des tranferts", self.taxes_proj_choices)
        
        # Growth rate
        self.grth_spin = MyDoubleSpinBox(self.dockWidgetContents, u"Taux de croissance", min_ = - 100, max_ = 100, step = .1, value = 2)   
        
        # Discount rate
        self.dsct_spin = MyDoubleSpinBox(self.dockWidgetContents, u"Taux d'actualisation", min_ = - 100, max_ = 100, step = .1, value = 2)
        
        # Projection of the net expenses of the state
        self.state_proj_choices =  [(u"Global/Taux d'intérêt", 'global_r'),
                                    (u"Global/Taux de croissance", 'global_g'),
                                    (u"Par tête/taux d'intérêt", 'head_r'),
                                    (u"Par tête/taux de croissance", 'head_g')]
        self.state_proj_combo = MyComboBox(self.dockWidgetContents, u"Projection des contributions nettes de l'Etat", self.state_proj_choices)
                
        verticalLayout = QVBoxLayout(self.dockWidgetContents)
        verticalLayout.addWidget(self.population_combo)
        verticalLayout.addWidget(self.population_prolong_combo)
        verticalLayout.addWidget(self.pop_grth_spin)
        verticalLayout.addWidget(self.taxes_proj_combo)
        verticalLayout.addWidget(self.grth_spin)
        verticalLayout.addWidget(self.dsct_spin) 
        verticalLayout.addWidget(self.state_proj_combo)
        self.setWidget(self.dockWidgetContents)


        self.parent = parent    
        
        # Connectors
        self.connect(self.population_combo.box, SIGNAL('currentIndexChanged(int)'), self.set_population)        
        self.connect(self.population_prolong_combo.box, SIGNAL('currentIndexChanged(int)'), self.set_population_prolong)
        self.connect(self.taxes_proj_combo.box, SIGNAL('currentIndexChanged(int)'), self.set_taxes_proj)
        self.connect(self.state_proj_combo.box, SIGNAL('currentIndexChanged(int)'), self.set_state_proj_params)
        #self.connect(self.grth_spin.box, SIGNAL('currentIndexChanged(int)'), self.set_grth())

        # Initialize parameters        
#        self.init_parameters()


    def init_parameters(self):
        '''
        Initialize the parameters of the simulation 
        '''        
        try:
            population_file = CONF.get('paths', 'population_file')         
            store_pop = HDFStore(population_file,'r')                
            self.population_choices = store_pop.keys()
            store_pop.close()

            profiles_file = CONF.get('paths', 'profiles_file')         
            store_prof = HDFStore(profiles_file,'r')
            profiles = store_prof['profiles']
            
            self.set_population_prolong()
            self.set_taxes_proj()
            
        except Exception, e:
            self.population_loaded = False
            QMessageBox.warning(self, u"Impossible de lire les données de population", 
                                u"GA n'a pas réussi à lire les données de population. L'erreur suivante a été renvoyée:\n%s\n\nVous pouvez configuer le chemin vers le fichier de données  Fichier>Paramètres>Chemins>Fichier données population"%e)
            return False
        finally:

            
            store_prof.close()
            self.update_population_choices()
            QApplication.restoreOverrideCursor()

        self._input_profiles = profiles.reset_index()
        
        
        
    def set_population(self):
        '''
        Sets population data
        '''
        widget = self.population_combo.box
        if isinstance(widget, QComboBox):
            data = widget.itemData(widget.currentIndex())                
            data_name = unicode(data.toString())
            self.population_name = data_name
            self.emit(SIGNAL('population_changed()'))
            
    def update_population_choices(self):
        box = self.population_combo.box
        box.clear()
    #        for name, key in self.population_choice:
        for name in self.population_choices:
            box.addItem(name, QVariant(name))


    def set_population_prolong(self):
        '''
        Sets population prolongation method
        '''
        widget = self.population_prolong_combo.box
        if isinstance(widget, QComboBox):
            data = widget.itemData(widget.currentIndex())
            self.population_prolong = unicode(data.toString())
            self.emit(SIGNAL('population_changed()'))
#            self.emit(SIGNAL('population_prolong_changed()'))


    def set_taxes_proj(self):
        '''
        Sets taxes projection
        '''
        widget = self.taxes_proj_combo.box
        if isinstance(widget, QComboBox):
            data = widget.itemData(widget.currentIndex())                
            data_name = unicode(data.toString())
            self.taxes_proj = data_name
            self.emit(SIGNAL('taxes_proj_changed()'))



    def set_state_proj_params(self):
        '''
        Sets state projection parameters
        '''
        widget = self.state_proj_combo.box
        if isinstance(widget, QComboBox):
            data = widget.itemData(widget.currentIndex())                
            data_name = unicode(data.toString())
            self.state_proj = data_name
            self.emit(SIGNAL('state_proj_changed()'))
            
    def set_grth(self):
        '''
        Sets growth rate parameter
        '''
        widget = self.grth_spin.spin
        if isinstance(widget, QDoubleSpinBox):
            data = widget.value()                
            self.grth = float(data)
            self.emit(SIGNAL('rates_changed()'))
                        
    def set_dsct(self):
        '''
        Sets discount rate parameter
        '''
        widget = self.dsct_spin.spin
        if isinstance(widget, QDoubleSpinBox):
            data = widget.value()                
            self.dsct = float(data)
            self.emit(SIGNAL('rates_changed()'))
            
    def get_grth(self):
        '''
        Returns growth rate
        '''
        self.set_grth()
        return self.grth
    
    def get_dsct(self):
        '''
        Returns discount rate
        '''
        self.set_dsct()
        return self.dsct

    
    