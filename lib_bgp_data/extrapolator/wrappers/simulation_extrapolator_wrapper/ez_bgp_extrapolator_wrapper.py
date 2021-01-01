#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Let's take a moment of silence for the lack of docs"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import logging

import psycopg2

from .tables import Simulation_Extrapolator_Results_Table
from .tables import Simulation_Extrapolator_Forwarding_Table

from .simulation_extrapolator_wrapper import Simulation_Extrapolator_Wrapper

from ....utils.base_classes import Parser
from ....utils.database import Database
from ....utils import utils


class EZ_BGP_Extrapolator_Wrapper(Simulation_Extrapolator_Wrapper):
    """This class runs the extrapolator.

    In depth explanation at the top of module.
    """

    __slots__ = []

    branch = "ezbgpsec-script-integration"

    def append_extra_bash_args(self, bash, arg_1, arg_2, arg_3, arg_4, arg_5):
        if arg_1 is not None:
            bash += f" --local-thresh {arg_1}"
        if arg_2 is not None:
            bash += f" --global-thresh {arg_2}"
        return bash
