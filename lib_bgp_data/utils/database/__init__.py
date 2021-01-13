#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This subpackage contains the functionality to interact with a database.

database generically interacts with db. generic_table has specific table funcs
that may be useful. See README for detailed explanation
"""

__author__ = "Justin Furuness", "Matt Jaccino"
__credits__ = ["Justin Furuness", "Matt Jaccino"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from .config import Config
from .database import Database
from .generic_table import Generic_Table
from .postgres import Postgres
from .tests.generic_table_test import Generic_Table_Test
