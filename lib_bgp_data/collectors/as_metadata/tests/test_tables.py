#!/usr/bin/env python3
# -*- coding: utf-8 -*-


__author__ = "Samarth Kasbawala"
__credits__ = ["Samarth Kasbawala"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import pytest

from ..tables import ASN_Metadata_Table
from ....utils.database import Generic_Table_Test


@pytest.mark.asn_lookup
class Test_ASN_Metadata_Table(Generic_Table_Test):
    """Tests all table function for asn lookup class"""

    table_class = ASN_Metadata_Table

