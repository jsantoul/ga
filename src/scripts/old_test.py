# -*- coding:utf-8 -*-
# Created on 25 avr. 2013
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © #2013 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)


from src.lib.cohorte import Cohorts
from pandas import HDFStore, read_csv
import os

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
