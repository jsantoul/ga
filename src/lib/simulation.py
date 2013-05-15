'''
Created on 20 mars 2013

@author: benjelloul, santoul
'''
from __future__ import division
from pandas import HDFStore
from cohorte import Cohorts
from numpy import array
from pandas import concat


class Simulation(object):
    """
    A simulation object contains all parameters to compute a simulation 
    """
    def __init__(self):
        super(Simulation, self).__init__()
        self.population = None
        self.profiles = None
        self.population_projection = None
        self.tax_projection = None
        self.growth_rate = None
        self.discount_rate = None
        self.country = None
        self.net_gov_wealth = 0
        self.net_gov_spendings = 0
        self.cohorts = None #A DataCohorts object
        self.aggregate_pv = None #An AccountingCohorts object
        self.percapita_pv = None #An AccountingCohorts object
        
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


    def set_profiles(self, dataframe):
        """
        Set profiles dataframe
        
        dataframe : pandas DataFrame
                    Dataframe conaining the profiles
        
        """
        self.profiles = dataframe
    
    def set_gov_spendings(self, G):
        """
        Set the value of unventilated spendings of the government
        
        G : Number
        """
        self.net_gov_spendings = G
    
    def set_gov_wealth(self, W):
        """
        Set the present value of the net government wealth
        """
        self.net_gov_wealth = W
    

    def set_discount_rate(self, r=0):
        """
        Set discount rate
        
        Parameters
        ----------
        
        r : float, default set to 0
            The discount rate
        
        """
        self.discount_rate = r
        
        
    def set_growth_rate(self, g=0):
        """
        Set discount rate
        
        Parameters
        ----------
        
        r : float, default set to 0
            The growth rate
        """
        self.growth_rate = g

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

#===============================================================================
# Set of methods to perform the simulation itself
#===============================================================================


    def create_cohorts(self):
        """
        Create cohorts according to population, tax and transfers,
        and state expenses projection    
        """
        population = self.population
        cohorts = Cohorts(data = population, columns = ['pop'])
        
        # Complete population projection
        year_length = self.population_projection["year_length"]
        method = self.population_projection["method"]        
        cohorts.population_project(year_length, method = method)
        
        # Generate discount factor and growth factor
        cohorts.gen_dsct(self.discount_rate)
        cohorts.gen_grth(self.growth_rate)

        # Fill profiles
        cohorts.fill(self.profiles)
        method = self.tax_projection["method"]
        rate = self.tax_projection["rate"]
        cohorts.proj_tax(rate=rate, method=method)

        # Project net taxes TOOD: see MainWindow widget
        self.cohorts = cohorts
        
    
    def create_present_values(self, typ):
        """
        Create aggregated and per capita present values of net transfers according to the given cohort
        and state expenses projection 
        """
        self.aggregate_pv = self.cohorts.aggregate_generation_present_value(typ, discount_rate = self.discount_rate)
        self.percapita_pv = self.cohorts.per_capita_generation_present_value(typ, discount_rate = self.discount_rate)


#===============================================================================
# Set of methods to manipulate the simulated data
#===============================================================================
    
    def extract_generation(self, dataframe, year, typ, age = None):
        """
        Returns a dataframe containning chosen data to follow the evolution of a given group over time.
        
        Parameters
        ----------
        year : Int
                A year of reference contained in the cohort.
        typ : Str
              A column or a list of columns of the cohort that one wants to follow
        age : Int
              Default is zero. The age of reference of the group one is interested in.       
        dataframe : pandas dataframe
        A data frame containing the relevant data. It has to be an attribute of simulation (either : cohorts, aggregate_pv or percapita_pv).
        
        Returns
        -------
        generation_cohort : a cohort dataframe with the data of the group of people 
                            whose given references belong to. 
        """      

        if year is None:
            raise Exception('a year of reference is needed')
        if year not in list(self.dataframe.index_sets['year']):
            raise Exception('The given year is not valid')
        year_min = array(list(self.dataframe.index_sets['year'])).min()
        year_max = array(list(self.dataframe.index_sets['year'])).max()
        if typ not in self._types:
            raise Exception('the given column is not in the cohort')
        
        #Normalizing the age if not given
        if age is None:
            age = 0

        pvm = self.xs(0, level='sex')
        pvf = self.xs(1, level='sex')
        
        #Creating lower bounds for the filter generation
        if age > 0:
            if year-age >= year_min:
                start_age = 0
                year_start = year - age
            else:
                start_age = age - (year - year_min)
                year_start = year_min
        else:
            start_age = age
            year_start = year

        #Creating upper bounds for filter_list
        if year + (100-age) >= year_max:
            year_end = year_max
            end_age = age + (year_max - year)
        else:
            year_end = year + 100 - age
            end_age = 100

        #Creating the filtering list
        filter_list = zip(range(start_age, end_age+1), range(year_start, year_end+1))
        
#         Generation the generation DataFrame
        generation_data_male = pvm.loc[filter_list, typ]
        generation_data_female = pvf.loc[filter_list, typ]
         
        pieces = [generation_data_male, generation_data_female]
        res =  concat(pieces, keys = [0,1], names = ["sex"] )
        res = res.reorder_levels(['age','sex','year'])
         
        generation_cohort = Cohorts(res)
        generation_cohort.columns = [typ]
        return generation_cohort


   
    def create_age_class(self, dataframe, step = 1):
        """
        Transform a filled cohort dataframe by regrouping 
        age indexies in age class indexies. The size of the age class is indicated by the step argument
        
        Parameters
        ----------
        step : Int
        The number of years included in the age class
        
        dataframe : pandas dataframe
        A data frame containing the relevant data. It has to be an attribute of simulation (cohorts, aggregate_pv, percapita_pv).
        
        Returns
        -------
        age_class : A DataFrame of the Cohorts class with age indexes replaced with class indexes with values being the mean of the age class
        """
        # Separating Men and Women
        pvm = self.dataframe.xs(0, level='sex')
        pvf = self.dataframe.xs(1, level='sex')
        pvm.reset_index(inplace = True)
        pvf.reset_index(inplace = True)
        
        #Transforming the age indexes
        serie = array(pvm.age)
        pvm['age'] = array((serie//step)*step)
        pvf['age'] = array((serie//step)*step)
            
        age_class_pvm = pvm.groupby(['age', 'year']).mean()
        age_class_pvf = pvf.groupby(['age', 'year']).mean()
        
        #Put back the dataframes together
        pieces = [age_class_pvm, age_class_pvf]
        age_class =  concat(pieces, keys = [0,1], names = ["sex"] )
        age_class = age_class.reset_index()
        age_class = age_class.set_index(['age', 'sex', 'year'])
        return age_class            

    def compute_ipl(self, typ):
        """
        Return a value of the intertemporal public liability. 
        The dataframe has to contain the aggregated present values of transfer in order 
        for the method to work correctly
        
        Parameters
        ----------
        typ : the column containing the data used in the calculation
        
        net_gov_wealth : the present value of the wealth of the government
        
        net_gov_spendings : the present value of unventilated government's spendings
        
        Returns
        -------
        
        ipl : float
            the value of the intertemporal public liability
        """

        year_min = array(list(self.aggregate_pv.index_sets['year'])).min()
        year_max = array(list(self.aggregate_pv.index_sets['year'])).max()
#         age_min = array(list(self.aggregate_pv.index_sets['age'])).min()
        age_max = array(list(self.aggregate_pv.index_sets['age'])).max()
        
        past_gen_dataframe = self.aggregate_pv.xs(year_min, level = 'year')
        past_gen_dataframe = past_gen_dataframe.cumsum()
        past_gen_transfer = past_gen_dataframe.get_value((age_max, 1), typ)

        
        future_gen_dataframe = self.aggregate_pv.xs(0, level = 'age')
        future_gen_dataframe = future_gen_dataframe.cumsum()
        future_gen_transfer = future_gen_dataframe.get_value((1, year_max), typ)
        print "check future_gen_transfer", future_gen_transfer
        #Note : do not forget to eliminate values counted twice
        ipl = past_gen_transfer + future_gen_transfer + self.net_gov_wealth - self.net_gov_spendings - past_gen_dataframe.get_value((0, 0), typ)
        return ipl
    
    
    def compute_gen_imbalance(self, typ):
        """
        Returns a list of indexes of the generationnal imbalance between the newborn of the reference year 
        and the unborn of the next year.
        
        Returns
        -------
        TODO: finish the doc
        
        """
        
        year_min = array(list(self.aggregate_pv.index_sets['year'])).min()
        year_max = array(list(self.aggregate_pv.index_sets['year'])).max()
#         age_min = array(list(self.aggregate_pv.index_sets['age'])).min()
        age_max = array(list(self.aggregate_pv.index_sets['age'])).max()
        
        #Calculating the past transfers for both genders then deducting the equilibrium future transfers
        
        past_gen_dataframe = self.aggregate_pv.xs(year_min, level = 'year')
        past_gen_dataframe = past_gen_dataframe.cumsum()
        past_gen_transfer = past_gen_dataframe.get_value((age_max, 1), typ)
        
        future_gen_transfer = self.net_gov_spendings - self.net_gov_wealth - past_gen_transfer
        print "check future_gen_transfer", future_gen_transfer
         
        #Computing the number of people of the unborn generation
        population_unborn_ma = self.cohorts.get_value((0,0, year_min+1), 'pop')
        population_unborn_fe = self.cohorts.get_value((0,1,year_min+1), 'pop')
        population_unborn = population_unborn_ma + population_unborn_fe
        
        #Reorganizing data to prepare the computation of mu_1
        population_dataframe = self.cohorts.filter_value(age = [0], year = range(year_min+1, year_max+1), typ='pop')
        population_dataframe.gen_actualization(self.growth_rate, self.discount_rate)
        population_dataframe = population_dataframe.unstack(level='sex')
        del population_dataframe[('actualization', 1)] #TODO : check if this line is necessary
        population_dataframe['unborn'] = population_unborn
        population_dataframe['mixed'] = population_dataframe[('pop', 0)] + population_dataframe[('pop', 1)]
        print population_dataframe.head()
        population_dataframe[('actualization', 0)] *= population_dataframe['mixed']/population_dataframe['unborn']

        print "check column combination"
        print population_dataframe[("actualization", 0)]
        
        #Computing the coefficient mu_1
        population_dataframe = population_dataframe.cumsum()        
        mu_1 = population_dataframe.get_value((0,year_max), ('actualization', 0))
        print "mu_1 = ", mu_1
         
        #Computing the final imbalance coefficients
        population_unborn = population_unborn_ma + population_unborn_fe
        n_1 = future_gen_transfer/(mu_1*population_unborn) # = percapita_future_gen_transfer
        n_0 = (self.percapita_pv.get_value((0, 0, year_min), typ)/2 + 
                               self.percapita_pv.get_value((0, 1, year_min), typ)/2) # = actual_gen_transfer
        print "n_0", n_0 
        imbalance = n_1 - n_0
        imbalance_ratio = n_1/n_0
        coefficients = [n_1, imbalance, imbalance_ratio]
        return coefficients



if __name__ == '__main__':
    pass
