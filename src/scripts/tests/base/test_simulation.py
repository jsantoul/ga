# -*- coding:utf-8 -*-
'''
Created on 26 avr. 2013

@author: Mahdi Ben Jelloul, Jérôme SANTOUL
'''
import nose
from src.lib.simulation import Simulation
from src.scripts.tests.utils import (create_testing_population_dataframe,
                                     create_constant_profiles_dataframe)

#===============================================================================
# Testing the simulation object construction plus population and tax projection.
#===============================================================================

def test_simulation_creation():

    # Building population and profiles dataframes 
    # with ones everywhere
    population_dataframe = create_testing_population_dataframe(year_start=2001, year_end=2061)

    profiles_dataframe = create_constant_profiles_dataframe(population_dataframe, tax=1)

    r = 0
    g = 0
    simulation = Simulation()  
    simulation.set_population(population_dataframe)
    simulation.set_profiles(profiles_dataframe)
    simulation.set_population_projection(year_length=200, method="constant")
    
#    simulation.set_tax_projection(rate = g, method="per_capita")
    simulation.set_tax_projection(rate = g, method="aggregate")
    
    simulation.set_growth_rate(g)
    simulation.set_discount_rate(r)        
    simulation.create_cohorts()
    
    cohorts = simulation.cohorts
    pv =  cohorts.aggregate_generation_present_value("tax")

    assert  pv.get_value((0,0,2007), "tax") == 54
    assert  pv.get_value((0,0,2008), "tax") == 53



if __name__ == '__main__':
    nose.core.runmodule(argv=[__file__, '-v', '-i test_*.py'])    