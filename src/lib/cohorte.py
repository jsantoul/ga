# -*- coding:utf-8 -*-
# Copyright © 2012 Clément Schaff, Mahdi Ben Jelloul
'''
Created on May 22, 2012

@author: Clément Schaff, Mahdi Ben Jelloul
'''

from __future__ import division
from pandas import DataFrame, read_csv, concat, ExcelFile, HDFStore
from numpy import NaN, arange, hstack, array
import os

class Cohorts(DataFrame):
    """
    Stores data for some cohortes. Data should be a data frame with multindexing and at most one 
    column dimension. 
    Default columns are 'year', set col_names if different.
    """
    def __init__(self, data=None, index=None, columns=None, 
                 dtype=None, copy=False):
        super(Cohorts, self).__init__(data, index, columns , dtype, copy)

        if data is not None:
            if set(['age', 'sex', 'year']) != set(self.index.names):
                raise Exception('Need  age, sex and year indexes')
    
            self.index_sets = dict()
            self._begin = None
            self._end   = None
            self._agemin = None
            self._agemax = None
            self._agg = None
            self._nb_type = 0
            self._types = list()
            self._types_years = dict()   # TODO: merge this dict with the previous list
            
            self.post_init()

    def post_init(self):
        """
        Post initialization, computes index_sets, _agemin, _agemax attributes
        """
        temp = zip(*self.index)
        name = self.index.names 
        for t, n in zip(temp, name):
            self.index_sets[n] = set(t)

        self._agemin = min(self.index_sets['age'])
        self._agemax = max(self.index_sets['age'])


    def totaux(self, by, column, pivot = False):
        """
        Compute a pivot table 
        
        Parameters
        ----------
        by : str
             Variable which values are kept constant in each group (by variable)
        column : str
                 Variable which is summed by group 
        pivot : boolean, default False
                if True returns a pivot_table
        
        Returns
        -------
        df : a Dataframe
        
        """
        if pivot:
            # should return a square DataFrame where the last level is used as columns
            if len(by) ==2 and isinstance(by, list):
                a = self[column]
                a = a.groupby(level = by).sum()
                return a.unstack()
        df = DataFrame({column : self[column].groupby(level = by).sum()})
        return df 
            

    def new_type(self, name ):
        """
        Creates a new empty column
        
        Parameters
        ----------
        
        name : str
               Name of the new empty column
        """
        if name not in self._types:
            self[name] = NaN
            self._nb_type += 1
            self._types.append(name)
        else:
            raise Exception('%s already exists'% name)

    def fill_old(self, df, year = None):
        """
        Takes an age, sex profile (per capita transfers) in df 
        to fill year 'year' or all years if year is None
        """
        if isinstance(df, DataFrame):
            df1  = df 
        else:
            df1 = DataFrame(df)

        for col_name in df1.columns:
            if col_name not in self._types:
                self.new_type(col_name)

        if year is None:
            for yr in sorted(self.index_sets['year']):
                self.fill(df, year = yr)
        else:
            yr = year
            if isinstance(df, DataFrame):
                df1  = df 
            else:
                df1 = DataFrame(df)
            
            for col_name, column in df1.iteritems():
                column = column.reset_index()
                column['year'] = yr
                column = column.set_index(['age','sex','year'])
                self.update(column)
                
    def fill(self, df, year = None):
        """
        Takes age, sex profile (per capita transfers) found in df
        to fill year 'year' or all years if year is None
        
        Parameters
        ----------
        
        df : DataFrame
             a dataframe containing the profiles
        
        year : int, default None
               if None fill all the years else only the given year
        
        """        
        if not isinstance(df, DataFrame): 
            df = DataFrame(df)

        for col_name in df.columns:
            if col_name not in self._types:
                self.new_type(col_name)
                typ = col_name
                tmp = df[typ]
                tmp = tmp.unstack(level="year")
                tmp = tmp.dropna(axis=1, how="all")
                self._types_years[typ] = tmp.columns
                
            else:
                raise Exception("column already exists")
        
        if year is None:
            df_insert = df.reset_index(level='year', drop=True)
            years = sorted(self.index_sets['year'])
            list_df = [df_insert] * len(years)
            df_tot = concat(list_df, keys = years, names =['year'])
            df_tot = df_tot.reorder_levels(['age','sex','year'], axis=0)
            
        else:
            yr = year
            df_tot = None
            df_insert = df.reset_index()
            df_insert['year'] = yr
            if df_tot is None:
                df_tot = df_insert
            else:
                df_tot.append(df_insert, ignore_index=True)
                df_tot = df_tot.set_index(['age','sex','year'])

        self.update(df_tot)
        
    def add_agg(self, agg):
        '''
        Stores aggregates in Cohorte  TODO: REMOVEME DEPRECATED
        '''
        self._agg = agg*1e9

    def to_percap(self):
        '''
        Re-scale profiles to per capita amounts of transfers (after projection if it occurred)
        using aggregates
        '''
        
        if self._agg is None:
            raise Exception('cohorte: exiting to_perrcap because self._agg is None')
            return
        
        for typ in range(1, self._nb_type+1):
            var = 'typ%i'%typ
            self['tmp'] = self[var]*self['pop']
            sums = self.totaux(by = 'year', column = 'tmp')
            
            unities = self._agg['%i' %typ]/sums
            # warning: creates NaN from 2071 to 2200 because agg unknown
            
            grouped = self.groupby(level = ['sex', 'age'])[var]
            self[var] = grouped.transform(lambda x: x*unities.values)
        
            yr_min = min(self.index_sets['year'])
            for yr in range(yr_min,2201):   # TODO check yr -1 ?? 
                a = self.xs(yr-1, level='year', axis=0)[var]
                self.xs(yr, level='year', axis=0)[var] = a

    
    def gen_grth(self, g):
        self._growth_rate = g
        self['grth'] = NaN
        grouped = self.groupby(level = ['sex', 'age'])['grth']
        nb_years = len(self.index_sets['year'])
        self['grth'] = grouped.transform(lambda x: (1+g)**(arange(nb_years)))

    def gen_dsct(self, r):
        self._discount_rate = r 
        self['dsct'] = NaN
        grouped = self.groupby(level = ['sex', 'age'])['dsct']
        nb_years = len(self.index_sets['year'])
        self['dsct'] = grouped.transform(lambda x: 1/((1+r)**arange(nb_years)))
    
    def gen_actualization(self, arg1 , arg2):
        """
        A method to generate a column of actualization coefficients to be used with profiles data
        
        Parameters
        ----------
        Arg1 : any growth rate 
        Arg2 : any discount rate (such as interest rate)
        """
        self['actualization']= NaN
        grouped = self.groupby(level = ['sex', 'age'])['actualization']
        nb_years = len(self.index_sets['year'])
        self['actualization'] = grouped.transform(lambda x: ((1+ arg1)/(1+ arg2)**arange(nb_years)))        


    def proj_tax(self, rate = None , discount_rate = None , typ = None, method = None):
        """
        Projects taxes either per_capita or aggregate at the constant growth_rate rate
        
        Parameters
        ----------        
        rate : float,
            Growth rate of the economy
        discount_rate : float
        typ : the type of data which has to be expanded.
            The cohort should have one column for the population and at least one other column (the profile)
            which will be expanded
        method : str
            the method used for the projection 
            the name has to be either 'per_capita' or 'aggregate'
        """
        
        if rate is None:
            raise Exception('no growth_rate provided')
        if discount_rate is None:
            self.proj_tax(rate , 0 , typ, method)
            return
        if method is None:
            raise Exception('a method should be specified')
        if typ is None:
            for typ in self._types:
                self.proj_tax(rate , discount_rate , typ, method)
            return
        if typ not in self.columns:
            raise Exception('this is not a column of cohort')
        else:
            self.gen_grth(rate)
            if method == "per_capita":
                self[typ] = self[typ]*self['grth']
                
            if method == "aggregate":
                typ_years = self._types_years[typ]
                last_typ_year = max(typ_years)         
                last_typ_pop = self.xs(last_typ_year, level='year', axis=0)  
                years = self.index_sets['year']
                last_year = max(years)
                proj_years = range(last_typ_year, last_year+1)
                list_pop_df = [last_typ_pop] * len(proj_years)
                frozen_pop = concat(list_pop_df, keys = years, names =['year'])
                frozen_pop = frozen_pop.reorder_levels(['age','sex','year'], axis=0)
                
                
                self[typ] = self[typ]*self['grth']*frozen_pop["pop"]/self["pop"]
                # print self
            else:
                NotImplementedError


                
    def aggregate_generation_present_value(self, typ):
        """
        Computes the present value of one column for the whole generation
        
        Parameters
        ----------
        typ : str
              Name of the column of the per capita profile of tax or transfer
        """
        
        # TODO: test if self['dsct'] exists
        
        tmp = self['dsct']*self[typ]*self['pop']
        tmp = tmp.unstack(level = 'year')  # untack year indices to columns
        # TODO use a loop
#        for sex in self.index_sets[sex]:
        
        pvm = tmp.xs(0, level='sex')
        pvf = tmp.xs(1, level='sex') #Assuming 1 is the index for females resp. 0 is male.
        
        yr_min = array(list(self.index_sets['year'])).min()
        yr_max = array(list(self.index_sets['year'])).max()
        
        for yr in arange(yr_min, yr_max)[::-1]:
            pvm[yr] += hstack( [ pvm[yr+1].values[1:], 0]  )
            pvf[yr] += hstack( [ pvf[yr+1].values[1:], 0]  )
            
        pieces = [pvm, pvf]
        res =  concat(pieces, keys = [0,1], names = ["sex"] )
        res = res.stack()
        res = res.reset_index()
        res = res.set_index(['age', 'sex', 'year'])
        res.columns = [typ]
        return res


    def per_capita_generation_present_value(self, typ):
        """
        Returns present net value for typ per capita
        
        Parameters
        ----------
        typ : str
              Column name
        
        """

        if typ not in self._types:
            raise Exception('cohort: variable %s is not in self._types' %typ)
        pv_gen = self.pv_ga(typ) 
        pop = DataFrame({'pop' : self['pop']})
        return DataFrame(pv_gen[typ]/pop['pop'])

    def population_project(self, year_length = None, method = None):
        """
        Continuation of population to provide convergent present values
        
        Parameters
        ----------
        year_length : int, default None
                      Duration to continue the population projection
        method : str, default None
                 A value that must be 'stable' or 'TODO: add other protocols' is required.  
        """
#        For the other projection method, I see exponential growth at constant rate
        if 'pop' not in self.columns:
            raise Exception('pop is not a column of cohort')
        if year_length is None:
            raise Exception('a duration in years should be provided')
        if method is None:
            raise Exception('a method should be specified')
        years = self.index_sets['year'] 
        first_year = min(years)
        last_year = max(years)
        
        if ( first_year + year_length ) > last_year:
            new_last_year = first_year + year_length 
        else:
            return

        if method == 'stable':
            last_pop = self.xs(last_year, level='year', axis=0)
            pop = DataFrame(self['pop'])
            years = range(last_year+1,new_last_year+1)
            # TODO: modify here to add population growth rate
            list_df = [last_pop] * len(years)

            pop = concat(list_df, keys = years, names =['year'])
            pop = pop.reorder_levels(['age','sex','year'], axis=0)
            combined = self.combine_first(pop)
            self.__init__(data = combined, columns = ['pop'])
            

        if method == 'exp_growth':
#             TODO : finish this projection method. Add an argument, add checkpoint if growth rate is None
#             find efficient way to do the growth operation
            last_pop = self.xs(last_year, level='year', axis=0)
            pop = DataFrame(self['pop'])
            years = range(last_year+1,new_last_year+1)
#             self['dsct'] = grouped.transform(lambda x: 1/((1+r)**arange(nb_years)))
            list_df = [last_pop] * len(years) 

            pop = concat(list_df, keys = years, names =['year'])
            pop = pop.reorder_levels(['age','sex','year'], axis=0)
            combined = self.combine_first(pop)
            self.__init__(data = combined, columns = ['pop'])
            pass

    
    def set_population_from_csv(self, datafile):
        '''
        Sets population from csv file
        '''
        data = read_csv(datafile, index_col = [0,1])
        stacked = data.stack()
        stacked.index.names[2] = 'age'
        stacked = stacked.reorder_levels(['sex', 'year', 'age']).sortlevel()
        self.__init__(data = stacked, columns = ['pop'])


    def get_unknown_years(self, typ):
        """
        
        """
        cohorts_years = range(self._first_year, self._last_year+1)
        
        profile = self._profiles_years[typ]
        
        

if __name__ == '__main__':
    pass