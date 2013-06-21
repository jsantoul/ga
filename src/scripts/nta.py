# -*- coding:utf-8 -*-

'''
Created on 21 juin 2013

@author: Mahdi Ben Jelloul
'''

from src import SRC_PATH
import os
from src.lib.simulation import Simulation


def test():
    country = "france"    
    population_filename = os.path.join(SRC_PATH, 'countries', country, 'sources',
                                           'data_fr', 'proj_pop_insee', 'proj_pop.h5')
    profiles_filename = os.path.join(SRC_PATH, 'countries', country, 'sources',
                                         'data_fr','NTA', 'nta.h5')
    simulation = Simulation()
    population_scenario = "projpop0760_FECbasESPbasMIGbas"
    simulation.load_population(population_filename, population_scenario)
    simulation.load_profiles(profiles_filename)
    
    #Setting parameters
    year_length = 200
    r = 0.03
    g = 0.01
    n = 0.00
    net_gov_wealth = -3217.7e+09
    net_gov_spendings = 0
    simulation.set_population_projection(year_length=year_length, method="stable")
    simulation.set_tax_projection(method="per_capita", rate=g)
    simulation.set_growth_rate(g)
    simulation.set_discount_rate(r) 
    simulation.set_population_growth_rate(n)
 
    simulation.profiles = simulation.profiles.xs(1979,axis=0,level="year")
    simulation.profiles.reset_index(inplace=True)
    simulation.profiles['year']=1979
    simulation.profiles.set_index(['age', 'sex', 'year'], inplace=True)  
#     simulation.profiles = simulation.profiles.ix[(0,0,1979):(100,1,1979)]  
    simulation.create_cohorts()
    simulation.set_population_projection()
    print simulation.cohorts
    
    
    

if __name__ == '__main__':
    test()