# -*- coding:utf-8 -*-
'''
Created on 26 avr. 2013

@author: Mahdi Ben Jelloul, Jérôme SANTOUL
'''
from __future__ import division
import nose
from src.lib.simulation import Simulation
from src.scripts.tests.utils import (create_testing_population_dataframe,
                                     create_constant_profiles_dataframe,
                                     create_neutral_profiles_cohort)

import os
from src.lib.simulation import Simulation
from src.lib.cohorts.accounting_cohorts import AccountingCohorts
from pandas import read_csv, HDFStore, concat, ExcelFile, DataFrame, MultiIndex
from numpy import array, hstack, arange, NaN
import matplotlib.pyplot as plt
from src import SRC_PATH
from src.lib.cohorts.accounting_cohorts import AccountingCohorts


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



# TODO: create the test    
def test_compute_gen_imbalance():
    size_generation = 1
    cohort = create_neutral_profiles_cohort(population = size_generation)
    simulation = Simulation()    
    simulation.discount_rate = 0
    simulation.growth_rate = 0
    simulation.cohorts = cohort
    simulation.create_present_values('tax')
    gen_imbalance = simulation.compute_gen_imbalance(typ = 'tax')
#     print gen_imbalance
    assert gen_imbalance == -5000.0/(2*199.0)

def test_comparison():
    
    population_dataframe = create_testing_population_dataframe(year_start=2001, year_end=2261, population=2)
    profiles_dataframe = create_constant_profiles_dataframe(population_dataframe, tax=1)
    
    r = 0.00
    g = 0.00
    n = 0.00
    
    simulation = Simulation()    
    simulation.population = population_dataframe
    simulation.population_alt = population_dataframe
    
    simulation.profiles = profiles_dataframe
    
    net_gov_wealth = -10
    net_gov_spending = 0
    taxes_list = ['tax']
    payments_list = ['sub']
    
    simulation.set_population_projection(year_length=simulation.year_length, method="exp_growth")
    simulation.set_tax_projection(method="per_capita", rate=g)
    simulation.set_growth_rate(g)
    simulation.set_discount_rate(r)
    simulation.set_population_growth_rate(n)
    simulation.set_gov_wealth(net_gov_wealth)
    simulation.set_gov_spendings(net_gov_spending, default=True)
    simulation.create_cohorts()
    simulation.create_present_values(typ='tax')
    
    simulation.cohorts_alt = simulation.cohorts
    
    simulation.cohorts_alt.loc[[x==2102 for x in simulation.cohorts_alt.index.get_level_values(2)], 'tax'] = (-100)
    simulation.create_present_values(typ='tax', default=False)
    
    ipl_base = simulation.compute_ipl(typ='tax')
    ipl_alt = simulation.compute_ipl(typ='tax', default=False, precision=False)
    
    #Saving the decomposed ipl:
    to_save = simulation.break_down_ipl(typ='tax', default=False, threshold=60)
       
#     to_save = age_class_pv
    xls = "C:/Users/Utilisateur/Documents/GitHub/ga/src/countries/france/sources/Carole_Bonnet/choc_test_alt.xlsx"
         
    to_save.to_excel(xls, 'ipl')
    print ipl_base
    print ipl_alt
    assert ipl_base == -105232



if __name__ == '__main__':
#     test_compute_gen_imbalance()
    test_comparison()
#     nose.core.runmodule(argv=[__file__, '-v', '-i test_*.py'])    