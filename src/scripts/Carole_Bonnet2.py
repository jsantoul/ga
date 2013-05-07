# -*- coding:utf-8 -*-
# Created on 6 mai 2013
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © #2013 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)


import os
from src.lib.simulation import Simulation
from src.lib.cohorte import Cohorts
from pandas import read_csv, HDFStore, concat
from numpy import array, hstack
from src import SRC_PATH




def test():
    
    population = read_csv('C:\Users\Utilisateur\Documents\GitHub\ga\src\countries\France\sources\data_fr\pop.csv', sep=',')
    # print population.columns
    population = population.set_index(['age', 'sex'])
    population = population.stack()
    population = population.reset_index()
    population['level_2'] = population.level_2.convert_objects(convert_numeric=True)

    population['year'] = population['level_2']
    population['pop'] = population[0]
    del population['level_2']
    del population[0]
    population = population.set_index(['age', 'sex', 'year'])

    #Remove the years 2007 and beyond to ensure integrity when combined with INSEE data
    year = list(range(1991, 2007, 1))
    filter_year = array([x in year for x in population.index.get_level_values(2)])
    population = population.loc[filter_year, :]
    
    
        
    country = "france"    
    population_filename = os.path.join(SRC_PATH, 'countries', country, 'sources',
                                           'data_fr', 'proj_pop_insee', 'proj_pop.h5')
    profiles_filename = os.path.join(SRC_PATH, 'countries', country, 'sources',
                                         'data_fr','profiles.h5')
    
    
#     population.append_to_multiple(population_filename, "table", append = True)
    
#     Previous attempt to fuse INSEE and the pop data of C Bonnet
#     #Loading insee data
#     projection = HDFStore('C:\Users\Utilisateur\Documents\GitHub\ga\src\countries\France\sources\data_fr\proj_pop_insee\proj_pop.h5', 'r')
#     projection_dataframe = projection['/projpop0760_FECbasESPbasMIGbas']
#  
#     #Combining
#     concatened = concat([population, projection_dataframe], verify_integrity = True)
#     concatened = concatened.reset_index()
#     concatened['year'] = concatened.year.convert_objects(convert_numeric=True)
#     concatened = concatened.set_index(['age', 'sex', 'year'])
#  
#     #Saving as HDF5 file
#     export = HDFStore('neo_population.h5')
#     export.append('pop', concatened, data_columns = concatened.columns)
#     export.close()
#     export = HDFStore('neo_population.h5', 'r')



    
    simulation = Simulation()
#     print simulation.get_population_choices(population_filename)
    check = HDFStore(population_filename)
#     print check
    check.close()
    population_scenario = "projpop0760_FECbasESPbasMIGbas"
        
    simulation.load_population(population_filename, population_scenario)
    simulation.load_profiles(profiles_filename)
    """
    Hypothesis set #1 : 
    actualization rate r = 3%
    growth rate g = 1%
    """
    r = 0.03
    g = 0.01
    simulation.set_discount_rate(r)
    simulation.set_growth_rate(g)
    
    #Setting parameters
    year_length = 100
    
    simulation.set_population_projection(year_length=year_length, method="exp_growth")
    simulation.set_tax_projection(method="per_capita", rate=g)
    simulation.set_growth_rate(g)
    simulation.set_discount_rate(r)        
    simulation.create_cohorts()
#     print simulation.cohorts.head()
    print simulation.cohorts._types
    simulation.cohorts['total_taxes'] = 0
    simulation.cohorts['total_payments'] = 0
    set_taxes = ['tva', 'tipp', 'cot', 'irpp', 'impot', 'property']
    set_payments = ['chomage', 'retraite', 'revsoc', 'maladie', 'educ']
    print simulation.cohorts._types
    for typ in set_taxes:
        simulation.cohorts['total_taxes'] += hstack(simulation.cohorts[typ])
    for typ in set_payments:
        simulation.cohorts['total_payments'] += hstack(simulation.cohorts[typ])
    #Net_transfers = money recieved from the state minus tax paid
    simulation.cohorts['net_transfers'] = simulation.cohorts['total_taxes'] - simulation.cohorts['total_payments']
#     print simulation.cohorts['net_transfers']
#     print simulation.cohorts.get_value((5,1,2010), 'net_transfers')

    #Creating age classes
    simulation.cohorts = Cohorts(simulation.cohorts.create_age_class(step = 5))
    simulation.cohorts._types = [u'tva', u'tipp', u'cot', u'irpp', u'impot', u'property', u'chomage', u'retraite', u'revsoc', u'maladie', u'educ', u'net_transfers']
    print simulation.cohorts._types
    
    #Generating generationnal accounts
    aggregate_gen_pv = simulation.cohorts.aggregate_generation_present_value(typ = 'net_transfers', discount_rate = simulation.discount_rate)
    print aggregate_gen_pv.xs((0, 2007), level = ['sex', 'year'])
    print aggregate_gen_pv.xs((0, 2008), level = ['sex', 'year'])

    
if __name__ == '__main__':
    test()
