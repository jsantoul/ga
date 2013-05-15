# -*- coding:utf-8 -*-
# Copyright © 2012 Clément Schaff, Mahdi Ben Jelloul
'''
Created on 14 mai 2013

@author: Jérôme SANTOUL
'''
from __future__ import division
from pandas import DataFrame, read_csv, concat, ExcelFile, HDFStore
from numpy import NaN, arange, hstack, array
import os
from cohorte import Cohorts

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
        '''
        Constructor
        '''
     
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
        if typ not in self._types:
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
 
 
    
    def create_age_class(self, step = 1):
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
        # Separating Men and Women
        pvm = self.xs(0, level='sex')
        pvf = self.xs(1, level='sex')
        pvm.reset_index(inplace = True)
        pvf.reset_index(inplace = True)
         
        #Transforming the age indexes
        serie = array(pvm.age)
        pvm['age'] = array((serie//step)*step)
        pvf['age'] = array((serie//step)*step)
             
        age_class_pvm = pvm.groupby(['age', 'year']).mean()
        age_class_pvf = pvf.groupby(['age', 'year']).mean()
         
        #Put back the dataframes together
        pieces = [age_class_pvm, age_class_pvf]
        res =  concat(pieces, keys = [0,1], names = ["sex"] )
        res = res.reset_index()
        res = res.set_index(['age', 'sex', 'year'])
        return res            
 
    def compute_ipl(self, typ, net_gov_wealth = None, net_gov_spendings = None):
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
#         age_min = array(list(self.index_sets['age'])).min()
        age_max = array(list(self.index_sets['age'])).max()
         
        past_gen_dataframe = self._pv_aggregate.xs(year_min, level = 'year')
        past_gen_dataframe = past_gen_dataframe.cumsum()
        past_gen_transfer = past_gen_dataframe.get_value((age_max, 1), typ)
 
         
        future_gen_dataframe = self._pv_aggregate.xs(0, level = 'age')
        future_gen_dataframe = future_gen_dataframe.cumsum()
        future_gen_transfer = future_gen_dataframe.get_value((1, year_max), typ)
        print "check future_gen_transfer", future_gen_transfer
        #Note : do not forget to eliminate values counted twice
        ipl = past_gen_transfer + future_gen_transfer + net_gov_wealth - net_gov_spendings - past_gen_dataframe.get_value((0, 0), typ)
        return ipl
     
     
    def compute_gen_imbalance(self, typ, net_gov_wealth = None, net_gov_spendings = None, growth_rate = 0, discount_rate = 0):
        """
        Returns the generationnal imbalance between the newborn of the reference year 
        and the unborn of the next year.
         
        Stratégie : calculer les transferts agrégés des gén futures pour équilibrer la CBI
        N_futur = G_net - W_net - N_passé
        Puis : calculer n_futur = [N_futur]/(mu_1*Pop_t+1)
        avec mu_1 = Sum{[(1+g)/(1+n)]^i*P_i/P_1}
        """
        if net_gov_wealth is None:
            net_gov_wealth = 0
        if net_gov_spendings is None:
            net_gov_spendings = 0
         
        #Computing the net transfer of future generation that even the budget constraint
        year_min = array(list(self.index_sets['year'])).min()
        year_max = array(list(self.index_sets['year'])).max()
#         age_min = array(list(self.index_sets['age'])).min()
        age_max = array(list(self.index_sets['age'])).max()
         
         
        #Calculating the past transfers for both genders then deducting the equilibrium future transfers
         
        past_gen_dataframe = self._pv_aggregate.xs(year_min, level = 'year')
        past_gen_dataframe = past_gen_dataframe.cumsum()
        past_gen_transfer = past_gen_dataframe.get_value((age_max, 1), typ)
         
        future_gen_transfer = net_gov_spendings - net_gov_wealth - past_gen_transfer
        print "check future_gen_transfer", future_gen_transfer
          
        #Reorganising the population data
        population_unborn_ma = self.get_value((0,0, year_min+1), 'pop')
        population_unborn_fe = self.get_value((0,1,year_min+1), 'pop')
        population_unborn = population_unborn_ma + population_unborn_fe
         
        population_dataframe = self.filter_value(age = [0], year = range(year_min+1, year_max+1), typ='pop')
        population_dataframe.gen_actualization(growth_rate, discount_rate)
        population_dataframe = population_dataframe.unstack(level='sex')
        del population_dataframe[('actualization', 1)]
        population_dataframe['unborn'] = population_unborn
        population_dataframe['mixed'] = population_dataframe[('pop', 0)] + population_dataframe[('pop', 1)]
        print population_dataframe.head()
        population_dataframe[('actualization', 0)] *= population_dataframe['mixed']/population_dataframe['unborn']
 
#         print "check 1"
#         print tmp['actualization']
        print "check column combination"
        print population_dataframe[("actualization", 0)]
         
        #Computing the adjustment coefficient of the population mu_1
        population_dataframe = population_dataframe.cumsum()        
        mu_1 = population_dataframe.get_value((0,year_max), ('actualization', 0))
        print "mu_1 = ", mu_1
          
        #Computing the final imbalance coefficients
        population_unborn = population_unborn_ma + population_unborn_fe
        percapita_future_gen_transfer = n_1 = future_gen_transfer/(mu_1*population_unborn)
        actual_gen_transfer = n_0 = (self._pv_percapita.get_value((0, 0, year_min), typ) + 
                               self._pv_percapita.get_value((0, 1, year_min), typ))
        print "n_0", n_0 
        imbalance = n_1 - n_0
        imbalance_ratio = n_1/n_0
        coefficients = [n_1, imbalance, imbalance_ratio]
        return coefficients        