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
from numpy import array, hstack, arange, NaN
import matplotlib.pyplot as plt
from src import SRC_PATH
from src.lib.cohorts.accounting_cohorts import AccountingCohorts


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
    population_scenario_alt = "projpop0760_FECbasESPbasMIGbas"
    population_scenario = "projpop0760_FECbasESPbasMIGbas"
    simulation.load_population(population_filename, population_scenario)
    simulation.load_population(population_filename, population_scenario_alt, default=False)
    
    # Adding missing population data between 1996 and 2007 :
    store_pop = HDFStore(os.path.join(SRC_PATH, 'countries', country, 'sources',
                                           'Carole_Bonnet', 'pop_1996_2006.h5'))
    corrected_pop = store_pop['population']
    simulation.population = concat([corrected_pop, simulation.population])
    simulation.population_alt = concat([corrected_pop.iloc[0:101, :], corrected_pop.iloc[1111:1212,:]]) #concat([corrected_pop, simulation.population_alt])
    
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
    
    #simulation.cohorts_alt.loc[(0,0,2014):, 'cot'] *= (1+0.1)
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

#     #Plotting profiles :
#     profiles_to_plot = simulation.cohorts.xs(90, level = "age").unstack(level="sex")
#     profiles_to_plot = profiles_to_plot['net_transfers']
#     profiles_to_plot.columns = ['men' , 'women']
#       
#     profiles_to_plot_alt = simulation.cohorts_alt.xs(90, level = "age").unstack(level="sex")
#     profiles_to_plot_alt = profiles_to_plot_alt['net_transfers']
#     profiles_to_plot_alt.columns = ['men_alt' , 'women_alt']
#   
#     profiles_to_plot['men_alt'] = profiles_to_plot_alt['men_alt'] ; profiles_to_plot['women_alt'] = profiles_to_plot_alt['women_alt']
#     profiles_to_plot.plot(style = '--') ; plt.legend()
# #     age_class_pv_alt.plot(style = '--') ; plt.legend()
#     plt.axhline(linewidth=2, color='black')
    
#     cohorts_age_class.xs(2020, level = "year").unstack(level="sex").plot(subplots=True)
#     plt.show()

    #Saving the decomposed ipl:
    to_save = simulation.break_down_ipl(typ='net_transfers', default=False, threshold=60)
       
#     to_save = age_class_pv
    xls = "C:/Users/Utilisateur/Documents/GitHub/ga/src/countries/france/sources/Carole_Bonnet/stationnaire_alt.xlsx"
         
    to_save.to_excel(xls, 'ipl')


def compute_elasticities():
    
    print 'Entering the comparison function'
    
    simulation = Simulation()

    year_length = 200
    simulation.set_year_length(nb_year=year_length)
    net_gov_wealth = -3217.7e+09
    year_gov_spending = (1094)*1e+09
    net_gov_wealth_alt = -3217.7e+09
    year_gov_spending_alt = (1094)*1e+09
    
    taxes_list = ['tva', 'tipp', 'cot', 'irpp', 'impot', 'property']
    payments_list = ['chomage', 'retraite', 'revsoc', 'maladie', 'educ']
    
    simulation.set_population_projection(year_length=simulation.year_length, method="exp_growth")

    epsilon = 0.5

    levels = ['haut', 'cent', 'bas']
    record = DataFrame(index=levels)
    print record
    
    param1 = 'haut'
    param2 = 'haut'
    param3 = 'cent'
    
    population_scenario = "projpop0760_FEC"+param2+"ESP"+param2+"MIG"+param2
    population_scenario_alt = 'projpop0760_FEC'+param1+'ESP'+param2+'MIG'+param3
    
    simulation.load_population(population_filename, population_scenario)
    simulation.load_population(population_filename, population_scenario_alt, default=False)

    # Adding missing population data between 1996 and 2007 :
    store_pop = HDFStore(os.path.join(SRC_PATH, 'countries', country, 'sources',
                                           'Carole_Bonnet', 'pop_1996_2006.h5'))
    corrected_pop = store_pop['population']
    simulation.population = concat([corrected_pop, simulation.population])
    simulation.population_alt = concat([corrected_pop, simulation.population_alt])
    print '    longueur après combinaison',len(simulation.population)

    #Loading profiles :
    simulation.load_profiles(profiles_filename)
    r = 0.03
    g = 0.01
    n = 0.00
    pi = g
    
    r_alt = r
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
    print 'IPL = ', ipl
    print 'IPL_alt=  ', ipl_alt
    
    #Elasticities
    print "COMPUTING ELASTICITIES"
    print '------------------------'
    ipl_derivative = (ipl_alt - ipl)/epsilon
    print '    semi élasticité of IPL:', ipl_derivative/ipl
    print 'Valeur de q :'
    print (1+g)/(1+r)
    
    col_name = 'MIG'+param3
    record[col_name] = NaN
    record.loc[param1, col_name] = ipl_derivative/ipl
        
    print record.to_string()
            
#     xls = "C:/Users/Utilisateur/Documents/GitHub/ga/src/countries/france/sources/Carole_Bonnet/elasticities_pop.xlsx"
#      
#     record.to_excel(xls, 'cohorte')
    

def simple_scenario():
    
    #Initialisation et entrée des paramètres de base :
    simulation = Simulation()
    year_length = 300
    simulation.set_year_length(nb_year=year_length)
    net_gov_wealth = -3217.7e+09
    year_gov_spending = (1094)*1e+09
    net_gov_wealth_alt = -3217.7e+09
    year_gov_spending_alt = (1094)*1e+09
    taxes_list = ['tva', 'tipp', 'cot', 'irpp', 'impot', 'property']
    payments_list = ['chomage', 'retraite', 'revsoc', 'maladie', 'educ']
    
    simulation.set_population_projection(year_length=simulation.year_length, method="exp_growth")

    #On charge la population:
    population_scenario = "projpop0760_FECbasESPbasMIGbas"
    store_pop = HDFStore(os.path.join(SRC_PATH, 'countries', country, 'sources',
                                           'Carole_Bonnet', 'pop_1996_2006.h5'))
    corrected_pop = store_pop['population']
    simulation.population = concat([corrected_pop.iloc[0:101, :], corrected_pop.iloc[1111:1212,:]]) #<- la première année TODO: c'est moche
    simulation.load_population(population_filename, population_scenario, default=False)

    simulation.population_alt = concat([corrected_pop, simulation.population_alt])

    simulation.load_profiles(profiles_filename)
    r = 0.03
    g = 0.01
    n = 0.00
    
    r_alt = r
    g_alt = g 
    n_alt = 0.00

    #On crée le témoin :
    simulation.set_tax_projection(method="aggregate", rate=g)
    simulation.set_growth_rate(g)
    simulation.set_discount_rate(r) 
    simulation.set_population_growth_rate(n)
    
    simulation.create_cohorts()
    
    simulation.set_gov_wealth(net_gov_wealth)
    simulation.set_gov_spendings(year_gov_spending, default=True, compute=True)
    simulation.cohorts.compute_net_transfers(name = 'net_transfers', taxes_list = taxes_list, payments_list = payments_list)
    simulation.create_present_values('net_transfers', default=True)
    
    #On crée le groupe test :
    simulation.set_growth_rate(g_alt, default=False)
    simulation.set_discount_rate(r_alt, default=False) 
    simulation.set_population_growth_rate(n_alt, default=False)
    
    simulation.create_cohorts(default=False)
    simulation.cohorts_alt.loc[[x>=2015 for x in simulation.cohorts_alt.index.get_level_values(2)], 'retraite'] *= (1/2)

    simulation.set_gov_wealth(net_gov_wealth_alt, default=False)
    simulation.set_gov_spendings(year_gov_spending_alt, default=False, compute=True)
    simulation.cohorts_alt.compute_net_transfers(name = 'net_transfers', taxes_list = taxes_list, payments_list = payments_list)
    simulation.create_present_values('net_transfers', default=False)
    
    #Calcul de l'IPL et de sa décomposition
    ipl_base = simulation.compute_ipl(typ='net_transfers')
    ipl_alt = simulation.compute_ipl(typ='net_transfers', default=False, precision=False)
    
    tmp = simulation.cohorts.loc[:, ['net_transfers', 'pop', 'dsct']]
    tmp['running_transfers'] = tmp['net_transfers']
    tmp['net_transfers'] *= tmp['dsct']

    tmp_2 = simulation.cohorts_alt.loc[:, ['net_transfers', 'pop', 'dsct']]
    tmp_2['running_transfers'] = tmp_2['net_transfers']
    tmp_2['net_transfers'] *= tmp_2['dsct']
    
    xls = "C:/Users/Utilisateur/Documents/GitHub/ga/src/countries/france/sources/Output_folder/"

    for year in range(1996, 2007):
        flux_df = AccountingCohorts(tmp).extract_generation(year=year, typ='net_transfers', age=0)
        flux_df = flux_df.xs(0, level='sex')
        print year

        flux_df_alt = AccountingCohorts(tmp_2).extract_generation(year=year, typ='net_transfers', age=0)
        flux_df_alt = flux_df_alt.xs(0, level='sex')
        flux_df[year] = flux_df_alt['net_transfers']
    
        flux_df.to_excel(str(xls)+str(year)+'_.xlsx', 'flux')


    print ipl_base, ipl_alt
#     flux_df.to_excel(xls+'flux_temoin.xlsx', 'témoin')
#     flux_df_alt.to_excel(xls+'flux_pop.xlsx', 'avec_pop')
    


def transition():
    
    levels = ['haut', 'bas']
    
    taxes_list = ['tva', 'tipp', 'cot', 'irpp', 'impot', 'property']
    payments_list = ['chomage', 'retraite', 'revsoc', 'maladie', 'educ']
    
    year_length = 250
    year_min = 1996
    year_max = year_min+year_length-1
    
    arrays=arange(year_min, year_min+60)
    record = DataFrame(index=arrays)
    
    simulation = Simulation()

    for param1 in levels:
        for param2 in levels:
            
                population_scenario = "projpop0760_FEC"+param1+"ESP"+param2+"MIG"+param1
                simulation.load_population(population_filename, population_scenario)
    
                # Adding missing population data between 1996 and 2007 :
                store_pop = HDFStore(os.path.join(SRC_PATH, 'countries', country, 'sources',
                                           'Carole_Bonnet', 'pop_1996_2006.h5'))
                corrected_pop = store_pop['population']
                simulation.population = concat([corrected_pop, simulation.population])

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
                simulation.set_gov_wealth(net_gov_wealth)
                simulation.set_gov_spendings(year_gov_spending, default=True, compute=True)
                
                record[population_scenario] = NaN
                col_name2 = population_scenario+'_precision'
                record[col_name2] = NaN

                simulation.create_cohorts()
                simulation.cohorts.compute_net_transfers(name = 'net_transfers', taxes_list = taxes_list, payments_list = payments_list)
                simulation.create_present_values(typ='net_transfers')

                for year in range(year_min, year_min+60):
                    
                    #On tente de tronquer la df au fil du temps
                    try:
                        simulation.aggregate_pv = simulation.aggregate_pv.drop(labels=year-1, level='year')
                    except:
                        print 'except path'
                        pass
                    simulation.aggregate_pv = AccountingCohorts(simulation.aggregate_pv)

#                     imbalance = simulation.compute_gen_imbalance(typ='net_transfers')
                    ipl = simulation.compute_ipl(typ='net_transfers')
                    
                    # Calcul du résidut de l'IPL pour vérifier la convergence 
                    #(on se place tard dans la projection)
                    precision_df = simulation.aggregate_pv
                    print precision_df.head().to_string()
                    
                    year_min_ = array(list(precision_df.index.get_level_values(2))).min()
                    year_max_ = array(list(precision_df.index.get_level_values(2))).max() - 1
            #         age_min = array(list(self.index.get_level_values(0))).min()
                    age_max_ = array(list(precision_df.index.get_level_values(0))).max()
                    print 'CALIBRATION CHECK : ', year_min_, year_max_
                    
                    past_gen_dataframe = precision_df.xs(year_min_, level = 'year')
                    past_gen_dataframe = past_gen_dataframe.cumsum()
                    past_gen_transfer = past_gen_dataframe.get_value((age_max_, 1), 'net_transfers')
#                     print '    past_gen_transfer = ', past_gen_transfer
             
                    future_gen_dataframe = precision_df.xs(0, level = 'age')
                    future_gen_dataframe = future_gen_dataframe.cumsum()
                    future_gen_transfer = future_gen_dataframe.get_value((1, year_max_), 'net_transfers')
#                     print '    future_gen_transfer =', future_gen_transfer
                    
                    #Note : do not forget to eliminate values counted twice
                    last_ipl = past_gen_transfer + future_gen_transfer + net_gov_wealth - simulation.net_gov_spendings - past_gen_dataframe.get_value((0, 0), 'net_transfers')
                    last_ipl = -last_ipl
                    
                    print last_ipl, ipl
                    precision = (ipl - last_ipl)/ipl
                    print 'precision = ', precision
                    
                    record.loc[year, population_scenario] = ipl
                    record.loc[year, col_name2] = precision
                print record.head().to_string()
    xls = "C:/Users/Utilisateur/Documents/GitHub/ga/src/countries/france/sources/Carole_Bonnet/"+'ipl_evolution'+'.xlsx'
    print record.head(30).to_string()
    record.to_excel(xls, 'ipl')
    
    
if __name__ == '__main__':
#     test_comparison()
    simple_scenario()
#     test_saving()
#     compute_elasticities()
#     multiple_scenario()
#     transition()