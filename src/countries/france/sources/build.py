# -*- coding:utf-8 -*-
# Created on 20 mars 2013
# This file is part of GA.
# Copyright ©2013 Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see ga/__init__.py for details)

from __future__ import division
from pandas import ExcelFile, HDFStore
from numpy import arange
import os

def build_hdf_fr():
        
    # population
    DIR= '../../data_fr/proj_pop_insee'
        
    store = HDFStore(os.path.join(DIR,'proj_pop.h5'))    
    sex_dict = {0: 'populationH', 1: 'populationF'} 

    for fil in os.listdir(DIR):
        if fil[:7] == 'projpop':
            filename = os.path.join(DIR, fil)
            xls = ExcelFile(filename)
#            sheets = xls.sheet_names
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
    DIR= '../../data_fr'
    profile_file = 'profils.xls'
    store = HDFStore(os.path.join(DIR,'profiles.h5'))
    filename = os.path.join(DIR, profile_file)
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
    print 'DONE'
