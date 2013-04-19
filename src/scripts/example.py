# -*- coding:utf-8 -*-
'''
Created on 20 mars 2013

@author: Utilisateur
'''

from src import SRC_PATH
from src.lib.simulation import Simulation
import os

def test():
    
    country = "france"    
    population_filename = os.path.join(SRC_PATH, 'countries', country, 'sources',
                                       'data_fr', 'proj_pop_insee', 'proj_pop.h5')
    profiles_filename = os.path.join(SRC_PATH, 'countries', country, 'sources',
                                     'data_fr','profiles.h5')
    
    r = .05
    g = .02
    
    
    simulation = Simulation()
    simulation.set_country(country)
    print simulation.get_population_choices(population_filename)
    
    population_scenario = "projpop0760_FECcentESPcentMIGcent"
    
    simulation.load_population(population_filename, population_scenario)
    simulation.load_profiles(profiles_filename)
    print simulation.population
    print simulation.profiles
    simulation.set_population_projection(year_length=200, method="constant")
    simulation.set_tax_projection(method="per_capita", rate=0)
    simulation.set_growth_rate(g)
    simulation.set_discount_rate(r)        
    simulation.create_cohorts()
    

    
if __name__ == '__main__':
    test()
    