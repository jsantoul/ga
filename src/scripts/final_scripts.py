# -*- coding:utf-8 -*-
# Created on 7 août 2013
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © #2013 Jérôme SANTOUL
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)


"""
Note : ces scripts sont ici pour générer des documents excels utilisables facilement pour créer des graphes
lisibles et clairs.

"""

from __future__ import division
import os
from src.lib.simulation import Simulation
from src.lib.cohorts.accounting_cohorts import AccountingCohorts
from pandas import read_csv, HDFStore, concat, ExcelFile, DataFrame, MultiIndex
from numpy import array, hstack, arange, NaN
import matplotlib.pyplot as plt
from src import SRC_PATH
from src.lib.cohorts.data_cohorts import DataCohorts
import gc


country = "france"    
population_filename = os.path.join(SRC_PATH, 'countries', country, 'sources',
                                           'data_fr', 'proj_pop_insee', 'proj_pop.h5')
profiles_filename = os.path.join(SRC_PATH, 'countries', country, 'sources',
                                         'data_fr','profiles.h5')
CBonnet_results = os.path.join(SRC_PATH, 'countries', country, 'sources',
                                           'Carole_Bonnet', 'theoretical_results.xls')
pop_insee = os.path.join(SRC_PATH, 'countries', country, 'sources',
                                           'Carole_Bonnet', 'pop_1996_2006.xls')
xls = "C:/Users/Utilisateur/Documents/GitHub/ga/src/countries/france/sources/Output_folder/"


#===============================================================================
# Cette partie du programme initialise la simulation pour effectuer les calculs. 
# Des options plus avancées
# sont contenues à l'intérieur des fonctions ci-après 
#===============================================================================

def generate_simulation():
    
    print 'Entering the comparison function'
    
    simulation = Simulation()
    population_scenario = "projpop0760_FECbasESPbasMIGbas"
    population_scenario_alt = "projpop0760_FECbasESPbasMIGbas"
    simulation.load_population(population_filename, population_scenario)
    simulation.load_population(population_filename, population_scenario_alt, default=False)
    
    # Adding missing population data between 1996 and 2007 :
    store_pop = HDFStore(os.path.join(SRC_PATH, 'countries', country, 'sources',
                                           'Carole_Bonnet', 'pop_1996_2006.h5'))
    corrected_pop = store_pop['population']
    truncated_pop = concat([corrected_pop.iloc[0:101, :], corrected_pop.iloc[1111:1212,:]])
    
    simulation.population = concat([corrected_pop, simulation.population])
    simulation.population_alt = concat([corrected_pop, simulation.population_alt])
    
    #Loading profiles :
    simulation.load_profiles(profiles_filename)
    
    year_length = 250
    simulation.set_year_length(nb_year=year_length)
    """
    Default Hypothesis set : 
    actualization rate r = 3%
    growth rate g = 1%
    net_gov_wealth = -3217.7e+09 (unit : Franc Français (FRF) of 1996)
    non ventilated government spendings in 1996 : 1094e+09 FRF
    """

    r = 0.03
    g = 0.01
    n = 0.00
    pi = 0.01
    net_gov_wealth = -3217.7e+09
    year_gov_spending = (1094)*1e+09
    taxes_list = ['tva', 'tipp', 'cot', 'irpp', 'impot', 'property']
    payments_list = ['chomage', 'retraite', 'revsoc', 'maladie', 'educ']
    
    simulation.set_population_projection(year_length=simulation.year_length, method="exp_growth")
    simulation.set_tax_projection(method="desynchronized", rate=g, inflation_rate=pi, typ=taxes_list, payments_list=payments_list)
    simulation.set_growth_rate(g)
    simulation.set_discount_rate(r) 
    simulation.set_population_growth_rate(n)
    simulation.create_cohorts()
    simulation.set_gov_wealth(net_gov_wealth)
    simulation.set_gov_spendings(year_gov_spending, default=True, compute=True)


    simulation.cohorts.compute_net_transfers(name = 'net_transfers', taxes_list = taxes_list, payments_list = payments_list)
    simulation.create_present_values('net_transfers', default=True)
    
    """
    Alternate Hypothesis set : 
    actualization rate r = 3%
    growth rate g = 1%
    net_gov_wealth = -3217.7e+09 (unit : Franc Français (FRF) of 1996)
    non ventilated government spendings in 1996 : 1094e+09 FRF
    """

    r_alt = 0.03
    g_alt = 0.01
    n_alt = 0.00
    pi_alt = 0.01
    net_gov_wealth_alt = -3217.7e+09
    year_gov_spending_alt = (1094)*1e+09

    simulation.set_tax_projection(method="desynchronized", rate=g_alt, inflation_rate=pi_alt, typ=taxes_list, payments_list=payments_list)
    simulation.set_growth_rate(g_alt, default=False)
    simulation.set_discount_rate(r_alt, default=False) 
    simulation.set_population_growth_rate(n_alt, default=False)
    simulation.create_cohorts(default=False)
    simulation.set_gov_wealth(net_gov_wealth_alt, default=False)
    simulation.set_gov_spendings(year_gov_spending_alt, default=False, compute=True)
    
#     simulation.cohorts_alt.loc[[x>=2075 for x in simulation.cohorts_alt.index.get_level_values(2)], 'cot'] *= (1+0.1)
    simulation.cohorts_alt.compute_net_transfers(name = 'net_transfers', taxes_list = taxes_list, payments_list = payments_list)
    simulation.create_present_values('net_transfers', default=False)
    
    
    return simulation



#===============================================================================
# Fonctions avancées pour produire les excels
#===============================================================================

simulation = generate_simulation()

def produce_gen_accounts(year=1996):
    
    #Creating age classes
    cohorts_age_class = simulation.create_age_class(typ = 'net_transfers', step = 5)
    cohorts_age_class._types = [u'tva', u'tipp', u'cot', u'irpp', u'impot', u'property', u'chomage', u'retraite', u'revsoc', u'maladie', u'educ', u'net_transfers']
    age_class_pv_fe = cohorts_age_class.xs((1, year), level = ['sex', 'year'])
    age_class_pv_ma = cohorts_age_class.xs((0, year), level = ['sex', 'year'])
    
    cohorts_age_class_alt = simulation.create_age_class(typ = 'net_transfers', step = 5, default=False)
    cohorts_age_class_alt._types = [u'tva', u'tipp', u'cot', u'irpp', u'impot', u'property', u'chomage', u'retraite', u'revsoc', u'maladie', u'educ', u'net_transfers']
    age_class_pv_fe_alt = cohorts_age_class_alt.xs((1, year), level = ['sex', 'year'])
    age_class_pv_ma_alt = cohorts_age_class_alt.xs((0, year), level = ['sex', 'year'])
    
    print "AGE CLASS PV"
    print age_class_pv_ma.head()
    print age_class_pv_ma_alt.head()
    
    age_class_pv = concat([age_class_pv_ma, age_class_pv_fe, age_class_pv_ma_alt, age_class_pv_fe_alt], 
                          axis=1, ignore_index=True)
    age_class_pv.columns = ['compte_ma', 'pop_ma', 'compte_fe', 'pop_fe', 
                            'compte_ma_alt', 'pop_ma_alt', 'compte_fe_alt', 'pop_fe_alt']
    print age_class_pv.head()
    
    age_class_pv.to_excel(xls+"gen_accounts_cot.xlsx", 'gen_accounts')
    

def produce_percap_transfert_flux(simulation=simulation, year_list = range(1996, 2050, 10), year_min=1996):
    
    print 'producing flux of transfers per capita'
    tmp = simulation.cohorts.loc[:, ['net_transfers', 'pop', 'dsct']]
    tmp['running_transfers'] = tmp['net_transfers']
    tmp['net_transfers'] *= tmp['dsct']

    tmp_2 = simulation.cohorts_alt.loc[:, ['net_transfers', 'pop', 'dsct']]
    tmp_2['running_transfers'] = tmp_2['net_transfers']
    tmp_2['net_transfers'] *= tmp_2['dsct']
    

    for year in year_list:
        flux_df = AccountingCohorts(tmp).extract_generation(year=year, typ='net_transfers', age=0)
        flux_df = flux_df.xs(0, level='sex')
        flux_df.columns = [year]
        print year

        flux_df_alt = AccountingCohorts(tmp_2).extract_generation(year=year, typ='net_transfers', age=0)
        flux_df_alt = flux_df_alt.xs(0, level='sex')
        flux_df_alt.columns = [str(year)+'_alt']
        
        flux_df = concat([flux_df, flux_df_alt], axis=1)#, ignore_index=True)
        flux_df[year] *= ((1+simulation.discount_rate)/(1+simulation.growth_rate))**(year - year_min)
        flux_df[str(year)+'_alt'] *= ((1+simulation.discount_rate_alt)/(1+simulation.growth_rate_alt))**(year - year_min)
        print flux_df.head()
    
        flux_df.to_excel(str(xls)+str(year)+'_ESP.xlsx', 'flux')
        gc.collect()
        
def produce_agg_transfert_flux(simulation=simulation, year_list = range(1996, 2050, 10), year_min=1996):
    
    tmp = simulation.cohorts.loc[:, ['net_transfers', 'pop', 'dsct']]
    tmp['running_transfers'] = tmp['net_transfers']
    tmp['net_transfers'] *= tmp['dsct']*tmp['pop']

    tmp_2 = simulation.cohorts_alt.loc[:, ['net_transfers', 'pop', 'dsct']]
    tmp_2['running_transfers'] = tmp_2['net_transfers']
    tmp_2['net_transfers'] *= tmp_2['dsct']*tmp_2['pop']
    

    for year in year_list:
        flux_df = AccountingCohorts(tmp).extract_generation(year=year, typ='net_transfers', age=0)
        flux_df = flux_df.xs(0, level='sex')
        flux_df.columns = [year]
        print year

        flux_df_alt = AccountingCohorts(tmp_2).extract_generation(year=year, typ='net_transfers', age=0)
        flux_df_alt = flux_df_alt.xs(0, level='sex')
        flux_df_alt.columns = [str(year)+'_alt']
        
        flux_df = concat([flux_df, flux_df_alt], axis=1)#, ignore_index=True)
        flux_df[year] *= ((1+simulation.discount_rate)/(1+simulation.growth_rate))**(year - year_min)
        flux_df[str(year)+'_alt'] *= ((1+simulation.discount_rate_alt)/(1+simulation.growth_rate_alt))**(year - year_min)
        print flux_df.head()
    
        flux_df.to_excel(str(xls)+str(year)+'_ESP_agg.xlsx', 'flux')
    gc.collect()

def produce_ipl_evolution(simulation, year_min = 1996):
    
    arrays=arange(year_min, year_min+60)
    record = DataFrame(index=arrays)
    record['ipl'] = NaN
    record['ipl_réforme'] = NaN
    
    for year in range(year_min, year_min+60):
        print year
        #On tente de tronquer la df au fil du temps
        try:
            simulation.population = simulation.population.drop(labels=year-1, level='year')
            simulation.population_alt = simulation.population_alt.drop(labels=year-1, level='year')
        except:
            print 'except path'
            pass
        
        taxes_list = ['tva', 'tipp', 'cot', 'irpp', 'impot', 'property']
        payments_list = ['chomage', 'retraite', 'revsoc', 'maladie', 'educ']
        
        simulation.create_cohorts()
        simulation.create_cohorts(default=False)

        simulation.cohorts.compute_net_transfers(name = 'net_transfers', taxes_list = taxes_list, payments_list = payments_list)
        simulation.create_present_values('net_transfers', default=True)
        
        simulation.cohorts_alt.loc[[x>=2075 for x in simulation.cohorts_alt.index.get_level_values(2)], 'cot'] *= (1+0.1)
        simulation.cohorts_alt.compute_net_transfers(name = 'net_transfers', taxes_list = taxes_list, payments_list = payments_list)
        simulation.create_present_values('net_transfers', default=False)

#                     imbalance = simulation.compute_gen_imbalance(typ='net_transfers')
        ipl = simulation.compute_ipl(typ='net_transfers')
        ipl_alt = simulation.compute_ipl(typ='net_transfers', default=False)
       
        
        record.loc[year, "ipl"] = ipl/(8050.6e+09*(1+simulation.growth_rate)**(year-year_min))
        record.loc[year, 'ipl_réforme'] = ipl_alt/(8050.6e+09*(1+simulation.growth_rate)**(year-year_min))

    record.to_excel(xls+'ipl_flux_ESP.xlsx', 'ipl_relative_au_pib')
    gc.collect()

def produce_imbalance_evolution(simulation=simulation, year_min = 1996):
    
    arrays=arange(year_min, year_min+60)
    record = DataFrame(index=arrays)
    record['déséquilibre'] = NaN
    record['déséquilibre_alt'] = NaN
    
#     for year in range(year_min, year_min+60):
#         print year
#         #On tente de tronquer la df au fil du temps
#         try:
#             simulation.aggregate_pv = simulation.aggregate_pv.drop(labels=year-1, level='year')
#             simulation.aggregate_pv_alt = simulation.aggregate_pv_alt.drop(labels=year-1, level='year')
#         except:
#             print 'except path'
#             pass
#         simulation.aggregate_pv = AccountingCohorts(simulation.aggregate_pv)
#         simulation.aggregate_pv_alt = AccountingCohorts(simulation.aggregate_pv_alt)
#         
#         ratio_base = simulation.compute_gen_imbalance(typ='net_transfers')
#         ratio_alt = simulation.compute_gen_imbalance(typ='net_transfers', default=False)
#         record.loc[year, "déséquilibre"] = ratio_base
#         record.loc[year, 'déséquilibre_alt'] = ratio_alt
#     print record.head(30).to_string()
#     record.to_excel(xls+'imbalance_flux.xlsx', 'flux de déséquilibre')

    for year in range(year_min, year_min+60):
        print year
        #On tente de tronquer la df au fil du temps
        try:
            simulation.population = simulation.population.drop(labels=year-1, level='year')
            simulation.population_alt = simulation.population_alt.drop(labels=year-1, level='year')
        except:
            print 'except path'
            pass
        
        taxes_list = ['tva', 'tipp', 'cot', 'irpp', 'impot', 'property']
        payments_list = ['chomage', 'retraite', 'revsoc', 'maladie', 'educ']
        
        simulation.create_cohorts()
        simulation.create_cohorts(default=False)

        simulation.cohorts.compute_net_transfers(name = 'net_transfers', taxes_list = taxes_list, payments_list = payments_list)
        simulation.create_present_values('net_transfers', default=True)
        
        simulation.cohorts_alt.loc[[x>=2075 for x in simulation.cohorts_alt.index.get_level_values(2)], 'cot'] *= (1+0.1)
        simulation.cohorts_alt.compute_net_transfers(name = 'net_transfers', taxes_list = taxes_list, payments_list = payments_list)
        simulation.create_present_values('net_transfers', default=False)

#                     imbalance = simulation.compute_gen_imbalance(typ='net_transfers')
        imbalance = simulation.compute_gen_imbalance(typ='net_transfers')
        imbalance_alt = simulation.compute_gen_imbalance(typ='net_transfers', default=False)
       
        
        record.loc[year, "déséquilibre"] = imbalance
        record.loc[year, 'déséquilibre_alt'] = imbalance_alt
    record.to_excel(xls+'imbalance_flux_ESP.xlsx', 'flux de déséquilibre')
    

def cohorts_to_excels(simulation=simulation, to_print='base', suffix=''):
    """
    to_print : 'base' or 'alt' or 'both'
                Indicates the program what cohort to save
    """
    
    if to_print=='base' or to_print=='both':
        simulation.cohorts.to_excel(xls+suffix+'.xlsx', 'cohort_base')
    if to_print=='alt' or to_print=='both':
        simulation.cohorts_alt.to_excel(xls+suffix+'_alt.xlsx', 'cohort_alt')
    if to_print not in ['base', 'alt', 'both']:
        raise Warning('Nothing has been printed')




if __name__ == '__main__':
    simulation = generate_simulation()
#     produce_gen_accounts()
#     produce_agg_transfert_flux()
#     produce_percap_transfert_flux()
    produce_ipl_evolution(simulation=simulation)
    simulation = generate_simulation()
    produce_imbalance_evolution(simulation=simulation)
#     cohorts_to_excels()