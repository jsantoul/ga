# -*- coding:utf-8 -*-
# Created on 6 mai 2013
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © #2013 Clément Schaff, Mahdi Ben Jelloul, Jérôme SANTOUL
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)

from __future__ import division
import os
from src.lib.simulation import Simulation
from src.lib.cohorts.accounting_cohorts import AccountingCohorts
from pandas import read_csv, HDFStore, concat, ExcelFile, DataFrame, MultiIndex
from numpy import array, hstack, arange
import matplotlib.pyplot as plt
from src import SRC_PATH

country = "france"    
population_filename = os.path.join(SRC_PATH, 'countries', country, 'sources',
                                           'data_fr', 'proj_pop_insee', 'proj_pop.h5')
profiles_filename = os.path.join(SRC_PATH, 'countries', country, 'sources',
                                         'data_fr','profiles.h5')
CBonnet_results = os.path.join(SRC_PATH, 'countries', country, 'sources',
                                           'Carole_Bonnet', 'theoretical_results.xls')
pop_insee = os.path.join(SRC_PATH, 'countries', country, 'sources',
                                           'Carole_Bonnet', 'pop_1996_2006.xls')


def test_comparison():
    
    print 'Entering the comparison function'
    
    simulation = Simulation()
    population_scenario_alt = "projpop0760_FECbasESPhautMIGbas"
    population_scenario = "projpop0760_FECbasESPbasMIGbas"
    simulation.load_population(population_filename, population_scenario)
    simulation.load_population(population_filename, population_scenario_alt, default=False)
    
    # Adding missing population data between 1996 and 2007 :
    store_pop = HDFStore(os.path.join(SRC_PATH, 'countries', country, 'sources',
                                           'Carole_Bonnet', 'pop_1996_2006.h5'))
    corrected_pop = store_pop['population']
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
    growth rate g = 0.5%
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
    

    simulation.cohorts_alt.compute_net_transfers(name = 'net_transfers', taxes_list = taxes_list, payments_list = payments_list)
    simulation.create_present_values('net_transfers', default=False)


    #Creating age classes
    cohorts_age_class = simulation.create_age_class(typ = 'net_transfers', step = 5)
    cohorts_age_class._types = [u'tva', u'tipp', u'cot', u'irpp', u'impot', u'property', u'chomage', u'retraite', u'revsoc', u'maladie', u'educ', u'net_transfers']
    age_class_pv_fe = cohorts_age_class.xs((1, 1996), level = ['sex', 'year'])
    
    cohorts_age_class_alt = simulation.create_age_class(typ = 'net_transfers', step = 5, default=False)
    cohorts_age_class_alt._types = [u'tva', u'tipp', u'cot', u'irpp', u'impot', u'property', u'chomage', u'retraite', u'revsoc', u'maladie', u'educ', u'net_transfers']
    age_class_pv_fe_alt = cohorts_age_class_alt.xs((1, 1996), level = ['sex', 'year'])
    
    print "AGE CLASS PV"
    print age_class_pv_fe.head(20)
    print age_class_pv_fe_alt.head(20)
    
    # Calculating the Intertemporal Public Liability
    ipl = simulation.compute_ipl(typ = 'net_transfers')
    ipl_alt = simulation.compute_ipl(typ = 'net_transfers', default = False)


    print "------------------------------------"
    print "IPL par défaut =", ipl
    print "IPL alternatif =", ipl_alt
    print "share of the GDP : ", ipl/8050.6e+09*100, "%"
    print "-alternative share-", ipl_alt/8050.6e+09*100, "%"
    print "------------------------------------"
    
    print "INTERNAL CHECKS :"
    print simulation.net_gov_spendings, simulation.net_gov_spendings_alt
    print simulation.net_gov_wealth, simulation.net_gov_wealth_alt
    
    
    #Plotting
    age_class_pv = cohorts_age_class.xs(1996, level = "year").unstack(level="sex")
    age_class_pv = age_class_pv['net_transfers']
    age_class_pv.columns = ['men' , 'women']
     
    age_class_pv_alt = cohorts_age_class_alt.xs(1996, level = "year").unstack(level="sex")
    age_class_pv_alt = age_class_pv_alt['net_transfers']
    age_class_pv_alt.columns = ['men_alt' , 'women_alt']
 
    age_class_pv['men_alt'] = age_class_pv_alt['men_alt'] ; age_class_pv['women_alt'] = age_class_pv_alt['women_alt']
    age_class_pv.plot(style = '--') ; plt.legend()
#     age_class_pv_alt.plot(style = '--') ; plt.legend()
    plt.axhline(linewidth=2, color='black')
    plt.show()


def compute_elasticities():
    
    print 'Entering the comparison function'
    
    simulation = Simulation()
    population_scenario = "projpop0760_FECbasESPbasMIGbas"
    simulation.load_population(population_filename, population_scenario)
    
    # Adding missing population data between 1996 and 2007 :
    store_pop = HDFStore(os.path.join(SRC_PATH, 'countries', country, 'sources',
                                           'Carole_Bonnet', 'pop_1996_2006.h5'))
    corrected_pop = store_pop['population']
    simulation.population = concat([corrected_pop, simulation.population])
    print '    longueur après combinaison',len(simulation.population)

    #Loading profiles :
    simulation.load_profiles(profiles_filename)
    
    year_length = 200
    simulation.set_year_length(nb_year=year_length)
    net_gov_wealth = -3217.7e+09
    year_gov_spending = (1094)*1e+09
    net_gov_wealth_alt = -3217.7e+09
    year_gov_spending_alt = (1094)*1e+09
    
    taxes_list = ['tva', 'tipp', 'cot', 'irpp', 'impot', 'property']
    payments_list = ['chomage', 'retraite', 'revsoc', 'maladie', 'educ']
    
    simulation.set_population_projection(year_length=simulation.year_length, method="exp_growth")

    elasticities_df = DataFrame(data=None, index=arange(0,4, 0.5), columns=arange(1, 4, 0.5), 
                 dtype=None, copy=False)
    epsilon = 1e-06
    
    for r_index in arange(1, 4, 0.5):
        for g_index in arange(0, 4, 0.5):
            r = r_index/100
            g = g_index/100
            n = 0.00
            pi = g
            
            r_alt = r + epsilon
            g_alt = g 
            n_alt = 0.00
            pi_alt = g_alt
            
            simulation.set_tax_projection(method="desynchronized", rate=g, inflation_rate=pi, typ=taxes_list, payments_list=payments_list)
            simulation.set_growth_rate(g)
            simulation.set_discount_rate(r) 
            simulation.set_population_growth_rate(n)
            simulation.create_cohorts()
            simulation.set_gov_wealth(net_gov_wealth)
            simulation.set_gov_spendings(year_gov_spending, default=True, compute=True)
            simulation.cohorts.compute_net_transfers(name = 'net_transfers', taxes_list = taxes_list, payments_list = payments_list)
            simulation.create_present_values('net_transfers', default=True)
            
            
            simulation.set_tax_projection(method="desynchronized", rate=g_alt, inflation_rate=pi_alt, typ=taxes_list, payments_list=payments_list)
            simulation.set_growth_rate(g_alt, default=False)
            simulation.set_discount_rate(r_alt, default=False) 
            simulation.set_population_growth_rate(n_alt, default=False)
            simulation.create_cohorts(default=False)
            simulation.set_gov_wealth(net_gov_wealth_alt, default=False)
            simulation.set_gov_spendings(year_gov_spending_alt, default=False, compute=True)
            simulation.cohorts_alt.compute_net_transfers(name = 'net_transfers', taxes_list = taxes_list, payments_list = payments_list)
            simulation.create_present_values('net_transfers', default=False)
            
            
            # Calculating the Intertemporal Public Liability
            ipl = simulation.compute_ipl(typ = 'net_transfers')
            ipl_alt = simulation.compute_ipl(typ = 'net_transfers', default = False)
            
            #Elasticities
            print "COMPUTING ELASTICITIES"
            print '------------------------'
            ipl_derivative = (ipl_alt - ipl)/epsilon
            print '    semi élasticité of IPL:', ipl_derivative/ipl
            print 'Valeur de q :'
            print (1+g)/(1+r)
            
            elasticities_df.loc[g_index, r_index] = ipl_derivative/ipl
    
    print elasticities_df.to_string()
            
    xls = "C:/Users/Utilisateur/Documents/GitHub/ga/src/countries/france/sources/Carole_Bonnet/elasticities_r.xlsx"
     
    elasticities_df.to_excel(xls, 'cohorte')
    

def multiple_scenario():
    
    print 'starting recording of multiple scenario'
    
    simulation = Simulation()
    levels = ['haut', 'cent', 'bas']
    
    taxes_list = ['tva', 'tipp', 'cot', 'irpp', 'impot', 'property']
    payments_list = ['chomage', 'retraite', 'revsoc', 'maladie', 'educ']
    
    arrays=[array(['FEC_haut', 'FEC_haut', 'FEC_haut','FEC_cent', 'FEC_cent', 'FEC_cent', 'FEC_bas', 'FEC_bas', 'FEC_bas']),
            array(['MIG_haut', 'MIG_cent', 'MIG_bas','MIG_haut', 'MIG_cent', 'MIG_bas','MIG_haut', 'MIG_cent', 'MIG_bas'])]
    
    
    record = DataFrame(index=arrays, columns=['ESP_haut', 'ESP_cent', 'ESP_bas'])
    
    print record
    
    for param1 in levels:
        for param2 in levels:
            for param3 in levels:
                
                scenario_name = "projpop0760_FEC"+param1+"ESP"+param2+"MIG"+param3
                print scenario_name
                
                simulation.load_population(population_filename, scenario_name)

                # Adding missing population data between 1996 and 2007 :
                store_pop = HDFStore(os.path.join(SRC_PATH, 'countries', country, 'sources',
                                           'Carole_Bonnet', 'pop_1996_2006.h5'))
                corrected_pop = store_pop['population']
                simulation.population = concat([corrected_pop, simulation.population])

                #Loading profiles :
                simulation.load_profiles(profiles_filename)
    
                year_length = 250
                r = 0.03
                g = 0.01
                n = 0.00
                pi = 0.01
                simulation.set_year_length(nb_year=year_length)
                net_gov_wealth = -3217.7e+09
                year_gov_spending = (1094)*1e+09
                
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
                
                ipl = simulation.compute_ipl(typ = 'net_transfers')
                
#                 index_name = ('FEC_'+param1, 'MIG_'+param3)
                column_name = 'ESP_'+param2
                
                print ipl
                
                record.loc[('FEC_'+param1, 'MIG_'+param3), column_name] = ipl
                print record.to_string()
    xls = "C:/Users/Utilisateur/Documents/GitHub/ga/src/countries/france/sources/Carole_Bonnet/multiple_scenario.xlsx"
     
    record.to_excel(xls, 'ipl')
    
    
def test_saving():
    simulation = Simulation()
    
    
    population_scenario = "projpop0760_FECbasESPbasMIGbas"
    simulation.load_population(population_filename, population_scenario)
    simulation.load_profiles(profiles_filename)
    
    year_length = 250
    simulation.year_length = year_length
    r = 0.03
    g = 0.01
    n = 0.00
    net_gov_wealth = -3217.7e+09
    year_gov_spending = (1094)*1e+09
    
    # Loading simulation's parameters :
    simulation.set_population_projection(year_length=year_length, method="stable")
    simulation.set_tax_projection(method="per_capita", rate=g)
    simulation.set_growth_rate(g)
    simulation.set_discount_rate(r) 
    simulation.set_population_growth_rate(n)
    simulation.create_cohorts()
    simulation.set_gov_wealth(net_gov_wealth)
    simulation.set_gov_spendings(year_gov_spending, default=True, compute=True)
    
    taxes_list = ['tva', 'tipp', 'cot', 'irpp', 'impot', 'property']
    payments_list = ['chomage', 'retraite', 'revsoc', 'maladie', 'educ']
    simulation.cohorts.compute_net_transfers(name = 'net_transfers', taxes_list = taxes_list, payments_list = payments_list)
    simulation.create_present_values(typ = 'net_transfers')
    
    xls = "C:/Users/Utilisateur/Documents/GitHub/ga/src/countries/france/sources/Carole_Bonnet/saved_cohorts.xlsx"
    
    simulation.saving_simulation(file_path=xls)

def transition():
    
    
    levels = ['haut', 'cent', 'bas']
    
    taxes_list = ['tva', 'tipp', 'cot', 'irpp', 'impot', 'property']
    payments_list = ['chomage', 'retraite', 'revsoc', 'maladie', 'educ']
    
    arrays=array(['FEC-MIG_haut', 'FEC-MIG_cent', 'FEC-MIG_bas'])
    year_length = 200
    year_min = 1996
    year_max = year_min+year_length+1
    
    record = DataFrame(index=arrays, columns=['ESP_haut', 'ESP_cent', 'ESP_bas'])
    simulation = Simulation()

    print record
    for param1 in levels:
        for param2 in levels:
            population_scenario = "projpop0760_FEC"+param1+"ESP"+param2+"MIG"+param1

            simulation.load_population(population_filename, population_scenario)
    
            # Adding missing population data between 1996 and 2007 :
            store_pop = HDFStore(os.path.join(SRC_PATH, 'countries', country, 'sources',
                                           'Carole_Bonnet', 'pop_1996_2006.h5'))
            corrected_pop = store_pop['population']
            simulation.population = concat([corrected_pop, simulation.population])
            print '    longueur après combinaison',len(simulation.population)

            simulation.load_profiles(profiles_filename)
    
            simulation.year_length = year_length
            r = 0.03
            g = 0.01
            n = 0.00
            net_gov_wealth = -3217.7e+09
            year_gov_spending = (1094)*1e+09
    
            # Loading simulation's parameters :
            simulation.set_population_projection(year_length=year_length, method="stable")
            simulation.set_tax_projection(method="per_capita", rate=g)
            simulation.set_growth_rate(g)
            simulation.set_discount_rate(r) 
            simulation.set_population_growth_rate(n)
            simulation.create_cohorts()
            simulation.set_gov_wealth(net_gov_wealth)
            simulation.set_gov_spendings(year_gov_spending, default=True, compute=True)
    
            simulation.cohorts.compute_net_transfers(name = 'net_transfers', taxes_list = taxes_list, payments_list = payments_list)
    
#             year_min = simulation.cohorts._year_min
#             year_max = simulation.cohorts._year_min + year_length+1
            
            transition = DataFrame(index=array(range(year_min, year_max)), columns=['debt'])
    
            for year in range(year_min, year_max):
                actualize = True
        
                r = simulation.discount_rate
                g = simulation.growth_rate
                t = year-year_min
        
                df_year = simulation.cohorts.filter_value(year=[year], typ=['net_transfers', 'pop'])
        
                print year
#                 print (t*actualize)
        
                df_year['agg_transfers'] = df_year['net_transfers']*df_year['pop']*((1+g)/(1+r))**(t*actualize)
                df_year = df_year.cumsum()
        
                gov_spendings = simulation.net_gov_spendings*((1+g)/(1+r))**(t*actualize)
                cum_net_transfers = df_year.get_value((100,1,year), 'agg_transfers')
                debt = cum_net_transfers - gov_spendings
        
                transition.loc[year, 'debt'] = debt
#                 print transition.head().to_string()
        
            xls = "C:/Users/Utilisateur/Documents/GitHub/ga/src/countries/france/sources/Carole_Bonnet/"+population_scenario+'.xlsx'
     
            transition.to_excel(xls, 'ipl')
    
    
if __name__ == '__main__':
#     test_comparison()
#     test_saving()
#     compute_elasticities()
#     multiple_scenario()
    transition()