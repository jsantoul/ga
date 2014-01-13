# -*- coding:utf-8 -*-
# Copyright © 2012 Clément Schaff, Mahdi Ben Jelloul
'''
Created on 20 mars 2013

@author: M Benjelloul, J Santoul
'''
from __future__ import division
from pandas import HDFStore
from pandas.io.parsers import ExcelFile

from cohorts.data_cohorts import DataCohorts
from src import SRC_PATH

import os, warnings

class Simulation(object):
    """
    A simulation object contains all parameters to compute a simulation. And perform multiple comparisons.
    For now one can only compare two different scenarii.
    
    TODO: Prepare the arrival of the sub-level hypothesis sets : 
    """
    def __init__(self):
        # These attributes are the core data of a simulation
        super(Simulation, self).__init__()
        self.profiles = None
        self.population_projection = {}
        self.tax_projection = {}
        self.year_length = 0
        self.country = None
        # Note : all the attributes that are dictionnaries must remain dictionnaries.
        
        # dictionnary attributes for comparison  
        self.population = {}
        self.growth_rate = {}
        self.population_growth_rate = {}
        self.discount_rate = {} #actualisation rate
        self.net_gov_spendings = {'default':0}
        self.cohorts = {} #A dict of DataCohorts object
        self.aggregate_pv = {} #An dict of AccountingCohorts object
        self.percapita_pv = {} #An dict of AccountingCohorts object
        self.net_gov_wealth = {'default':0}

        
#===============================================================================
# Set of methods to enter various parameters of the simulation object
#===============================================================================
        
    def set_country(self, country):
        """
        Set simulation country
        
        Parameters
        ----------
        country : str
                  country of the simulation
        """
        self.country = country
        
        
    def get_population_choices(self, filename):
        store_pop = HDFStore(filename,'r')
        choices = store_pop.keys()
        store_pop.close()
        return choices
        
    def set_population(self, dataframe, scenario="default"):
        """
        Set population dataframe. If no scenario name is precised, the base scenario will
        be modified
                
        Parameters
        ----------
        dataframe : pandas DataFrame
                    Dataframe conaining the population
        
        """
        self.population[scenario] = dataframe
#         if default:
#             self.population = dataframe
#         else:
#             self.population_alt = dataframe 
        
    
    def load_population(self, population_filename, population_scenario, scenario="default"):
        """
        Load population form a hdf5 file
        
        Parameters
        ----------
        
        population_filename : str
                   complete path to the hdf5 file
                   
        popualtion_scenario : str
                          name of the table in the hdf5 file
        """
        store_pop = HDFStore(population_filename,'r')
        dataframe = store_pop[population_scenario]
        self.set_population(dataframe, scenario=scenario)
        store_pop.close()


    def set_profiles(self, dataframe):
        """
        Set profiles dataframe
        
        dataframe : pandas DataFrame
                    Dataframe conaining the profiles
        
        """
        self.profiles = dataframe
    
    def set_gov_spendings(self, G, scenario="default", compute=False):
        """
        Set the value of unventilated spendings of the government. To perform the computation, 
        you must define first the value of the growth and discount rate.
        
        Parameters
        ----------
        
        G : Number
        default : True or False
                  indicates wether this are the spendings for the default hypotheses set or alternate one
        compute : True/False
                  use this option if you have the spendings only for the reference year. It will compute
                  the net present value of spendings for the entire time.
        """
#         if default:
#             g = self.growth_rate
#             r = self.discount_rate
#         else:
#             g = self.growth_rate_alt
#             r = self.discount_rate_alt
        try:
            g = self.growth_rate[scenario]
            r = self.discount_rate[scenario]
        except:
            raise Exception("No value for growth/discount rate for the scenario %s" (scenario))
            
        if compute:
            net_gov_spendings = 0
            for t in range(1, self.year_length+1):
                year_gov_spending = G*((1+g)/(1+r))**t
                net_gov_spendings += year_gov_spending
        else:
            net_gov_spendings = G
        
        self.net_gov_spendings[scenario] = G
    
    def set_gov_wealth(self, W, scenario="default"):
        """
        Set the present value of the net government wealth
        default : True or False
                  indicates wether this is the wealth for the default hypotheses set or 
                  alternate one
        """

        self.net_gov_wealth[scenario] = W

        
    def set_year_length(self, nb_year = 300):
        """
        Set the present value of the net government wealth
        """
        self.year_length = nb_year

    def set_discount_rate(self, r=0, scenario="default"):
        """
        Set discount rate
        
        Parameters
        ----------
        
        r : float, default set to 0
            The discount rate
        default : True or False
                  indicates wether this is the discount rate for the default hypotheses set or 
                  alternate one
        
        """
        self.discount_rate[scenario] = r

        
    def set_growth_rate(self, g=0, scenario="default"):
        """
        Set economy's BGP growth rate
        
        Parameters
        ----------
        
        g : float, default set to 0
            The growth rate
        default : True or False
                  indicates wether this is the growth rate for the default hypotheses set or alternate one

        """
        self.growth_rate[scenario] = g


    def set_population_growth_rate(self, n=0, scenario="default"):
        """
        Set the growth rate of the population
        
        Parameters
        ----------
        
        n : float, default set to 0
            The growth rate
        default : True or False
                  indicates wether this is the growth rate for the default hypotheses set or alternate one
        """
        self.population_growth_rate[scenario] = n

            
    def set_population_projection(self, **kwargs):
        """
        Set population projection parameters
        TODO: check if working w/ new scenario configuration !!!!!
        Parameters
        ----------
        
        method : str
                 method use to project population
        """
        if self.population_projection is None:
            self.population_projection = dict()
        for key, value in kwargs.iteritems():
            self.population_projection[key] = value


    def set_tax_projection(self, **kwargs):
        """
        Set tax projection parameters
        TODO: check if working w/ new scenario configuration !!!!!

        Parameters
        ----------
        
        method : str
                 method use to project taxes
        """
        if self.tax_projection is None:
            self.tax_projection = dict()
        
        for key, value in kwargs.iteritems():
            self.tax_projection[key] = value


    def load_profiles(self, profiles_filename):
        """
        Load profiles form a hdf5 file
        
        Parameters
        ----------
        
        profiles_filename : str
                   complete path to the hdf5 file
                   
        """
        
        store = HDFStore(profiles_filename, 'r')
        dataframe = store['profiles']
        self.set_profiles(dataframe)
        
    def compute_net_transfers(self, name = 'net_transfers', taxes_list = None, payments_list = None, scenario="default"):
        if taxes_list is None:
            taxes_list = []
            warnings.warn('No list of taxes provided, using an empty list for computation')
        if payments_list is None:
            payments_list = []
            warnings.warn('No list of subsidies or payments provided, using an empty list for computation')
        self.cohorts[scenario].compute_net_transfers(name, taxes_list, payments_list)

            
    def get_scenario_param(self, scenario_name = "default"):
        """
        method to call all the existing parameters of a scenario inside a simulation
        """
        
        #Part 1 : get existing values
        attr_dict_value = {'growth rate': self.growth_rate, "discount rate":self.discount_rate, 
                           "net gov spendings": self.net_gov_spendings, 
                           "net gov wealth" : self.net_gov_wealth, 
                           "population growth rate" : self.population_growth_rate}
        attr_dict_existence = {"cohorte de base":self.cohorts, 
                               "valeurs agrégées":self.aggregate_pv, 
                               "valeurs par capita":self.percapita_pv}
        
        for attribute, dict in attr_dict_value.items():
            try:
                new_value = dict[scenario_name]
                attr_dict_value[attribute] = new_value
            except:
                attr_dict_value[attribute] = False
        
        for dataframe, dict in attr_dict_existence.items():
            try:
                attr_dict_existence[dataframe] = (dict is not None)
                print "try succedeed" #test line
            except:
                attr_dict_existence[dataframe] = False
        
        #Part 2 : print what is existing
        
        print attr_dict_value
        print attr_dict_existence


#===============================================================================
# Set of methods to conduct the simulation itself
#===============================================================================


    def create_cohorts(self, scenario="default"):
        """
        Create cohorts according to population, tax and transfers,
        and state expenses projection    
        """
        population = self.population[scenario]
            
        cohorts = DataCohorts(data = population, columns = ['pop'])
        
        # Loading parameters to create a cohort :
        year_length = self.population_projection["year_length"] #replace with self.year_length ??

        growth_rate = self.growth_rate[scenario]
        discount_rate = self.discount_rate[scenario]
        pop_growth_rate = self.population_growth_rate[scenario]

        # Complete population projection
        method = self.population_projection["method"]        
        cohorts.population_project(year_length, method = method, growth_rate = pop_growth_rate)
        
        # Generate discount factor and growth factor
        cohorts.gen_dsct(discount_rate)
        cohorts.gen_grth(growth_rate)

        # Fill profiles
        cohorts._fill(self.profiles)
        method = self.tax_projection["method"]
        if method == 'desynchronized':
            taxes_list = self.tax_projection["typ"]
            payments_list = self.tax_projection["payments_list"]
            inflation_rate = self.tax_projection['inflation_rate']
            cohorts.proj_tax(rate=growth_rate, inflation_rate=inflation_rate, typ = taxes_list, method=method, payments_list = payments_list)
        else: cohorts.proj_tax(rate=growth_rate, method=method)

        # Project net taxes TOOD: see MainWindow widget

        self.cohorts[scenario] = cohorts
        self.cohorts[scenario].name = scenario #TODO: Vraiment utile cette ligne ??
        
    
    def create_present_values(self, typ, scenario="default"):
        """
        Create aggregated and per capita present values of net transfers according to the given cohort
        and state expenses projection 
        """
        self.aggregate_pv[scenario] = self.cohorts[scenario].aggregate_generation_present_value(typ, discount_rate = self.discount_rate[scenario])
        self.aggregate_pv[scenario].name = 'comptes_gen_agrégés'+scenario
        self.aggregate_pv[scenario]['pop'] = self.cohorts[scenario]['pop']
            
        self.percapita_pv[scenario] = self.cohorts[scenario].per_capita_generation_present_value(typ, discount_rate = self.discount_rate[scenario])
        self.percapita_pv[scenario].name = 'comptes_gen_indiv'+scenario
        self.percapita_pv[scenario]['pop'] = self.cohorts[scenario]['pop']
            

    def compute_ipl(self, typ, scenario="default", precision=False):
        """
        Returns the Intertemporal Public Liability generated by the simulation
        
        Parameters
        ----------
        
        typ : the name of the column containing the aggregated values of generational accounts
        
        default : indicate wether to perform the computation on the default or alternative parameters
        
        precision : to perform the computation of teh precision of the ipl instead of the ipl instead.
        """
     
        IPL = self.aggregate_pv[scenario].compute_ipl(typ, net_gov_wealth = self.net_gov_wealth[scenario], net_gov_spendings=self.net_gov_spendings[scenario], precision=precision)
        return IPL
    
    def create_age_class(self, typ, step = 1, scenario="default"):
        """
        Returns a dataframe containing the average net transfer present values for each age class.
        """
        age_class = self.aggregate_pv[scenario].create_age_class(step, typ)
        return age_class
        
    def compute_gen_imbalance(self, typ, scenario="default", to_return='ratio'):
        """
        Returns a list of indexes of the generationnal imbalance between the newborn of the reference year 
        and the unborn of the next year.
        
        Parameters
        ----------
        typ : Str
        the name of the column containing the net_transfers from wich the imbalance will be calculated.
        default : True or False
        indicates if the computation should be performed on the default scenario or on the alternative scenario
        to_return : 'ratio', 'difference', 'n_1' or 'all'
        indicates the value one wants to compute (more on these below). If all is chosen, a tuple will be returned
         
        Returns
        -------
        coefficients : List
        A list of three numbers ordered as follow 
        - n_1 is the predicted per_capita net transfer for the unborn generation which satisfies the Government Budget Constraint.
        - n_1 - n_0 is the 'difference' of net payments between the newborn and the unborn
        - n_1/n_0 is the 'ratio' of the payments.
         
        """   
        #Gestion des exception de l'argument to_return:
        if to_return not in ['difference', 'ratio', 'n_1', 'all']:
            to_return = 'ratio'
            print "Warning : argument to_return not recognized, function will return the ratio value "
        
        #On définit les dataframes et valeurs avec lesquelles on veut travailler :     
        aggregate_pv = self.aggregate_pv[scenario]
        cohorts = self.cohorts[scenario]
        percapita_pv = self.percapita_pv[scenario]
        
        year_min = aggregate_pv._year_min
        year_max = aggregate_pv._year_max
        age_max = aggregate_pv._agemax
        
        net_gov_spendings = self.net_gov_spendings[scenario]
        net_gov_wealth = self.net_gov_wealth[scenario]
        growth_rate = self.growth_rate[scenario]
        discount_rate = self.discount_rate[scenario]
        
        #Calculating the past transfers for both genders then deducting the equilibrium future transfers
        past_gen_dataframe = aggregate_pv.xs(year_min, level = 'year')
        past_gen_dataframe = past_gen_dataframe.cumsum()
        past_gen_transfer = past_gen_dataframe.get_value((age_max, 1), typ)
         
        future_gen_transfer = net_gov_spendings - net_gov_wealth - past_gen_transfer
        
        #Computing the number of people of the unborn generation
        population_unborn_ma = cohorts.get_value((0,0, year_min+1), 'pop')
        population_unborn_fe = cohorts.get_value((0,1,year_min+1), 'pop')
        population_unborn = population_unborn_ma + population_unborn_fe
         
        #Reorganizing data to prepare the computation of mu_1
        population_dataframe = cohorts.filter_value(age = [0], year = range(year_min+1, year_max+1), typ='pop')
        population_dataframe.gen_actualization(growth_rate, discount_rate)
        population_dataframe = population_dataframe.unstack(level='sex')
        del population_dataframe[('actualization', 1)] #TODO : check if this line is necessary
        
        population_dataframe['unborn'] = population_unborn
        population_dataframe['mixed'] = population_dataframe[('pop', 0)] + population_dataframe[('pop', 1)]
        population_dataframe[('actualization', 0)] *= population_dataframe['mixed']/population_dataframe['unborn']
 
        #Computing the coefficient mu_1
        population_dataframe = population_dataframe.cumsum()        
        mu_1 = population_dataframe.get_value((0,year_max), ('actualization', 0))
        
        #Computing the final imbalance coefficients
        population_unborn = population_unborn_ma + population_unborn_fe
        n_1 = future_gen_transfer/(mu_1*population_unborn) # = percapita_future_gen_transfer
        n_0 = (percapita_pv.get_value((0, 0, year_min), typ)/2 + 
                               percapita_pv.get_value((0, 1, year_min), typ)/2) # = actual_gen_transfer
        
        difference = n_1 - n_0
        ratio = n_1/n_0
        coefficients = [n_1, difference, ratio]
        
        if to_return == 'difference':
            return difference
        if to_return == 'ratio':
            return ratio
        if to_return == 'n_1':
            return n_1
        if to_return == 'all':
            return coefficients
    
    
    def break_down_ipl(self, typ, scenario="default", threshold = 60):
        """
        Returns the Intertemporal Public Liability series component in a dataframe
        WARNING : STILL NOT COMPLETE.
        Parameters
        ----------
        
        typ : the name of the column containing the aggregated values of generational accounts
        
        default : indicate wether to perform the computation on the default or alternative parameters
        """
        
        net_gov_wealth = self.net_gov_wealth[scenario]
        net_gov_spendings = self.net_gov_spendings[scenario]     
        break_down = self.aggregate_pv[scenario].break_down_ipl(typ, net_gov_wealth , net_gov_spendings, threshold = threshold)
        return break_down


    def save_simulation(self, filename, attribute_list = ['cohorts', 'aggregate_pv', 'percapita_pv', 
                        'cohorts_alt', 'aggregate_pv_alt', 'percapita_pv_alt'], has_alt = False):
        """
        Saves the output dataframe under default directory in an HDF store.
        Warning : will override .h5 file if already existant !
        Warning : the data is saved as a dataframe, one has to recreate the Cohort when reading.

        Parameters
        ----------
        name : the name of the table inside the store
        filename : the name of the .h5 file where the table is stored. Created if not existant. 
        """
        # Creating the filepath :
        ERF_HDF5_DATA_DIR = os.path.join(SRC_PATH,'countries',self.country,'sources','Output_folder/')
        store = HDFStore(os.path.join(os.path.dirname(ERF_HDF5_DATA_DIR),filename+'.h5'))
        
        #Looping over simulation's attributes, saving only the one who are matching the list 
        # AND aren't empty
        from pandas import DataFrame

        for attrib, value in self.__dict__.iteritems():
            if attrib in attribute_list and value is not None:
                
                #Transforming the data within a cohort in a dataframe so HDFStore can handle it :
                record = DataFrame(index=value.index)
                for col in value.columns:
                    record[col] = value[col]
                print 'saving'
                store[attrib] = record
            else:
                print 'ignored'
        print store
        store.close()
if __name__ == '__main__':
    pass
