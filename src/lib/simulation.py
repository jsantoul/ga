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


class Simulation(object):
    """
    A simulation object contains all parameters to compute a simulation 
    """
    def __init__(self):
        # These attributes are the core data of a simulation
        super(Simulation, self).__init__()
        self.profiles = None
        self.population_projection = None
        self.tax_projection = None
        self.year_length = 0

        # Base hypothesis set :
        self.population = None
        self.growth_rate = None #Growth rate of the economy
        self.population_growth_rate = None
        self.discount_rate = None
        self.country = None
        self.net_gov_spendings = 0
        self.cohorts = None #A DataCohorts object
        self.aggregate_pv = None #An AccountingCohorts object
        self.percapita_pv = None #An AccountingCohorts object
        self.net_gov_wealth = 0
       
        # Duplicated attributes to compute elasticities (alt stands for alternate):
        self.population_alt = None
        self.growth_rate_alt = None
        self.discount_rate_alt = None
        self.net_gov_spendings_alt = 0
        self.population_growth_rate_alt = None
        self.net_gov_wealth_alt = 0
        self.cohorts_alt = None #A DataCohorts object
        self.aggregate_pv_alt = None #An AccountingCohorts object
        self.percapita_pv_alt = None #An AccountingCohorts object        

        
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
        
    def set_population(self, dataframe, default=True):
        """
        Set population dataframe
        
        Parameters
        ----------
        dataframe : pandas DataFrame
                    Dataframe conaining the population
        
        """
        if default:
            self.population = dataframe
        else:
            self.population_alt = dataframe 
        
    
    def load_population(self, population_filename, population_scenario, default=True):
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
        self.set_population(dataframe, default=default)
        store_pop.close()


    def set_profiles(self, dataframe):
        """
        Set profiles dataframe
        
        dataframe : pandas DataFrame
                    Dataframe conaining the profiles
        
        """
        self.profiles = dataframe
    
    def set_gov_spendings(self, G, default=True, compute=False):
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
        if default:
            g = self.growth_rate
            r = self.discount_rate
        else:
            g = self.growth_rate_alt
            r = self.discount_rate_alt
            
        if compute:
            net_gov_spendings = 0
            for t in range(1, self.year_length+1):
                year_gov_spending = G*((1+g)/(1+r))**t
                net_gov_spendings += year_gov_spending
        else:
            net_gov_spendings = G
        
        if default:
            self.net_gov_spendings = net_gov_spendings
        else:
            self.net_gov_spendings_alt = net_gov_spendings
    
    def set_gov_wealth(self, W, default=True):
        """
        Set the present value of the net government wealth
        default : True or False
                  indicates wether this is the wealth for the default hypotheses set or 
                  alternate one
        """
        if default:
            self.net_gov_wealth = W
        else:
            self.net_gov_wealth_alt = W
            
        
    def set_year_length(self, nb_year = 300):
        """
        Set the present value of the net government wealth
        """
        self.year_length = nb_year

    def set_discount_rate(self, r=0, default=True):
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
        if default:
            self.discount_rate = r
        else:
            self.discount_rate_alt = r
        
        
    def set_growth_rate(self, g=0, default=True):
        """
        Set economy's BGP growth rate
        
        Parameters
        ----------
        
        g : float, default set to 0
            The growth rate
        default : True or False
                  indicates wether this is the growth rate for the default hypotheses set or alternate one

        """
        if default:
            self.growth_rate = g
        else:
            self.growth_rate_alt = g

    def set_population_growth_rate(self, n=0, default=True):
        """
        Set the growth rate of the population
        
        Parameters
        ----------
        
        n : float, default set to 0
            The growth rate
        default : True or False
                  indicates wether this is the growth rate for the default hypotheses set or alternate one
        """
        if default:
            self.population_growth_rate = n
        else:
            self.population_growth_rate_alt = n
            
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


    def load_profiles(self, profiles_filename, profiles_name = "profiles"):
        """
        Load profiles form a hdf5 file
        
        Parameters
        ----------
        
        profiles_filename : str
                   complete path to the hdf5 file
                   
        profiles : str, default to "profiles"
                   name of the table in the hdf5 file
        """
        
        store = HDFStore(profiles_filename, 'r')
        dataframe = store['profiles']
        self.set_profiles(dataframe)
        
    def compute_net_transfers(self, name = 'net_transfers', taxes_list = None, payments_list = None, default=True):
        if taxes_list is None:
            taxes_list = []
            raise Warning('No list of taxes provided, using an empty list for computation')
        if payments_list is None:
            payments_list = []
            raise Warning('No list of subsidies or payments provided, using an empty list for computation')
        if default:
            self.cohorts.compute_net_transfers(name, taxes_list, payments_list)
        else:
            self.cohorts_alt.compute_net_transfers(name, taxes_list, payments_list)

#===============================================================================
# Set of methods to conduct the simulation itself
#===============================================================================


    def create_cohorts(self, default = True):
        """
        Create cohorts according to population, tax and transfers,
        and state expenses projection    
        """
        if default:
            population = self.population
        else:
            population = self.population_alt
            
        cohorts = DataCohorts(data = population, columns = ['pop'])
        
        # Loading parameters to create a cohort :
        year_length = self.population_projection["year_length"]

        if default:
            growth_rate = self.growth_rate
            discount_rate = self.discount_rate
            pop_growth_rate = self.population_growth_rate
        else:
            growth_rate = self.growth_rate_alt
            discount_rate = self.discount_rate_alt
            pop_growth_rate = self.population_growth_rate_alt
            
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
        if default:
            self.cohorts = cohorts
            self.cohorts.name = 'cohorte'
        else:
            self.cohorts_alt = cohorts
            self.cohorts_alt.name = "cohorte_alternative"
        
    
    def create_present_values(self, typ, default=True):
        """
        Create aggregated and per capita present values of net transfers according to the given cohort
        and state expenses projection 
        """
        if default:
            self.aggregate_pv = self.cohorts.aggregate_generation_present_value(typ, discount_rate = self.discount_rate)
            self.aggregate_pv.name = 'comptes_gen_agrégés'
            self.aggregate_pv['pop'] = self.cohorts['pop']
            
            self.percapita_pv = self.cohorts.per_capita_generation_present_value(typ, discount_rate = self.discount_rate)
            self.percapita_pv.name = 'comptes_gen_indiv'
            self.percapita_pv['pop'] = self.cohorts['pop']
            
        else:
            self.aggregate_pv_alt = self.cohorts_alt.aggregate_generation_present_value(typ, discount_rate = self.discount_rate_alt)
            self.aggregate_pv_alt.name = 'comptes_agrégés_alternatifs'
            self.aggregate_pv_alt['pop'] = self.cohorts_alt['pop']
            
            self.percapita_pv_alt = self.cohorts_alt.per_capita_generation_present_value(typ, discount_rate = self.discount_rate_alt)
            self.percapita_pv_alt.name = 'comptes_indiv_alternatifs'
            self.percapita_pv_alt['pop'] = self.cohorts_alt['pop']


    def compute_ipl(self, typ, default=True, precision=False):
        """
        Returns the Intertemporal Public Liability generated by the simulation
        
        Parameters
        ----------
        
        typ : the name of the column containing the aggregated values of generational accounts
        
        default : indicate wether to perform the computation on the default or alternative parameters
        
        precision : to perform the computation of teh precision of the ipl instead of the ipl instead.
        """
        
        if default:
            IPL = self.aggregate_pv.compute_ipl(typ, net_gov_wealth = self.net_gov_wealth, net_gov_spendings=self.net_gov_spendings, precision=precision)
        else:
            IPL = self.aggregate_pv_alt.compute_ipl(typ, net_gov_wealth = self.net_gov_wealth_alt, net_gov_spendings=self.net_gov_spendings_alt, precision=precision)
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
        
    def compute_gen_imbalance(self, typ, default=True):
        """
        Returns a list of indexes of the generationnal imbalance between the newborn of the reference year 
        and the unborn of the next year.
        
        Parameters
        ----------
        typ : Str
        the name of the column containing the net_transfers from wich the imbalance will be calculated.
         
        Returns
        -------
        coefficients : List
        A list of three numbers ordered as follow 
        - n_1 is the predicted per_capita net transfer for the unborn generation which satisfies the Government Budget Constraint.
        - n_1 - n_0 is the difference of net payments between the newborn and the unborn
        - n_1/n_0 is the ratio of the payments.
         
        """   
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
        imbalance = n_1 - n_0
        imbalance_ratio = n_1/n_0
        coefficients = [n_1, imbalance, imbalance_ratio]
        return imbalance_ratio
    
    def saving_simulation(self, file_path=None):
        """
        CANNOT BE COMPLETED FOR NOW BECAUSE OF A BUG OF PANDAS
        """
        
        if file_path is None:
            raise Exception('A complete path to the file should be provided. DO not hesitate to use os.path.join')
        
        writer = ExcelFile(file_path)
        print writer
        cohorts_list_base =  [self.cohorts, self.cohorts_alt, self.percapita_pv, self.percapita_pv_alt, 
                          self.aggregate_pv, self.aggregate_pv_alt]
        cohorts_list = []
        
        for df in cohorts_list_base:
            try:
                name = df.name
                cohorts_list.append(df)
                print 'good to go'
            except:
                print 'no such cohort in this simulation'
        
        print len(cohorts_list)
        df_dict = dict( (dataframe.name , dataframe) for dataframe in cohorts_list)
        print df_dict
        
        for name, attribute in df_dict.iteritems():
            print 'new dataframe'
            #try:
            attribute.to_excel(writer, sheet_name=name)
            #except:
            #    print 'BUG ENCOUNTERED'
        writer.save()
    
    def break_down_ipl(self, typ, default=True, threshold = 60):
        """
        Returns the Intertemporal Public Liability series component in a dataframe
        
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


if __name__ == '__main__':
    pass
