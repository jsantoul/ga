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
        Takes an age, sex profile (per capita transfers) 
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

    def proj_tax(self, rate = None, typ = None, method = 'per_capita'):
        """
        Projects taxes either per_capita or globally at the constant growth_rate rate
        
        Parameters
        ----------
        
        rate : Growth rate of the economy
        
        typ : the type of data to expand
            this is the name of the column the method will have to expand

        method : the method used for the projection 
            the name has to be either 'per_capita' or 'aggregate'
        
        """
        
        """
        Questions about this method :
        -> When is this method supposed to be used ? Before or after pop projection ?
        
        -> What kind of info the cohort must contain to be used with the method ?
        The profile dataframe the tax or should the tax profile be specified in the arguments ?
        """  
        if typ not in self.columns:
            raise Exception('this %s is not a column of cohort') %(typ)
        if method is None:
            raise Exception('a method should be specified')
        
        if method == 'per_capita':
#             TODO: create a column 'growth' values are : (1+g)*elapsed_year. 
#             Fill the 'typ' column with the value at the initial year (ask about behaviour of this)
#             see later to fix if given value is not initial year
#             Finally multiply the column 'typ' with the column 'growth'
            pass
#             last_pop = self.xs(last_year, level='year', axis=0)
#             pop = DataFrame(self['pop'])
#             years = range(last_year+1,new_last_year+1)
#             list_df = [last_pop] * len(years)
#  
#             pop = concat(list_df, keys = years, names =['year'])
#             pop = pop.reorder_levels(['age','sex','year'], axis=0)
#             combined = self.combine_first(pop)
#             self.__init__(data = combined, columns = ['pop'])
        if rate is None:
            raise Exception('no rate provided using growth_rate')
        
        if typ is None:
            for typ in self._types:
                self.proj_tax(rate, typ, method)
        else:
            if method == 'per_capita':
                self[typ] = self[typ]*self['grth']
            else:
                NotImplementedError
                
    def pv_ga(self, typ):
        """
        Computes the present value of one column for the whole generation
        
        Parameters
        ----------
        typ : str
              Name of the column
        """    
        tmp = self['dsct']*self[typ]*self['pop']
        tmp = tmp.unstack(level = 'year')
        
        # TODO use a loop
#        for sex in self.index_sets[sex]:
        
        pvm = tmp.xs(0, level='sex')
        pvf = tmp.xs(0, level='sex')
        
        yr_min = array(list(self.index_sets['year'])).min()
        yr_max = array(list(self.index_sets['year'])).max()
        
        for yr in arange(yr_min, yr_max)[::-1]:
            pvm[yr] += hstack([pvm[yr+1].values[1:], 0])
            pvf[yr] += hstack([pvf[yr+1].values[1:], 0])
            
        pieces = [pvm, pvf]
        res =  concat(pieces, keys = [0,1], names = ["sex"] )
        res = res.stack()
        res = res.reset_index()
        res = res.set_index(['age', 'sex', 'year'])
        res.columns = [typ]
        return res


    def pv_percap(self, typ):
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
                 A value that must be 'stable' or is required.  
        """
        
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

    
    def set_population_from_csv(self, datafile):
        '''
        Sets population from csv file
        '''
        data = read_csv(datafile, index_col = [0,1])
        stacked = data.stack()
        stacked.index.names[2] = 'age'
        stacked = stacked.reorder_levels(['sex', 'year', 'age']).sortlevel()
        self.__init__(data = stacked, columns = ['pop'])


        
def test_us():    
    ############################################"
    ## set simulation parameters
    ############################################"
    
    # set path to data
    DIR= 'data_us'
    
    # number of types (tax or transfer)
    nb_type = 17
    
    # define aggregate scenario
    agg_scenar = 'aggmed' # can be in ('agglow', 'aggmed', 'agghigh')
    
    # define population scenario
    pop_scenar = 'popmed' # can be in ('popmed', 'pophigh', 'poplow')
    
    ############################################################
    ## load data
    ############################################################
    
    # load population data
    datafile = os.path.join(DIR, pop_scenar +'.csv')
    profiles = Cohorts()
    profiles.set_population_from_csv(datafile)
    
    
    # load relative profiles and fill Cohorte
    datafile = os.path.join(DIR, 'rp.csv')
    data = read_csv(datafile, index_col = [0,1])
    for i in range(1, nb_type + 1):
        var = 'typ%i'%i
        profiles.new_type(var)
        for sex in profiles.index_sets['sex']:
            profiles.fill(data.ix[sex, i], var, sex)
    
    # load aggregate data (year x types)
    datafile = os.path.join(DIR, agg_scenar+'.csv')
    agg = read_csv(datafile, index_col = 0)
    profiles.add_agg(agg)    
    
    # set r and g
    r = 0.060
    g = 0.012
    
    # create discount factor and growth rate
    
    # print out.to_string()
    # print coh.totaux(['year', 'age'], pivot = True).to_string()
    
    profiles.gen_grth(g)
    profiles.gen_dsct(r)
    profiles.to_percap()
    
    # profiles['typ1'].unstack(level = 'year').to_csv('out.csv')
    #print profiles['typ1'].unstack(level = 'year').head().to_string()
    
    print profiles.pv_ga('typ1')


    
    
def test_fr():
        
#    
#    
#    
    ############################################################
    ## load data
    ############################################################
    
    # load population data

    DIR= '../data_fr/proj_pop_insee'
    store = HDFStore(os.path.join(DIR,'proj_pop.h5'))
    pop = store['projpop0760_FECcentESPcentMIGcent']
    store.close()
    profiles = Cohorts(data = pop, columns = ['pop'])
    
    DIR= '../data_fr'
    store = HDFStore(os.path.join(DIR,'profiles.h5'))
    vars = store['profiles']
    store.close()
    profiles.fill(vars)
    # set r and g
    r = 0.060
    g = 0.012
    
    # create discount factor and growth rate
    
    # print out.to_string()
    # print coh.totaux(['year', 'age'], pivot = True).to_string()
    
    profiles.gen_grth(g)
    profiles.gen_dsct(r)
#    profiles.to_percap()

#    profiles.to_csv('out.csv')
    # profiles['typ1'].unstack(level = 'year').to_csv('out.csv')
    #print profiles['typ1'].unstack(level = 'year').head().to_string()
    #print profiles['grth']
    #print profiles['tva']
    var = 'educ'
    pv_g =  profiles.pv_ga(var)
    y = 2060
    a = 4
#    print (profiles.ix[a,1,y][var]*profiles.ix[a,1,y]['pop']*profiles.ix[a,1,y]['grth']*profiles.ix[a,1,y]['dsct'])
#    print pvf[2060].head()
#    print pvf.index
#    print pv_g[2060].head()
    p = profiles.pv_percap(var)
    print p.index.names
    print p.ix[:,0,2007].to_string()
    print p
    
#TODO : method for filling years by type
#       method for extending population projection (complete table for 1996-2007)
#       GUI interface       
#       Burden diagnostics
#         - 
#       Reform mode
#       Immigration
#       Burden decomposition
# 

# GUI profil par age pour une année donnée
#     profil des prel et transferts par cohorte  (per cap/actualisée et agrégée)
#     budget de l'etat
#     parametrisation des projections  population pyraide des ages
# 
if __name__ == '__main__':
    pass