# -*- coding:utf-8 -*-
# Copyright © 2012 Clément Schaff, Mahdi Ben Jelloul
'''
Created on May 22, 2012

@author: Clément Schaff, Mahdi Ben Jelloul
'''

from __future__ import division
from pandas import DataFrame, read_csv, Series, ExcelFile, HDFStore
from numpy import NaN, arange, zeros, hstack, array
import os

class Cohorte(DataFrame):
    '''
    Stores data for some cohortes. Data should be a data frame with multindexing and at most one 
    column dimension. 
    Default columns are 'year', set col_names if different.
    '''
    def __init__(self, data=None, index=None, columns=None, 
                 dtype=None, copy=False):
        super(Cohorte, self).__init__(data, index, columns , dtype, copy)

        if data is not None:
            if set(['age', 'sex', 'year']) != set(self.index.names):
                raise Exception('Need  age, sex and year indexes')
    
            self.index_sets = {}
            self._begin = None
            self._end   = None
            self._agemin = None
            self._agemax = None
            self._agg = None
            self._nb_type = 0
            self._types = []
            self.post_init()

        
    def set_population_from_csv(self, datafile):
        '''
        Sets population from csv file
        '''
        data = read_csv(datafile, index_col = [0,1])
        stacked = data.stack()
        stacked.index.names[2] = 'age'
        stacked = stacked.reorder_levels(['sex', 'year', 'age']).sortlevel()
        self.__init__(data = stacked, columns = ['pop'])

    def post_init(self):
        temp = zip(*self.index)
        name = self.index.names 
        for t, n in zip(temp, name):
            self.index_sets[n] = set(t)

        self._agemin = min(self.index_sets['age'])
        self._agemax = max(self.index_sets['age'])


    def totaux(self, by, column, pivot = False):
        if pivot:
            # should return a square DataFrame where the last level is used as columns
            if len(by) ==2 and isinstance(by, list):
                a = self[column]
                a = a.groupby(level = by).sum()
                return a.unstack()
        return self[column].groupby(level = by).sum()
            

    def new_type(self, name ):
        '''
        creates a new empty column
        '''
        if name not in self._types:
            self[name] = NaN
            self._nb_type += 1
            self._types.append(name)
        else:
            raise Exception('%s already exists'% name)

    def fill(self, df, year = None):
        '''
        takes an age profile in 'vect' and fill column 'column' with it for each year, given a sex
        '''
        if year is None:
            for yr in sorted(self.index_sets['year']):
                self.fill(df, year = yr)
        else:
            yr = year
            df1 = DataFrame(df)
            for col_name, column in df1.iteritems():
                if col_name not in self._types:
                    self.new_type(col_name)
                column = column.reset_index()
                column['year'] = yr
                column = column.set_index(['age','sex','year'])
                self.combine_first(column)

            
    
    def fill_old(self, vect, column, sex, year = None):
        '''
        takes an age profile in 'vect' and fill column 'column' with it for each year, given a sex
        '''
        if year is None:
            for yr in sorted(self.index_sets['year']):
                self.fill(vect, column, sex, year = yr)
        else:
            yr = year

            if column not in self.columns:
                self[column] = NaN
            
            v = DataFrame({column: vect})
            v['age'] = v.index
            v['year'] = yr
            v['sex']  = sex 
            v = v.set_index(['age','sex','year'])
            
            new_data = self.combine_first(v)
            self = Cohorte(new_data)
    
        
    def add_agg(self, agg):
        '''
        stores aggregates in Cohorte
        '''
        self._agg = agg*1e9

    def to_percap(self):
        '''
        rescale profiles to per capita amounts
        '''
        try: 
            g = self._growth_rate
        except e:
            raise "growth rate is not set ", e 
        
        
        try: 
            r = self._discount_rate
        except e:
            print "discount rate is not set ", e 
        
        
        for typ in range(1, self._nb_type+1):
            var = 'typ%i'%typ
            self['tmp'] = self[var]*self['pop']
            sums = self.totaux('year', 'tmp')
            
            unities = self._agg['%i' %typ]/sums
            # warning: creates NaN from 2071 to 2200 because agg unknown
            
            grouped = self.groupby(level = ['sex', 'age'])[var]
            self[var] = grouped.transform(lambda x: x*unities.values)
        
            yr_min = array(list(self.index_sets['year'])).min()
            for yr in range(yr_min,2201):   # TODO 
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

    def pv_ga(self, typ):
        
        tmp = self['dsct']*self[typ]*self['pop']*self['grth']
        tmp = tmp.unstack(level = 'year')
        
        M = tmp.ix[:,0]
        F = tmp.ix[:,1]
        
        pvm = M.copy()
        pvf = F.copy()

        yr_min = array(list(self.index_sets['year'])).min()
        yr_max = array(list(self.index_sets['year'])).max()
        for yr in arange(yr_min, yr_max)[::-1]:
            print yr
            pvm[yr] += hstack([pvm[yr+1].values[1:], 0])
            pvf[yr] += hstack([pvf[yr+1].values[1:], 0])
        
        # print pvm[yr_max].head()
        return pvm, pvf
        
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
    profiles = Cohorte()
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


def build_hdf_fr():
        
    # population
    DIR= '../data_fr/proj_pop_insee'
        
    store = HDFStore(os.path.join(DIR,'proj_pop.h5'))    
    sex_dict = {0: 'populationH', 1: 'populationF'} 

    for file in os.listdir(DIR):
        
        if file[:7] == 'projpop':
                    
            filename = os.path.join(DIR, file)
            xls = ExcelFile(filename)
            sheets = xls.sheet_names
            pop = None
                    
            for sex, sheet in sex_dict.items():
                df = xls.parse(sheet, skiprows = [0,1,2,3],
                           na_values=['NA'], index_col = 0)
                df = df.reset_index()
                del df[df.columns[0]]
                for i in arange(109,114): df = df.drop([i])
                # Rename index
                df.index.names = ['age']    
                df.columns = df.columns.astype('int32')
                df = df.unstack()
                df.index.names[0] = 'year'
                df = df.reset_index()
                df['sex'] = sex
                if pop is None:
                    pop = df
                else:
                    pop = pop.append(df)
               
            pop['pop'] = pop[0]
            del pop[0]
            
            s = pop[pop['age']>=100] 
            s = s.set_index(['age', 'sex', 'year'])
            s = s.sum(axis=0, level = ['sex', 'year'])
            
            pop = pop.set_index(['age', 'sex', 'year'])

            for t in s.index:
                pop.set_value( (100,) + t, 'pop', s.ix[t]['pop'])

            for a in range(101,109):
                pop = pop.drop(a, axis =0, level="age")
            print file[:-4]
            store[file[:-4]] = pop

    store.close()
    
    # profiles
    DIR= '../data_fr'
    file = 'profils.xls'
    store = HDFStore(os.path.join(DIR,'profiles.h5'))
    filename = os.path.join(DIR, file)
    xls = ExcelFile(filename)
    sheets = xls.sheet_names
    profiles = None
    for sheet in sheets:
        df = xls.parse(sheet)
        df['age'] = df['age'].astype(int)
        df['sex'] = df['sex'].astype(int)
        df['year'] = 1996
        df = df.set_index(['age', 'sex','year']) 
        
        
        if profiles is None:
            profiles = df
        else:
            profiles = profiles.merge(df,right_index=True, left_index=True)
        
    store['profiles'] = profiles
    

    
    store.close()
    
    
    
def test_fr():
        
#    
#    
#    
    ############################################################
    ## load data
    ############################################################
    
    # load population data

    DIR= '../data_fr/proj_pop_insee'
    store = HDFStore(os.path.join(DIR,'propj_pop.h5'))
    pop = store['projpop0760_FECcentESPcentMIGcent']
    store.close()
    profiles = Cohorte(data = pop, columns = ['pop'])
    
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
    pvm, pvf =  profiles.pv_ga(var)
    y = 2060
    a = 4
    print (profiles.ix[a,1,y][var]*profiles.ix[a,1,y]['pop']*profiles.ix[a,1,y]['grth']*profiles.ix[a,1,y]['dsct'])
    print pvf[2060].head()
    print pvf.index
    print pvm[2060].head()

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
    build_hdf_fr()