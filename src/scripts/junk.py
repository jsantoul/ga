# -*- coding:utf-8 -*-

'''
Created on 21 juin 2013

@author: Jérôme SANTOUL
'''
from __future__ import division
from pandas import HDFStore, DataFrame
from pandas.io.parsers import ExcelFile

from src.lib.cohorts.data_cohorts import DataCohorts
from src.lib.hypothesis_set import HypothesisSet

from src import SRC_PATH
import os
from src.lib.simulation import Simulation


def test():
    
    simulation = Simulation(profiles=DataFrame(), country='France')
    population = DataFrame()
    simulation.set_population(population, 'alternatif')
    print simulation.reference_scenario.__dict__
    
    

if __name__ == '__main__':
    test()