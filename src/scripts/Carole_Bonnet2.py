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
from pandas import read_csv, HDFStore, concat, ExcelFile, DataFrame
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
    
def fill_pop_data():
    
    h5_insee = ExcelFile(pop_insee)

    for year in range(1996, 2007):
        print year
        
        #On extrait la feuille qui nous intéresse :
        xls = h5_insee.parse(str(year), index_col = 0)
        print xls.columns
        age_max = max(xls['age'])
        print '    age_max = ', age_max
        
        #On sépare les hommes et les femmes puis on crée la colonne sexe
        xls_men = xls.loc[:, ['men','age','year']]
        xls_wom = xls.loc[:, ['women','age','year']]
        
        xls_men['sex'] = 0
        xls_wom['sex'] = 1
        
        if year == 1996:
            print 'initialisation', year
            xls_men.set_index(['age', 'sex', 'year'], inplace=True)
            xls_wom.set_index(['age', 'sex', 'year'], inplace=True)
            
            corrected_pop_men = xls_men
            corrected_pop_wom = xls_wom
            print corrected_pop_men.head().to_string()
            
        else:
        #Il faut gérer le changement de notation des données insee : 
        #à partir de 2000 on enregistre les gens jusqu'à 105 ans au lieu de 100
        
            if age_max>100:    
                print '    Age maximal > 100'
                print range(age_max.astype('int'), 99, -1)
                
                # On somme les personnes de 100 ans et plus
                tot_men = xls_men.men[ xls_men.age >= 100].sum()
                tot_wom = xls_wom.women[ xls_wom.age >= 100].sum()
                print tot_men, tot_wom
                
                # On remplace la valeur des centanaires par la valeur calculée
                # puis on coupe les dataframes :
                xls_men.loc[xls_men.age == 100,'men'] = tot_men
                xls_wom.loc[xls_wom.age == 100,'women'] = tot_wom   
                   
                xls_men.set_index(['age', 'sex', 'year'], inplace=True)
                xls_wom.set_index(['age', 'sex', 'year'], inplace=True)
                
                xls_men = xls_men.loc[:(100, 0, year),:]
                xls_wom = xls_wom.loc[:(100, 1, year),:]
                
                # On combine avec le reste :
                corrected_pop_men = concat([corrected_pop_men, xls_men])
                corrected_pop_wom = concat([corrected_pop_wom, xls_wom])
                 
            if age_max == 100:
                #On met en place les index puis on combine
                xls_men.set_index(['age', 'sex', 'year'], inplace=True)
                xls_wom.set_index(['age', 'sex', 'year'], inplace=True)
                
                corrected_pop_men = concat([corrected_pop_men, xls_men])
                corrected_pop_wom = concat([corrected_pop_wom, xls_wom])
                
                print corrected_pop_men.head().to_string()
                
            if age_max < 100:
                raise Exception('the maximum recorded age is below 100')
            
        print len(corrected_pop_men), '    longueur de corrected_pop'
        
    print '    fin des boucles'
    print corrected_pop_men.columns
    corrected_pop_men.columns = ['pop']
    corrected_pop_wom.columns = ['pop']

    print corrected_pop_men.head(10).to_string()
    
    corrected_pop = concat([corrected_pop_men, corrected_pop_wom])
    print corrected_pop.head().to_string()
    print len(corrected_pop)
    store_pop = HDFStore(os.path.join(SRC_PATH, 'countries', country, 'sources',
                                           'Carole_Bonnet', 'pop_1996_2006.h5'))
    store_pop['population'] = corrected_pop
    
    
def test():
    print 'Entering the simulation of C. Bonnet'

    simulation = Simulation()
    population_scenario = "projpop0760_FECbasESPhautMIGbas"
    simulation.load_population(population_filename, population_scenario)
    
    # Adding missing population data between 1996 and 2007 :
    store_pop = HDFStore(os.path.join(SRC_PATH, 'countries', country, 'sources',
                                           'Carole_Bonnet', 'pop_1996_2006.h5'))
    corrected_pop = store_pop['population']
    print simulation.population.head().to_string()
    print corrected_pop.head().to_string()
    print '    longueurs des inputs'
    print 'prévisions insee', len(simulation.population), 'population corrigée', len(corrected_pop)
     
    simulation.population = concat([corrected_pop, simulation.population])
    print '    longueur après combinaison',len(simulation.population)

    #Loading profiles :
    simulation.load_profiles(profiles_filename)
    xls = ExcelFile(CBonnet_results)
    
    """
    Hypothesis set #1 : 
    actualization rate r = 3%
    growth rate g = 1%
    net_gov_wealth = -3217.7e+09 (unit : Franc Français (FRF) of 1996)
    non ventilated government spendings in 1996 : 1094e+09 FRF
    """

    #Setting parameters :
    year_length = 250
    simulation.year_length = year_length
    r = 0.03
    g = 0.01
    n = 0.00
    net_gov_wealth = -3217.7e+09
    year_gov_spending = (1094)*1e+09

#     avg_gov_spendings = 0
#     # List w/ the economic affairs
#     spending_list = [241861, 246856, 245483, 251110, 261752, 271019,    
#                      286330,    290499,    301556,    315994,    315979,    332317,
#                      343392,    352239,    356353,    356858]
#     count = 0
#     for spent in spending_list:
#         year_gov_spending = spent*1e+06*((1+g)/(1+r))**count*6.55957
#         print year_gov_spending
#         net_gov_spendings += year_gov_spending
#         avg_gov_spendings += year_gov_spending
#         count += 1

#     avg_gov_spendings /= (count)
#     print 'avg_gov_spendings = ', avg_gov_spendings

    # Loading simulation's parameters :
    simulation.set_population_projection(year_length=year_length, method="stable")
    simulation.set_tax_projection(method="per_capita", rate=g)
    simulation.set_growth_rate(g)
    simulation.set_discount_rate(r) 
    simulation.set_population_growth_rate(n)
    simulation.create_cohorts()
    simulation.set_gov_wealth(net_gov_wealth)
    simulation.set_gov_spendings(year_gov_spending, default=True, compute=True)

    #Calculating net transfers :
    #Net_transfers = tax paid to the state minus money recieved from the state
    taxes_list = ['tva', 'tipp', 'cot', 'irpp', 'impot', 'property']
    payments_list = ['chomage', 'retraite', 'revsoc', 'maladie', 'educ']
    simulation.cohorts.compute_net_transfers(name = 'net_transfers', taxes_list = taxes_list, payments_list = payments_list)
    
    """
    Reproducing the table 2 : Comptes générationnels par âge et sexe (Compte central)
    """
    #Generating generationnal accounts :
    year = 1996
    simulation.create_present_values(typ = 'net_transfers')
    print "PER CAPITA PV"
    print simulation.percapita_pv.xs(0, level = 'age').head(10)
    print simulation.percapita_pv.xs((0, year), level = ['sex', 'year']).head(10)


    # Calculating the Intertemporal Public Liability
    ipl = simulation.compute_ipl(typ = 'net_transfers')
    print "------------------------------------"
    print "IPL =", ipl
    print "share of the GDP : ", ipl/8050.6e+09*100, "%"
    print "------------------------------------"
    
    #Calculating the generational imbalance
    gen_imbalance = simulation.compute_gen_imbalance(typ = 'net_transfers')
    print "----------------------------------"
    print "[n_1/n_0=", gen_imbalance,"]"
    print "----------------------------------"    
    
    
    #Creating age classes
    cohorts_age_class = simulation.create_age_class(typ = 'net_transfers', step = 5)
    cohorts_age_class._types = [u'tva', u'tipp', u'cot', u'irpp', u'impot', u'property', u'chomage', u'retraite', u'revsoc', u'maladie', u'educ', u'net_transfers']
    age_class_pv_fe = cohorts_age_class.xs((1, year), level = ['sex', 'year'])
    age_class_pv_ma = cohorts_age_class.xs((0, year), level = ['sex', 'year'])
    
    print "AGE CLASS PV"
    print age_class_pv_fe.head()
    print age_class_pv_ma.head()
    
    
#     #Plotting
#     age_class_pv = cohorts_age_class.xs(year, level = "year").unstack(level="sex")
#     age_class_pv = age_class_pv['net_transfers']
#     age_class_pv.columns = ['men' , 'women']
# #     age_class_pv['total'] = age_class_pv_ma['net_transfers'] + age_class_pv_fe['net_transfers']
# #     age_class_pv['total'] *= 1.0/2.0
#     age_class_theory = xls.parse('Feuil1', index_col = 0)
#         
#     age_class_pv['men_CBonnet'] = age_class_theory['men_Cbonnet']
#     age_class_pv['women_CBonnet'] = age_class_theory['women_Cbonnet']
#     age_class_pv.plot(style = '--') ; plt.legend()
#     plt.axhline(linewidth=2, color='black')
#     plt.show()

    #Saving the decomposed ipl:
#     breaked_down = simulation.break_down_ipl(typ='net_transfers')
#     
#     xls = "C:/Users/Utilisateur/Documents/GitHub/ga/src/countries/france/sources/Carole_Bonnet/broken_down.xlsx"
#       
#     breaked_down.to_excel(xls, 'ipl')
    
    
def show_data():
    
    country = "france"    
    population_filename = os.path.join(SRC_PATH, 'countries', country, 'sources',
                                           'data_fr', 'proj_pop_insee', 'proj_pop.h5')
    profiles_filename = os.path.join(SRC_PATH, 'countries', country, 'sources',
                                         'data_fr','profiles.h5')

    simulation = Simulation()
    population_scenario = "projpop0760_FECbasESPbasMIGbas"
    
    simulation.load_population(population_filename, population_scenario)
    simulation.load_profiles(profiles_filename)
    
    simulation.restricted_pop1 = simulation.population.iloc[:101,:]
    simulation.restricted_pop2 = simulation.population.iloc[5454:5555,:]
    
    simulation.restricted_pop = concat([simulation.restricted_pop1, simulation.restricted_pop2])
    simulation.profiles.reset_index(inplace=True); simulation.restricted_pop.reset_index(inplace=True)
    simulation.restricted_pop['year'] = 1996
    print simulation.restricted_pop.to_string()
    print simulation.profiles.head()
    
    simulation.profiles['pop'] = simulation.restricted_pop['pop'] 
    simulation.profiles.set_index(['age', 'sex', 'year'], inplace=True)
    print simulation.profiles.loc[:, ['pop', 'tva']].tail(10).to_string()

    simulation.profiles['tva'] *= simulation.profiles['pop']
    print simulation.profiles.loc[:, ['pop', 'tva']].tail(10).to_string()
    
    agreg_irpp = simulation.profiles.cumsum().get_value((100,1,1996), 'tva')
    agreg_pop = simulation.profiles.cumsum().get_value((100,1,1996), 'pop')
    print agreg_irpp, agreg_pop

    
if __name__ == '__main__':
#     fill_pop_data()
    test()
#     show_data()

