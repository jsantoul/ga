# -*- coding:utf-8 -*-
'''
Created on 25 août 2013

@author: Jérôme SANTOUL
'''
from __future__ import division
from pandas import HDFStore
from pandas.io.parsers import ExcelFile

from cohorts.data_cohorts import DataCohorts
from src import SRC_PATH

import os, warnings

class HypothesisSet(object):
    '''
    This object contains all the necessary data to perform a simulation except the reference year's profiles
    However, it must be part of a simulation and is piloted through a simulation.
    There are methods to allow the object to be constructed but they are private and should be used through
    a simulation object.
    '''


    def __init__(self):
        '''
        Constructor
        '''

        self.population = None
        self.population_growth_rate = None

        self.population_projection = None
        self.tax_projection = None
        
        self.growth_rate = None #Growth rate of the economy
        self.discount_rate = None #Either state bonds rate or inflation rate.
        
        self.net_gov_wealth = 0
        self.net_gov_spendings = 0
        
        self.cohorts = None #A DataCohorts object
        self.aggregate_pv = None #An AccountingCohorts object
        self.percapita_pv = None #An AccountingCohorts object
    
    
    def set_population(self, dataframe):
        """
        Set population dataframe
        
        Parameters
        ----------
        dataframe : pandas DataFrame
                    Dataframe conaining the population
        
        """

        self.population = dataframe
        
    
    def load_population(self, population_filename, population_scenario):
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
        self.set_population(dataframe)
        store_pop.close()



    def set_gov_spendings(self, G, compute=False):
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
        g = self.growth_rate
        r = self.discount_rate

            
        if compute:
            net_gov_spendings = 0
            for t in range(1, self.year_length+1):
                year_gov_spending = G*((1+g)/(1+r))**t
                net_gov_spendings += year_gov_spending
        else:
            net_gov_spendings = G
        
        self.net_gov_spendings = net_gov_spendings

            
            
    def set_gov_wealth(self, W):
        """
        Set the present value of the net government wealth
        default : True or False
                  indicates wether this is the wealth for the default hypotheses set or 
                  alternate one
        """
        self.net_gov_wealth = W

            
    def set_discount_rate(self, r=0):
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
        self.discount_rate = r
        
        
    def set_growth_rate(self, g=0):
        """
        Set economy's BGP growth rate
        
        Parameters
        ----------
        
        g : float, default set to 0
            The growth rate
        default : True or False
                  indicates wether this is the growth rate for the default hypotheses set or alternate one

        """
        self.growth_rate = g

    def set_population_growth_rate(self, n=0):
        """
        Set the growth rate of the population
        
        Parameters
        ----------
        
        n : float, default set to 0
            The growth rate
        default : True or False
                  indicates wether this is the growth rate for the default hypotheses set or alternate one
        """
        self.population_growth_rate = n
            
    def set_population_projection(self, **kwargs):
        """
        Set population projection parameters
        
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
        
        Parameters
        ----------
        
        method : str
                 method use to project taxes
        """
        if self.tax_projection is None:
            self.tax_projection = dict()
        
        for key, value in kwargs.iteritems():
            self.tax_projection[key] = value
            
    def compute_net_transfers(self, name = 'net_transfers', taxes_list = None, payments_list = None):
        if taxes_list is None:
            taxes_list = []
            warnings.warn('No list of taxes provided, using an empty list for computation')
        if payments_list is None:
            payments_list = []
            warnings.warn('No list of subsidies or payments provided, using an empty list for computation')

        self.cohorts.compute_net_transfers(name, taxes_list, payments_list)
            

    def create_cohorts(self):
        """
        Create cohorts according to population, tax and transfers,
        and state expenses projection    
        """
        population = self.population
            
        cohorts = DataCohorts(data = population, columns = ['pop'])
        
        # Loading parameters to create a cohort :
        year_length = self.population_projection["year_length"]

        growth_rate = self.growth_rate
        discount_rate = self.discount_rate
        pop_growth_rate = self.population_growth_rate
            
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
        self.cohorts = cohorts
        self.cohorts.name = 'cohorte'
        
    
    def create_present_values(self, typ):
        """
        Create aggregated and per capita present values of net transfers according to the given cohort
        and state expenses projection 
        """
        self.aggregate_pv = self.cohorts.aggregate_generation_present_value(typ, discount_rate = self.discount_rate)
        self.aggregate_pv.name = 'comptes_gen_agrégés'
        self.aggregate_pv['pop'] = self.cohorts['pop']
            
        self.percapita_pv = self.cohorts.per_capita_generation_present_value(typ, discount_rate = self.discount_rate)
        self.percapita_pv.name = 'comptes_gen_indiv'
        self.percapita_pv['pop'] = self.cohorts['pop']
            

    def compute_ipl(self, typ, precision=False):
        """
        Returns the Intertemporal Public Liability generated by the simulation
        
        Parameters
        ----------
        
        typ : the name of the column containing the aggregated values of generational accounts
        
        default : indicate wether to perform the computation on the default or alternative parameters
        
        precision : to perform the computation of teh precision of the ipl instead of the ipl instead.
        """
        
        IPL = self.aggregate_pv.compute_ipl(typ, net_gov_wealth = self.net_gov_wealth, net_gov_spendings=self.net_gov_spendings, precision=precision)
        return IPL
    
    def create_age_class(self, typ, step = 1, default = True):
        """
        Returns a dataframe containing the average net transfer present values for each age class.
        """
        if default:
            age_class = self.aggregate_pv.create_age_class(step, typ)
        else:
            age_class = self.aggregate_pv_alt.create_age_class(step, typ)
        return age_class
        
    def compute_gen_imbalance(self, typ, default=True, to_return='ratio'):
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
        #Gestio des exception de l'argument to_return:
        if to_return not in ['difference', 'ratio', 'n_1', 'all']:
            to_return = 'ratio'
            print "Warning : argument to_return not recognized, function will return the default value "
        # On définit les dataframes sur avec les quelles on veut travailler :     
        if default:
            aggregate_pv = self.aggregate_pv
            cohorts = self.cohorts
            percapita_pv = self.percapita_pv
        else:
            aggregate_pv = self.aggregate_pv_alt
            cohorts = self.cohorts_alt
            percapita_pv = self.percapita_pv_alt
        
        year_min = aggregate_pv._year_min
        year_max = aggregate_pv._year_max
#         age_min = self.aggregate_pv._agemin
        age_max = aggregate_pv._agemax
         
        #Calculating the past transfers for both genders then deducting the equilibrium future transfers
        past_gen_dataframe = aggregate_pv.xs(year_min, level = 'year')
        past_gen_dataframe = past_gen_dataframe.cumsum()
        past_gen_transfer = past_gen_dataframe.get_value((age_max, 1), typ)
         
        future_gen_transfer = self.net_gov_spendings - self.net_gov_wealth - past_gen_transfer
        
        #Computing the number of people of the unborn generation
        population_unborn_ma = cohorts.get_value((0,0, year_min+1), 'pop')
        population_unborn_fe = cohorts.get_value((0,1,year_min+1), 'pop')
        population_unborn = population_unborn_ma + population_unborn_fe
         
        #Reorganizing data to prepare the computation of mu_1
        population_dataframe = cohorts.filter_value(age = [0], year = range(year_min+1, year_max+1), typ='pop')
        population_dataframe.gen_actualization(self.growth_rate, self.discount_rate)
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
    
    
    def break_down_ipl(self, typ, default=True, threshold = 60):
        """
        Returns the Intertemporal Public Liability series component in a dataframe
        WARNING : STILL NOT COMPLETE.
        Parameters
        ----------
        
        typ : the name of the column containing the aggregated values of generational accounts
        
        default : indicate wether to perform the computation on the default or alternative parameters
        """
        
        if default:
            break_down = self.aggregate_pv.break_down_ipl(typ, net_gov_wealth = self.net_gov_wealth, net_gov_spendings=self.net_gov_spendings, threshold = threshold)
        else:
            break_down = self.aggregate_pv_alt.break_down_ipl(typ, net_gov_wealth = self.net_gov_wealth_alt, net_gov_spendings=self.net_gov_spendings_alt, threshold = threshold)
        return break_down


    def save_hset(self, filename, attribute_list = ['cohorts', 'aggregate_pv', 'percapita_pv', 
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
            
