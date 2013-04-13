# -*- coding:utf-8 -*-
# Created on 22 mars 2013
# Copyright © 2013 Clément Schaff, Mahdi Ben Jelloul

# Good docs about nosetest
# http://ivory.idyll.org/articles/nose-intro.html
# https://nose.readthedocs.org/en/latest/testing.html

import nose
from pandas import DataFrame, merge
from src.core.simulation import Simulation

def test_1():

    # Building population and profiles dataframes 
    # with ones everywhere

    df_age = DataFrame({ 'age': range(0,101)})
    df_sex = DataFrame({ 'sex': [0,1],})
    df_year = DataFrame({ 'year': range(2007,2061)})
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
    print 'pv'
    print pv
    
    print 'get_value'
    
    print  pv.get_value((0,0,2007), "tax") 
    print  pv.get_value((0,0,2008), "tax")

if __name__ == '__main__':
    
    test_1()
#    nose.runmodule(argv=[__file__, '-vvs', '-x', '--pdb', '--pdb-failure'],
#                   exit=False)