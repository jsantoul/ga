
# -*- coding:utf-8 -*-
#
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)

import os

from src import SRC_PATH
country = "france"
DEFAULT_POPULATION_FILENAME = os.path.join(SRC_PATH, 'countries', country, 'sources', 'data_fr', 'proj_pop_insee', 'proj_pop.h5')

DEFAULT_PROFILES_FILENAME = os.path.join(SRC_PATH, 'countries', country, 'sources', 'data_fr','profiles.h5')