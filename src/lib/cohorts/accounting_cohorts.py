# -*- coding:utf-8 -*-
# Copyright © 2012 Clément Schaff, Mahdi Ben Jelloul
'''
Created on 14 mai 2013

@author: Jérôme SANTOUL
'''
from __future__ import division
from pandas import concat, DataFrame
from numpy import array, arange, NaN
from src.lib.cohorts.cohort import Cohorts
import matplotlib.pyplot as plt

class AccountingCohorts(Cohorts):
    '''
    Stores computed net transfers obtained with data from data_Cohorts. Data should be a data frame with multindexing and at most one 
    column dimension. These cohorts should only contain national accounting data.
    Default columns are 'year', set col_names if different.
    Methods of this class allow index computation for national accounting.
    '''


    def __init__(self, data=None, index=None, columns=None, 
                 dtype=None, copy=False):
        super(AccountingCohorts, self).__init__(data, index, columns , dtype, copy)
     
    def extract_generation(self, year, typ, age = None):
        """
        Returns a dataframe containning chosen data to follow the evolution of a given group over time.
         
        Parameters
        ----------
        year : Int
                A year of reference contained in the cohort.
        typ : Str
              A column or a list of columns of the cohort that one wants to follow
        age : Int
              Default is zero. The age of reference of the group one is interested in.
         
        Returns
        -------
        generation_cohort : a cohort dataframe with the data of the group of people 
                            whose given references belong to. 
        """      
 
        if year is None:
            raise Exception('a year of reference is needed')
        if year not in list(self.index_sets['year']):
            raise Exception('The given year is not valid')
        year_min = array(list(self.index_sets['year'])).min()
        year_max = array(list(self.index_sets['year'])).max()
        if typ not in self.columns:
            raise Exception('the given column is not in the cohort')

        #Normalizing the age if not given
        if age is None:
            age = 0
                 
        pvm = self.xs(0, level='sex')
        pvf = self.xs(1, level='sex')
         
        #Creating lower bounds for the filter generation
        if age > 0:
            if year-age >= year_min:
                start_age = 0
                year_start = year - age
            else:
                start_age = age - (year - year_min)
                year_start = year_min
        else:
            start_age = age
            year_start = year
 
        #Creating upper bounds for filter_list
        if year + (100-age) >= year_max:
            year_end = year_max
            end_age = age + (year_max - year)
        else:
            year_end = year + 100 - age
            end_age = 100
 
        #Creating the filtering list
        filter_list = zip(range(start_age, end_age+1), range(year_start, year_end+1))
         
#         Generation the generation DataFrame
        generation_data_male = pvm.loc[filter_list, typ]
        generation_data_female = pvf.loc[filter_list, typ]
          
        pieces = [generation_data_male, generation_data_female]
        res =  concat(pieces, keys = [0,1], names = ["sex"] )
        res = res.reorder_levels(['age','sex','year'])
          
        generation_cohort = Cohorts(res)
        generation_cohort.columns = [typ]
        return generation_cohort
 
 
    
    def create_age_class(self, step = 1, typ = None):
        """
        Transform a filled cohort dataframe by regrouping 
        age indexies in age class indexies. The size of the age class is indicated by the step argument
         
        Parameters
        ----------
        step : Int
        The number of years included in the age class
         
        Returns
        -------
        res : A DataFrame of the Cohorts class with age indexes replaced with class indicies
        """
        
        if typ is None:
            typ = self._types
        
        # Separating Men and Women
        pvm = self.xs(0, level='sex')
        pvf = self.xs(1, level='sex')
        pvm.reset_index(inplace = True)
        pvf.reset_index(inplace = True)
         
        #Transforming the age indexes
        serie = array(pvm.age)
        pvm['age'] = array((serie//step)*step)
        pvf['age'] = array((serie//step)*step)
        
#         #Old version of age class creation using the simulation.percapita_pv
#         age_class_pvm = pvm.groupby(['age', 'year']).mean()
#         age_class_pvf = pvf.groupby(['age', 'year']).mean() 

       
        #New version which takes in account the change of population over the years
        print pvm        
        age_class_pvm = pvm.groupby(['age', 'year']).sum()
        age_class_pvf = pvf.groupby(['age', 'year']).sum()
        print age_class_pvm
        
        age_class_pvm[typ] *= 1.0/age_class_pvm['pop']
        age_class_pvf[typ] *= 1.0/age_class_pvf['pop']
         
        #Put back the dataframes together
        pieces = [age_class_pvm, age_class_pvf]
        res =  concat(pieces, keys = [0,1], names = ["sex"] )
        res = res.reset_index()
        res = res.set_index(['age', 'sex', 'year'])
        return AccountingCohorts(res)            
 
    def compute_ipl(self, typ, net_gov_wealth = None, net_gov_spendings = None, precision=False):
        """
        Return a value of the intertemporal public liability. 
        The dataframe has to contain the aggregated present values of transfer in order 
        for the method to work correctly
         
        Parameters
        ----------
        typ : the column containing the data used in the calculation
         
        net_gov_wealth : the present value of the wealth of the government
         
        net_gov_spendings : the present value of unventilated
         
        Returns
        -------
         
        ipl : float
            the value of the intertemporal public liability
        """
        if net_gov_wealth is None:
            net_gov_wealth = 0
        if net_gov_spendings is None:
            net_gov_spendings = 0
         
        year_min = array(list(self.index_sets['year'])).min()
        year_max = array(list(self.index_sets['year'])).max()
        before_year_max = array(list(self.index_sets['year'])).max() - 1
        
        age_max = array(list(self.index_sets['age'])).max()
         
        past_gen_dataframe = self.xs(year_min, level = 'year')
        past_gen_dataframe = past_gen_dataframe.cumsum()
        past_gen_transfer = past_gen_dataframe.get_value((age_max, 1), typ)
#         print '    past_gen_transfer = ', past_gen_transfer
 
         
        future_gen_dataframe = self.xs(0, level = 'age')
        future_gen_dataframe = future_gen_dataframe.cumsum()
        future_gen_transfer = future_gen_dataframe.get_value((1, year_max), typ)
#         print '    future_gen_transfer =', future_gen_transfer
        
        #Note : do not forget to eliminate values counted twice
        ipl = net_gov_spendings - net_gov_wealth - future_gen_transfer - past_gen_transfer + past_gen_dataframe.get_value((0, 0), typ)
        
        if precision:
            future_gen_transfer_last = future_gen_dataframe.get_value((1, before_year_max), typ)
            last_ipl = net_gov_spendings - net_gov_wealth - past_gen_transfer - future_gen_transfer_last + past_gen_dataframe.get_value((0, 0), typ)
            
            to_return = (ipl - last_ipl)/ipl
        else:
            to_return = ipl
        
        return to_return
    
    def break_down_ipl(self, typ, net_gov_wealth = None, net_gov_spendings = None, threshold = 60):
        """
        This special method allows to examinate the series component of the ipl.
        
        Parameters
        ----------
        typ : the column containing the data used in the calculation
         
        net_gov_wealth : the present value of the wealth of the government
         
        net_gov_spendings : the present value of unventilated gov spendings
         
        Returns
        -------
         
        break_down_df : DataFrame
            a dataframe containing the terms of the series within the ipl. One line stores the constants.
        """
        if net_gov_wealth is None:
            net_gov_wealth = 0
        if net_gov_spendings is None:
            net_gov_spendings = 0
         
        year_min = array(list(self.index_sets['year'])).min()
        year_max = array(list(self.index_sets['year'])).max()
        before_year_max = array(list(self.index_sets['year'])).max() - 1
        
        age_max = array(list(self.index_sets['age'])).max()
         
        past_gen_dataframe = self.xs(year_min, level = 'year')
        past_gen_dataframe = past_gen_dataframe.cumsum()
        past_gen_transfer = past_gen_dataframe.get_value((age_max, 1), typ)
#         print '    past_gen_transfer = ', past_gen_transfer
 
        #On crée nos deux dataframe de travail : 
        future_gen_dataframe = self.xs(0, level = 'age')
        age_gen_df = self.xs(threshold, level = 'age')
        
        # On manipule les générations non-nées
        future_gen_dataframe = future_gen_dataframe.unstack(level='sex')
        future_gen_dataframe['age'] = 0
        future_gen_dataframe.reset_index(inplace=True)
        future_gen_dataframe.set_index(keys=['age', 'year'], inplace=True)
        
        # On manipule des généartions seuil
        age_gen_df = age_gen_df.unstack(level='sex')
        age_gen_df['age'] = threshold
        age_gen_df.reset_index(inplace=True)
        age_gen_df.set_index(keys=['age', 'year'], inplace=True)

        broken_down = concat([future_gen_dataframe, age_gen_df])
        broken_down = broken_down.unstack(level='age')
        print broken_down.head().to_string()
        
        return broken_down


    def accounting_plot(self, step=5, typ=None):
        """
        Plot the columns of the accounting cohort after creating age classes. This a very sensitive
        script and is not optimized.
        TODO: optimize, ensure that it can plot a lot of things with minimal difficulty.
        """
        if typ is None:
            raise Exception('a columns to plot should be specified')
        age_class_plot = self.create_age_class(step).xs(self._year_min, level = "year").unstack(level="sex")
        age_class_plot = age_class_plot[typ]
        age_class_plot.columns = ['men' , 'women']
           
        age_class_plot.plot(style = '--') ; plt.legend()
        plt.axhline(linewidth=2, color='black')
        plt.show()
    

if __name__ == '__main__':
    pass
