# -*- coding:utf-8 -*-
# Copyright © 2012 Clément Schaff
# Based on gamatnew.m by Philip Oreopoulos, 1999

'''
Created on May 21, 2012

@author: Clément Schaff
'''

from __future__ import division
import numpy as np
from numpy import tile as repmat
from numpy import transpose as permute-
from numpy import sum
import os

DIR= 'data_us'

def get_data(fname):
    datafile = os.path.join(DIR, fname)
    data = np.loadtxt(datafile)
    return data
    

#==================================#
#  Parameter Settings and Switches #
#==================================#

# policy adjustment parameters:

switch04 = 1                # policy adjustment for all gen. if 1
startingyear = 1995        # starting year of policy if currentgen=1
                                # note: this parameter is not set
                        # at the moment, the policy change starts
                        # in the base year - this can easily be changed

class Transfers:
    oasdi           = 0
    medicare        = 1
    medicaid        = 2
    ui              = 3
    general_welfare = 4
    afdc            = 5
    food_stamps     = 6
    education       = 7

class Taxes:
    labour_income_taxes     = 8
    fica_taxes              = 9
    excise_taxes            = 10
    capital_income_taxes    = 11
    infarmarginal_capital   = 12
    monetary_base           = 13
    property_taxes          = 14

# matrix of tax/transfer category numbers
transfer_cats = [Transfers.oasdi,
                 Transfers.medicare,
                 Transfers.medicaid,
                 Transfers.ui,
                 Transfers.general_welfare,
                 Transfers.afdc,
                 Transfers.food_stamps,
                 Transfers.education
                 ] 


tax_cats = [Taxes.labour_income_taxes, 
            Taxes.fica_taxes, 
            Taxes.excise_taxes,
            Taxes.monetary_base, 
            Taxes.property_taxes
            ]

nb_transfer = len(transfer_cats)
nb_tax = len(tax_cats)
#! pour memoire: les nouveaux codes sont décalé de 1 (convention python)
# Codes are:
#  Taxes                                Transfers

# 9  Labour Income Taxes            1  OASDI
# 10 FICA Taxes                     2  Medicare        
# 11 Excise Taxes                   3  Medicaid 
# 12 Cap. Income Taxes              4  UI
# 13 Inframarginal Cap.             5  General Welfare
# 14 Monetary Base                  6  AFDC
# 15 Property Taxes                 7  Food Stamps
#                                   8  education
#                                   
#                                   16 Fed. Government Cons.
#                                   17 State Government Cons.

DEBT = 2078610000000

switch01 = 0     # omits cap. tax. adj. if '1'
switch02 = 1     # also calculates m & f together
switch05 = 0     # equalize burdens experiment
switch06 = 2     # specifies aggregate projections (1=low, 2=med, 3=high, 4=with edu)
switch07 = 2     # specifies demographic projections :  (1=low, 2=med, 3=high)
switch08 = 1     # seignorage adjustment                        

# interest rate
r = 0.060
# growth rate
g = 0.012
nb_ages =101
ages = np.arange(nb_ages)
nb_types = 17         # note: types 16, 17 are govcon
types = np.arange(nb_types)
nb_sex = 2
sexes = np.arange(nb_sex)

base_year     = 1995            
last_year     = 2100            
proj_year     = 2070            

# these definitions make the notation easier to follow when working with column and row numbers
nb_proj = proj_year - base_year + 1
nb_last = last_year - base_year + 1
nb_remain = last_year - proj_year + 1

prj_year    = proj_year - base_year + 1
lst_year    = last_year - base_year + 1
remain_year = last_year - proj_year + 1

#=====================================#
# Load in data files and conform data #
#=====================================#

if switch07 == 1:
    POPM = get_data('POPMLOW.txt')
    POPF = get_data('POPFLOW.txt')
elif switch07 == 2:
    POPM = get_data('POPMMED.txt')
    POPF = get_data('POPFMED.txt')
elif switch07 == 3:
    POPM = get_data('POPMHIGH.txt')
    POPF = get_data('POPFHIGH.txt')
else:
    raise Exception('swithch07 should be 1, 2 or 3')

# drop first column (years)
POPM = POPM[:,1:]        
POPF = POPF[:,1:]        

# loads relative profile data indexed by TYPE x AGE    (Male and Female)
RPM = get_data('RPM.txt') 
RPF = get_data('RPF.txt') 

# drop 1st col (type) and 2nd col (year)
RPM = RPM[:,2:]
RPF = RPF[:,2:]


#! compute inflation from the monetary base
RPM[Taxes.monetary_base, 0] = 0
RPF[Taxes.monetary_base, 0] = 0

# TODO: this comes from the original code but is really weird!!!!
for i in range(1,nb_ages):
    RPM[Taxes.monetary_base,i] = RPM[Taxes.monetary_base, i] - RPM[Taxes.monetary_base, i-1]
    RPF[Taxes.monetary_base,i] = RPF[Taxes.monetary_base, i] - RPF[Taxes.monetary_base, i-1]

# Normalize with respect to Male of age 40
rm40 = RPM[Taxes.monetary_base, 39]

RPM[Taxes.monetary_base, :] = RPM[Taxes.monetary_base, :] / rm40
RPF[Taxes.monetary_base, :] = RPF[Taxes.monetary_base, :] / rm40

# RP matrix is relative profiles with dims RP(age,year,type,sex), and 
# the year goes from baseyear to projyear  
RP = np.zeros((nb_ages, nb_proj, nb_types, nb_sex))

RP[:, :, :, 0] = repmat(np.transpose(RPM[:,:,np.newaxis], [1, 2, 0]), [1, nb_proj, 1])
RP[:, :, :, 1] = repmat(np.transpose(RPF[:,:,np.newaxis], [1, 2, 0]), [1, nb_proj, 1])

if  switch06 == 1:
    AGG = get_data('AGGLO.txt')
    g = 0.07
elif switch06 == 2:
    AGG = get_data('AGGMED.txt')
    g = 0.012
elif switch06 == 3:
    AGG = get_data('AGGHI.txt')
    g = 0.017
elif switch06 == 4:
    AGG = get_data('AGGEDUC.txt')
    g = 0.012
else:
    raise Exception('switch06 sould be 1, 2, 3 or 4')

# Aggregate matrix has dimensions YEAR x TYPE. first column  displaying the year is removed
# NOTE: the last two columns contain the values of federal and state government consumption

# drop first column (years)
AGG = AGG[:,1:]

#---------------------------------------------------------------#
# Gets discount and growth matricies with dims AGE x YEAR, from #
# baseyear to lastyear: (1+g)**0, (1+g)**1, (1+g)**2, ...          #
#---------------------------------------------------------------#
DSCT = np.zeros((nb_ages, nb_last))
GRTH = np.zeros((nb_ages, nb_last))

for i in range(nb_last):
    DSCT[:,i] = np.ones(nb_ages)/(1+r)**i
    GRTH[:,i] = np.ones(nb_ages)*(1+g)**i

#==================================================#
# Converts Aggregates to billions of U.S. dollars  #
# and defines some variables                       #
#==================================================#

AGG = 1000000000*AGG

#===============================================#
#                                               #
# Capital Income Tax Adjustment (If switch01=0) #
#                                               #            
#===============================================#

qcap     = 0.11100
delcap     = 0.00111

if switch01 == 1:
    AGG[:, Taxes.infarmarginal_capital] = 0

for i in  range(nb_proj):
    AGG[i, Taxes.capital_income_taxes] = AGG[i,Taxes.capital_income_taxes] - (delcap*AGG[0,Taxes.infarmarginal_capital])*((1+g)**i)

AGG[:, Taxes.infarmarginal_capital] = qcap*AGG[:, Taxes.infarmarginal_capital]

#=======================================================#
#                                                       #
# Calculates from data per capita amounts of taxes paid #
# and transfers received for each age group by year     #
#                                                       #
#        PERCAP matrix is (age,year,type,sex)           #
#                                                       #
#=======================================================#

# sum over ages for each (type, year)
print POPM[:,:].T.shape
SUMS = np.dot(RPM,POPM[:nb_proj,:].T)  + np.dot(RPF, POPF[:nb_proj,:].T)

# units of profiles
UNITIES = AGG/SUMS.T

UNITIES = repmat(permute(UNITIES[:,:,np.newaxis],[2,0,1]),[nb_ages,1,1])

PERCAP = np.zeros((nb_ages, nb_ages+ 1, nb_types, nb_sex))

PERCAP[:, :nb_proj, :, 0] = repmat(permute(RPM[:,:,np.newaxis],[1,2,0]),[1,nb_proj,1]) * UNITIES
PERCAP[:, :nb_proj, :, 1] = repmat(permute(RPF[:,:,np.newaxis],[1,2,0]),[1,nb_proj,1]) * UNITIES

PERCAP[:, nb_proj:nb_ages+1, :, :] = (repmat(PERCAP[:,[nb_proj-1],:,:],[1,nb_ages-nb_proj+1,1,1]) * 
                                     repmat(GRTH[:,1:(nb_ages-nb_proj+2), np.newaxis, np.newaxis],[1,1,nb_types,2])
                                     )
print PERCAP.shape 
del SUMS, UNITIES

#==================================================#
#                                                  #
# converts values to present value, and calculates #
# generational accounts for living age groups      #
#                                                  #
#==================================================#
rw, cl = POPM.shape

POP = np.zeros((cl, rw, 1, nb_sex))
POP[:,:,0,0] = POPM.T
POP[:,:,0,1] = POPF.T

PVTOTALS = PERCAP * repmat(DSCT[:, :nb_ages+1, np.newaxis, np.newaxis],[1, 1, nb_types, 2]) * repmat(POP[:, :nb_ages+1, :, :],[1, 1, nb_types, 1])

TaxTransfers = np.zeros((nb_ages, nb_types-2, nb_sex))
for typ in types[:-2]:
    for age in ages:
        TaxTransfers[age, typ, 0] = sum(np.diag(PVTOTALS[:, ages, typ, 0], - age)) / POP[age,0,0,0]
        TaxTransfers[age, typ, 1] = sum(np.diag(PVTOTALS[:, ages, typ, 1], - age)) / POP[age,0,0,1]

GABEFORE = sum(TaxTransfers, 1)    # sums along the rows in AVERAGES
GAFUTUREB = GABEFORE[0,:]*(1+g)

#==================================================#
#                                                  #
# calculates males and females together if         #
# switch02=1                                       #
#                                                  #
#==================================================#

if switch02 == 1:
    MFTOTALS = sum(PVTOTALS, 3)
    MFPOP = sum(POP[:, :2, 0, :], 2)
    TAXTRANSBEFORE = np.zeros((nb_ages, nb_types, nb_sex + 1))
    for typ in types:
        for age in ages:
            TAXTRANSBEFORE[age,typ,2] = sum(np.diag(MFTOTALS[:, ages, typ], -age)) / MFPOP[age,0]

    GABEFORE = np.hstack((GABEFORE, np.expand_dims(sum(TAXTRANSBEFORE[:,types[:-2],2],1),1)))

#============================================#
#                                            #
# calculate gap if no policy change          #
#                                            #
#============================================#

# The gap is the debt -
# the sum of all PV net payments for living generations -
# the PV net payments for future generations up to 2200 -
# the PV net payments for future generations extended out to infinity

netpvtaxes = (sum(sum(sum(sum(PVTOTALS[:,ages,:,:])))) + 
              sum(sum(sum(sum(repmat(PERCAP[:,[nb_ages],:,:], [1,nb_last-nb_ages,1,1]) *
                              repmat(GRTH[:,:nb_last-nb_ages, np.newaxis, np.newaxis], [1,1,nb_types,2]) *
                              repmat(DSCT[:,nb_ages:nb_last, np.newaxis, np.newaxis], [1,1,nb_types,2]) *
                              repmat(POP[:,nb_ages:nb_last,:,:], [1,1,nb_types,1])))))
              +
              sum(sum(sum(sum(PERCAP[:,nb_ages,:,:] *
                              repmat(GRTH[:,nb_last-nb_ages-1, np.newaxis, np.newaxis], [1,1,nb_types,2]) *
                              repmat(DSCT[:,nb_last-1, np.newaxis, np.newaxis], [1,1,nb_types,2]) *
                              repmat(POP[:,nb_last-1,:,:], [1,1,nb_types,1]))))) *
              (1+g)*(1/(1-((1+g)/(1+r))))
              )


govgap = DEBT - netpvtaxes


#==============================================================#
#                                                              #
# estimate percentage increase/decrease of tax/transfer types  #
# specified to eliminate gap.                                  #
#                                                              #
#    calculated for FUTURE generations only                    #
#                                                              #
#==============================================================#

# the percentage increase in particular tax/transfer programs is
# caclulated by summing all the PV payments/receipts of these
# programs for future generations, out to infinity, and calculating
# how much increase is required to remove the gap

# we calculate for tax and transfers seperately

# NOTE: the 'triu,1' command keeps the upper triangular portion of the 
# PERCAP matrix, shifted to the right one, which is the PV TOTALS for 
# future generations between 1994 and 2094.  The rest of the matrix 
# (for the percap amounts for living generations) become zero

tax_total = np.zeros(nb_tax)
j = 0
for tax_cat in tax_cats:
    TMP = PERCAP[:, nb_ages, tax_cat, :]

    tax_total[j] = (sum(sum(sum(np.triu(PVTOTALS[:, ages,tax_cat,0], 1)))) +
                    sum(sum(sum(np.triu(PVTOTALS[:, ages,tax_cat,1], 1)))) +
                    sum(sum(sum(sum(repmat(TMP[:,np.newaxis, np.newaxis, :],[1, nb_last - nb_ages, 1, 1]) *
                                    repmat(GRTH[:, :nb_last - nb_ages, np.newaxis, np.newaxis], [1,1,1,2]) *
                                    repmat(DSCT[:, nb_ages:nb_last, np.newaxis, np.newaxis], [1,1,1,2]) *
                                    POP[:, nb_ages:nb_last, :, :]))))
                    +
                    sum(sum(sum(sum(TMP[:,np.newaxis, np.newaxis, :] *
                                    repmat(GRTH[:,nb_last-nb_ages-1, np.newaxis, np.newaxis, np.newaxis],[1,1,1,2]) *
                                    repmat(DSCT[:,nb_last-1, np.newaxis, np.newaxis, np.newaxis],[1,1,1,2]) *
                                    POP[:,[nb_last-1],:,:])))) *
                    (1+g)*(1/(1-((1+g)/(1+r))))
                    )
    j +=1

transfer_total = np.zeros(nb_transfer)
j = 0
for transfer_cat in transfer_cats:
    TMP = PERCAP[:, nb_ages, transfer_cat, :]
    transfer_total[j] = -(sum(sum(sum(np.triu(PVTOTALS[:,ages,transfer_cat,0],1)))) +
                          sum(sum(sum(np.triu(PVTOTALS[:,ages,transfer_cat,1],1)))) +
                          sum(sum(sum(sum(repmat(TMP[:,np.newaxis, np.newaxis, :], [1,nb_last-nb_ages,1,1]) *
                                          repmat(GRTH[:,:nb_last-nb_ages, np.newaxis, np.newaxis], [1,1,1,2]) *
                                          repmat(DSCT[:,nb_ages:nb_last, np.newaxis, np.newaxis], [1,1,1,2]) *
                                          POP[:,nb_ages:nb_last,:,:])))) +
                          sum(sum(sum(sum(TMP[:,np.newaxis, np.newaxis, :] *
                                          repmat(GRTH[:,nb_last-nb_ages-1, np.newaxis, np.newaxis, np.newaxis], [1,1,1,2]) *
                                          repmat(DSCT[:,nb_last-1, np.newaxis, np.newaxis, np.newaxis], [1,1,1,2]) *
                                          POP[:,[nb_last-1],:,:])))) *
                        (1+g)*(1/(1-((1+g)/(1+r))))
                        )
    j += 1

# NOTE: we subtract to make the aggregate positive
percentagechange = govgap / ( sum(tax_total) + sum(transfer_total) )
print 'percentage change: %f' % percentagechange
#==============================================================#
#                                                              #
# policy adjustment for living generations if switch04=1       #
#                                                              #
#==============================================================#

# simply adds on the additional PV net tax payments for living generations
# and then calculates the percentage change again

if switch04 == 1:
    j = 0
    for tax_cat in tax_cats:
        tax_total[j] += (sum(sum(sum(np.tril(PVTOTALS[:, ages,tax_cat, 0])))) + 
                        sum(sum(sum(np.tril(PVTOTALS[:, ages,tax_cat, 1]))))
                        )
        j += 1

    j = 0
    for transfer_cat in transfer_cats:
        transfer_total[j] += -(sum(sum(sum(np.tril(PVTOTALS[:,ages,transfer_cat, 0])))) +
                              sum(sum(sum(np.tril(PVTOTALS[:,ages,transfer_cat, 1]))))
                              )
        j +=1

    print tax_total
    print transfer_total
    percentagechange = govgap / (sum(tax_total) + sum(transfer_total))
    print 'percentage change: %f' % percentagechange

#==============================================================#
#                                                              #
# computes new generational accounts, after policy change      #
# for future generations affected only...                      #
#                                                              #
#==============================================================#

FutureTaxTrans = np.zeros((nb_types, nb_sex+1))

if switch04 == 0:
    TAXTRANSAFTER = TAXTRANSBEFORE
    GAAFTER = GABEFORE

    for tax_cat in tax_cats:
        for sex in sexes:
            PERCAP[:,ages+1,tax_cat,sex] = (np.tril(PERCAP[:,ages+1,tax_cat,sex]) + 
                                                np.triu(PERCAP[:,ages+1,tax_cat,sex],1) * 
                                                (1+percentagechange)
                                                )

    for transfer_cat in transfer_cats:
        for sex in sexes:
            PERCAP[:,:,transfer_cat,sex] = (np.tril(PERCAP[:,:,transfer_cat,sex]) +
                                              np.triu(PERCAP[:,:,transfer_cat,sex],1) *
                                              (1-percentagechange)
                                              )
    PVTOTALSF = (PERCAP[:,1:102,:,:] *
                 repmat(DSCT[:,:nb_ages, np.newaxis, np.newaxis],[1,1,nb_types,2]) *
                 repmat(POP[:,1:nb_ages+1,:,:],[1,1,nb_types,1])
                 )

    for typ in types:
        for sex in sexes:
            FutureTaxTrans[typ,sex] = sum(np.diag(PVTOTALSF[:,:,typ,sex])) / POP[0,1,0,sex]

    GAFUTUREA = sum(FutureTaxTrans[:-2,:2]) / (1+g)


#==============================================#
# combines for males and females if switch02=1 #
#==============================================#

    if switch02 == 1:
        MFTOTALS=sum(PVTOTALS,3)
       
        for typ in types:
            FutureTaxTrans[typ, 2] = sum(np.diag(MFTOTALS[:,:,typ])) / MFPOP[0,1]
    
        GAFUTUREA = np.hstack((GAFUTUREA, np.expand_dims(sum(FutureTaxTrans[:-2, 2]) / (1+g),1)))

#================================================#
#                                                #
# Computes new GAs for all, if switch04=1        #
#                                                #
#================================================#

elif switch04 == 1:
    for tax_cat in tax_cats:
        PERCAP[:,:,tax_cat,:] = PERCAP[:,:,tax_cat,:]*(1+percentagechange)

    for transfer_cat in transfer_cats:
        PERCAP[:,:,transfer_cat,:] = PERCAP[:,:,transfer_cat,:] * (1-percentagechange)

    PVTOTALS = PERCAP * repmat(DSCT[:, :nb_ages+1, np.newaxis, np.newaxis], [1, 1, nb_types, 2]) * repmat(POP[:,:nb_ages+1,:,:], [1,1,nb_types,1])


    TAXTRANSAFTER = np.zeros((nb_ages, nb_types, nb_sex + 1))
    for typ in types:
        for age in ages: 
            for sex in sexes:
                TAXTRANSAFTER[age,typ,sex] = sum(np.diag(PVTOTALS[:,ages,typ,sex],-age)) / POP[age,0,0,sex]
    
    GAAFTER = np.zeros((nb_ages, nb_sex))
    for sex in sexes:
        a = sum(TAXTRANSAFTER[:,:-2,sex], 1)
        GAAFTER[:, sex] = sum(TAXTRANSAFTER[:,:-2,sex], 1)

# same now for future generations (the cohort born after
# the base year for comparison purposes

    PVTOTALSF = (PERCAP[:,2:102,:,:] *
                 repmat(DSCT[:,ages], [1,1,nb_types,2]) *
                 repmat(POP[:,2:nb_ages+1,:,:], [1,1,nb_types,1])
                 )

    for typ in types:
        for sex in sexes:
            FutureTaxTrans[typ,sex] = sum(np.diag(PVTOTALSF[:,:,typ,sex])) / POP[1,2,1,sex]

    GAFUTUREA = sum(FutureTaxTrans[1:15,:2]) / (1+g)


#GAFUTUREA = GAAFTER(1,:)

#================================================================#
# calculates GAs with males and females together if switch02 = 1 #
#================================================================#

    if switch02 == 1:
        MFTOTALS = sum(PVTOTALS, 3)
        MFPOP = sum(POP[:, :2, 0, :], 2)
        TAXTRANSAFTER = np.zeros((nb_ages, nb_types, nb_sex + 1))

        for typ in types:
            for age in ages:
                TAXTRANSAFTER[age,typ,2] = sum(np.diag(MFTOTALS[:, ages, typ], -age)) / MFPOP[age,0]

        GAAFTER = np.hstack((GAAFTER, np.expand_dims(sum(TAXTRANSAFTER[:,types[:-2],2],1),1)))
    
    # GAFUTUREA[0,2] = GAAFTER[0,2]/(1+g)

#===========================================#
# prints males GAs by 5 year age categories #
#===========================================#

#! format bank
# print GAAFTER[:,0]/1000
print GAFUTUREA[0,0]/1000


