# -*- coding:utf-8 -*-
# Created on 22 mars 2013
# Copyright © 2013 Clément Schaff, Mahdi Ben Jelloul

# Good docs about nosetest
# http://ivory.idyll.org/articles/nose-intro.html
# https://nose.readthedocs.org/en/latest/testing.html

import nose
from pandas import DataFrame, merge
from src.lib.simulation import Simulation
from src.lib.cohorte import Cohorts
from numpy import arange

#===============================================================================
# Some test function to generate fake data
#===============================================================================

def create_empty_population_dataframe(year_start, year_end):
    # Building population and profiles dataframes 
    # with ones everywhere
    # the length of the dataframe can be adjusted
    df_age = DataFrame({ 'age': range(0,101)})
    df_sex = DataFrame({ 'sex': [0,1],})
    df_year = DataFrame({ 'year': range(year_start,year_end)})
    df_age['key'] = 1
    df_sex['key'] = 1    
    df_year['key'] = 1 
    df = merge(df_age, df_sex,on='key')[['age', 'sex']]
                      
    df['key'] = 1
    df2 = merge(df, df_year,on='key')[['age', 'sex','year']]
    population_dataframe = df2.set_index(['age', 'sex','year'])
    population_dataframe['pop'] = 1
    return population_dataframe

def create_testing_population_dataframe(year_start, year_end, rate = None):
    
    if rate is None:       
        population_dataframe = create_empty_population_dataframe(year_start, year_end)
    else:
        population_dataframe = create_empty_population_dataframe(year_start, year_end)
#         created classic dataframe with constant population, now updating with growth 
      
        population_dataframe['grth'] = 1
        grouped = population_dataframe.groupby(level = ['sex', 'age'])['grth']
        nb_years = year_end-year_start
#        print population_dataframe
        population_dataframe['grth'] = grouped.transform(lambda x: (1+rate)**(arange(nb_years)))
        population_dataframe['pop'] = population_dataframe['pop']*population_dataframe['grth']
        population_dataframe.drop(['grth'], axis=1)
        #=======================================================================
        # self-testing part of the function
        #=======================================================================
        
#         test_value1 = population_dataframe.get_value((0,1,2011), 'pop')
#         print test_value1
#         assert test_value1 == 1024
        
        
#    print population_dataframe.get_value((0,1,2010), 'pop')
    return population_dataframe

def create_constant_profiles_dataframe(population_dataframe, **kwargs):
    """
    Function which creates a profile dataframe with a single year index
    """
    temp = zip(*population_dataframe.index)
    year_min = min(temp[2])
    population_dataframe.reset_index(inplace=True)
    profiles_dataframe = population_dataframe[population_dataframe.year==year_min]
    population_dataframe.set_index(["age","sex","year"],inplace=True)   
    for key, value in kwargs.iteritems():
        profiles_dataframe[key] = value
    del profiles_dataframe["pop"]
    profiles_dataframe.set_index(["age","sex","year"],inplace=True)
    return profiles_dataframe

def test_empty_frame_generation():
    """
    TODO Simple test to see if the function create_empty_dframe_simulation works correctly
    """
    year_start = 2001
    year_end = 2061
    population_dataframe = create_empty_population_dataframe(year_start, year_end)
    test_value = population_dataframe.get_value((0,0,2043), "pop")
    assert test_value == 1
         
#===============================================================================
# Some tests of the object Cohorts
#===============================================================================

def test_population_projection():
    # Create cohorts
    population = create_empty_population_dataframe(2001, 2061)
    cohorts = Cohorts(data = population, columns = ['pop'])

    # Complete population projection
    year_length = 200
    method = 'stable'   
    cohorts.population_project(year_length, method = method)
    test_value = cohorts.get_value((0,0,2161), "pop")
#    print test_value
    assert test_value == 1

#     print population_dataframe.head()
#     
#     population_dataframe.reset_index(inplace=True)
#     population_dataframe_restricted = population_dataframe[population_dataframe.year==2007 ]
#     population_dataframe_restricted["tax"] = 1 
# 
#     profiles_dataframe = population_dataframe_restricted.set_index(['age', 'sex','year'])
#     
#     population_dataframe.set_index(['age', 'sex','year'], inplace=True)
#     simulation = Simulation()
#     simulation.set_population(population_dataframe)
#     simulation.set_profiles(profiles_dataframe)
#     simulation.set_population_projection(year_length=200, method="constant")
# 
#     r = 0.00
#     g = 0.00
#     simulation.set_growth_rate(g)
#     simulation.set_discount_rate(r)       
# 
#     simulation.create_cohorts()
#     
#     
#     test_value = simulation.cohorts.get_value((0,0,2100),"tax")
#     assert test_value == 1    
#     pass

def test_column_combination():
    year_start = 2001

    pop_dataframe = create_empty_population_dataframe(year_start, 2061)
    print pop_dataframe
    profiles_dataframe = create_constant_profiles_dataframe(pop_dataframe, tax=-1.0, sub=0.5)
    print profiles_dataframe
    profiles_dataframe['net'] = profiles_dataframe.sum(axis=1) 
    print profiles_dataframe['net']
    # TODO: needs an assert


def test_fill_cohort():   
    population = create_empty_population_dataframe(2001, 2061)
    profiles = create_constant_profiles_dataframe(population, tax = -1, subsidies = 0.5)
    cohorts_test = Cohorts(data = population, columns = ['pop'])
    cohorts_test.fill(profiles, year = None)
    test_value = cohorts_test.get_value((0,0,2060), 'tax')
    print test_value
    # TODO: needs an assert


def test_dsct():
    population = create_empty_population_dataframe(2001, 2061)
    cohorts = Cohorts(data = population, columns = ['pop']) 
    cohorts.gen_dsct(0.05)
    test_value = cohorts.get_value((0,0,2060), 'dsct')
#    print test_value
    assert test_value <= 1
    
def test_tax_projection():

    population = create_empty_population_dataframe(2001, 2061)
    profile = create_constant_profiles_dataframe(population, tax = -1, sub=0.5) 
    g = 0.05
    r = 0
    cohort = Cohorts(population)
    cohort.fill(profile)
    typ = 'tax'
    cohort.proj_tax(g, r, typ,  method = 'per_capita')
#    print cohort
    test_value = cohort.get_value((0,1,2002), 'tax')
    test_value2 = cohort.get_value((0,1,2002), 'sub')
#    print test_value, test_value2
    # TODO: I don't understand the following
    if typ is None:
        assert test_value2 > 0.5 and test_value < -1
        return
    elif 'sub' in typ:
        assert test_value2 > 0.5
        if 'tax' in typ: 
            assert test_value < -1
    elif 'tax' in typ:
        assert test_value < -1
    
def test_tax_projection_aggregated():
    population = create_testing_population_dataframe(2001, 2061, 1)
    profile = create_constant_profiles_dataframe(population, tax = -1, sub=0.5)
    g = 0.0
    r = 0.0 
    cohort = Cohorts(population)
    cohort.fill(profile)
    typ = None
    cohort.proj_tax(g, r, typ,  method = 'aggregate')
    test_value = cohort.get_value((0,1,2002), 'tax')
    test_value2 = cohort.get_value((0,1,2002), 'sub')
    print test_value, test_value2
#     if typ is None:
#         assert test_value2 > 0.5 and test_value < -1
#         return
#     elif 'sub' in typ:
#         assert test_value2 > 0.5
#         if 'tax' in typ: 
#             assert test_value < -1
#     elif 'tax' in typ:
#         assert test_value < -1  
    pass


def test_pv_ga():
    pass



#===============================================================================
# Testing the simulation object construction plus population and tax projection.
#===============================================================================
def test_1():

    # Building population and profiles dataframes 
    # with ones everywhere

    df_age = DataFrame({ 'age': range(0,101)})
    df_sex = DataFrame({ 'sex': [0,1],})
    df_year = DataFrame({ 'year': range(2001,2061)})
    df_age['key'] = 1
    df_sex['key'] = 1    
    df_year['key'] = 1 
    df = merge(df_age, df_sex,on='key')[['age', 'sex']]
                      
    df['key'] = 1
    df2 = merge(df, df_year,on='key')[['age', 'sex','year']]
    population_dataframe = df2.set_index(['age', 'sex','year'])
    population_dataframe['pop'] = 1

    profiles_dataframe = df2[df2.year==2001 ]

    profiles_dataframe["tax"] = 1 

    profiles_dataframe = profiles_dataframe.set_index(['age', 'sex','year'])
    
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
    print cohorts._types_years
#    print 'pv'
#    print pv
    
#    print 'get_value'
    
    assert  pv.get_value((0,0,2007), "tax") == 54
    assert  pv.get_value((0,0,2008), "tax") == 53



if __name__ == '__main__':

#    test_1()
#    create_testing_population_dataframe(2001, 2061, 1)
#    test_population_projection() 
#    test_tax_projection() #Now working flawlessly
    #===========================================================================
    test_tax_projection_aggregated() #Not working as intended : 
    # pop growth of 100% with no economic growth leads to 100% per_capita tax growth each period 
    # instead of halving per_capita tax each period 
    #===========================================================================
#     test_fill_cohort() #Working
#     test_dsct() #Working
#     population_dataframe = create_empty_population_dataframe(2007, 2060)
#     profiles = create_constant_profiles_dataframe(population_dataframe, tax = -1, subsidies = .5)
#     print profiles
#    test_empty_frame_generation()
#    test_population_projection()
#     test_column_combination() #Working
#    nose.core.runmodule(argv=[__file__])
#    nose.core.runmodule(argv=[__file__, '-vvs', '-x', '--pdb', '--pdb-failure'],
#                    exit=False)

