# -*- coding:utf-8 -*-
# Created on 22 mars 2013
# Copyright © 2013 Clément Schaff, Mahdi Ben Jelloul

# Good docs about nosetest
# http://ivory.idyll.org/articles/nose-intro.html
# https://nose.readthedocs.org/en/latest/testing.html

import nose
from pandas import DataFrame, merge
from src.lib.simulation import Simulation


def create_test_simulation():
    pass

def test_population_projection():
    pass

def test_tax_projection():
    pass

def test_pv_ga():
    pass


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

    profiles_dataframe = df2[df2.year==2007 ]
    profiles_dataframe["tax"] = 1 

    profiles_dataframe = profiles_dataframe.set_index(['age', 'sex','year'])
    
    r = 0
    g = 0
    simulation = Simulation()  
    simulation.set_population(population_dataframe)
    simulation.set_profiles(profiles_dataframe)
    simulation.set_population_projection(year_length=200, method="constant")
    
    simulation.set_tax_projection(rate = g, method="per_capita")
    simulation.set_growth_rate(g)
    simulation.set_discount_rate(r)        
    simulation.create_cohorts()
    
    cohorts = simulation.cohorts
    pv =  cohorts.pv_ga("tax")
#    print 'pv'
#    print pv
    
#    print 'get_value'
    
    assert  pv.get_value((0,0,2007), "tax") == 54
    assert  pv.get_value((0,0,2008), "tax") == 53

def test_2():
    
    #Attempt to recreate the test with different parameters TODO: try to avoid sample generation again
    df_age = DataFrame({ 'age': range(0,101)})
    df_sex = DataFrame({ 'sex': [0,1],})
    df_year = DataFrame({ 'year': range(2001,2061)})
    #We have created 3 dataframes with different ranges, now assigning the value 1 for each key
    df_age['key'] = 1
    df_sex['key'] = 1    
    df_year['key'] = 1 
    #Merging the key values of the first and second dataframes then resetting to 1 ?
    df = merge(df_age, df_sex,on='key')[['age', 'sex']]     
    df['key'] = 1
    df2 = merge(df, df_year,on='key')[['age', 'sex','year']]
    population_dataframe = df2.set_index(['age', 'sex','year'])
    
    #TODO: a quoi sert cette ligne ? ajouter une catégorie et mettre la même valeur partout ?
    population_dataframe['pop'] = 1
    
    profiles_dataframe = df2[df2.year==2007 ]
    profiles_dataframe["tax"] = 1 
    profiles_dataframe["subsidies"] = 0.5
    profiles_dataframe = profiles_dataframe.set_index(['age', 'sex','year'])
    
    r = 0.00
    g = 0.00
    
    simulation = Simulation()  
    simulation.set_population(population_dataframe)
    simulation.set_profiles(profiles_dataframe)
    
    simulation.set_population_projection(year_length=200, method="constant")
    simulation.set_tax_projection(rate = g, method="per_capita")
    
    simulation.set_growth_rate(g)
    simulation.set_discount_rate(r)        
    simulation.create_cohorts()
        
    cohorts = simulation.cohorts
#    print cohorts
    pv1 =  cohorts.pv_ga("subsidies")

    pv2 =  cohorts.pv_ga("tax")
    
    print pv1.get_value((0,0,2007), "subsidies")
    print pv2.get_value((0,0,2007), "tax")



if __name__ == '__main__':
    
    test_1()
    nose.core.runmodule(argv=[__file__, '-vvs', '-x', '--pdb', '--pdb-failure'],
                   exit=False)
