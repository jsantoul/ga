# -*- coding:utf-8 -*-
'''
Created on 26 avr. 2013

@author: Mahdi Ben Jelloul
'''

from pandas import DataFrame, merge
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

#How do I use this attrib correctly ?
def create_testing_population_dataframe(year_start = None, year_end = None, rate = None):
    """
    """
    if year_start is None or year_end is None:
        #raise Exception("year_start and year_end are both required arguments")
        print "year_start and year_end are both required arguments"
        return
        
    if rate is None:       
        population_dataframe = create_empty_population_dataframe(year_start, year_end)
    else:
        population_dataframe = create_empty_population_dataframe(year_start, year_end)
#         created classic dataframe with constant population, now updating with growth 
      
        population_dataframe['grth'] = 1
        grouped = population_dataframe.groupby(level = ['sex', 'age'])['grth']
        nb_years = year_end-year_start
        population_dataframe['grth'] = grouped.transform(lambda x: (1+rate)**(arange(nb_years)))
        population_dataframe['pop'] = population_dataframe['pop']*population_dataframe['grth']
        del population_dataframe['grth']

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


if __name__ == '__main__':
    pass