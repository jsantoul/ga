# -*- coding:utf-8 -*-
'''
Created on 3 mai 2013

@author: Jérôme Santoul
'''

from src.lib.simulation import Simulation
from src.lib.cohorte import Cohorts
from pandas import DataFrame, read_csv, ExcelFile, HDFStore, read_table
import matplotlib.pyplot as plt
import numpy as np
from numpy import hstack

"""
Attempting to recreate some graphs made by Carole BONNET in her paper : 
Carole Bonnet « Comptabilité générationnelle appliquée à la France : quelques facteurs d'instabilité des résultats », Economie & prévision 3/2002 (no 154), p. 59-78. 
URL : www.cairn.info/revue-economie-et-prevision-2002-3-page-59.htm. 
"""

#loading population and profiles in dataframes
#TODO: convert all files in HDF5 to allow usage of HDFstore method.
# ISSUE: there is an unexplained problem with the path : C:\Users\Utilisateur\Documents\GitHub\ga\src\countries\france\sources\data_fr
#the folder \france is not recognised
population = read_table('C:\Users\Utilisateur\Documents\GitHub\ga\src\countries\pop.txt', sep=',')
# print population
population = population.set_index(['age', 'sex'])
population = population.stack()
population = population.reset_index()
population['year'] = population['level_2']
population['pop'] = population[0]
del population['level_2']
del population[0]
population = population.set_index(['age', 'sex', 'year'])
print population['pop']

net_payments = Simulation()
net_payments.set_population(population)
 
France = 'France'
net_payments.set_country(France)
r = 0.0
g = 0.01
net_payments.set_discount_rate(r)
net_payments.set_growth_rate(g)
print net_payments, net_payments.growth_rate, net_payments.discount_rate, net_payments.country
   
    
# net_payments.load_population("C:\Users\Utilisateur\Documents\GitHub\ga\src\countries\france\sources\data_fr", "pop.csv")
# net_payments.load_profiles("C:\Users\Utilisateur\Documents\GitHub\ga\src\countries\france\sources\data_fr", "profiles.h5")
net_payments.load_profiles("C:\Users\Utilisateur\Documents\GitHub\ga\src\countries\profiles.h5", "profiles.h5")
# Not sure if useful
# net_payments.get_population_choices("src.countries.france.sources.data_fr.poj_pop_insee.pop.csv")
  
#Setting parameters
year_length = 100
#===============================================================================
# #Does not work because of error : 
#   File "C:\Users\Utilisateur\Documents\GitHub\ga\src\lib\simulation.py", line 117, in create_cohorts
#     cohorts.population_project(year_length, method = method) 
#   File "C:\Users\Utilisateur\Documents\GitHub\ga\src\lib\cohorte.py", line 380, in population_project
#     if ( first_year + year_length ) > last_year:
# TypeError: cannot concatenate 'str' and 'int' objects
# net_payments.set_population_projection(year_length = year_length, method = "exp_growth", rate = 0)
# net_payments.set_tax_projection(method = "per_capita", typ = None, rate = g, discount_rate = r)
#===============================================================================

#   
# #Creating cohorts
# net_payments.create_cohorts()
# # If I understand correctly, the net_payment is now a cohort object with the values we are looking for.
#   
# #Creating a column with total taxes paid.
# for typ in net_payments._types:
#     net_payments['total'] += hstack(net_payments[typ])


cohorts = Cohorts(data = population, columns = ['pop'])      
        # Complete population projection
cohorts.population_project(year_length, method = "exp_growth")
        # Generate discount factor and growth factor
cohorts.gen_dsct(net_payments.discount_rate)
cohorts.gen_grth(net_payments.growth_rate)
        # Fill profiles
cohorts.fill(net_payments.profiles)
method = net_payments.tax_projection["method"]
rate = net_payments.tax_projection["rate"]
cohorts.proj_tax(rate=rate, method=method)

print cohorts






