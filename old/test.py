'''
Created on Jun 5, 2012

@author: Utilisateur
'''
from __future__ import division

from pandas import DataFrame, read_csv
from numpy import NaN, array, arange


x = arange(2071,1994,-1)
print x

#data = read_csv('../data_us/essay.csv', index_col = [0,1,2])
#
#data['tmp'] = NaN
#
#grouped = data.groupby(level = [ 'year'])
#
#a = arange(6)
#print a
#out = grouped['tmp'].transform(lambda x: 3+  x.year)
#
#print out.to_string()

