#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import pytest

from ..tables import Unique_Prefix_Origins_Table, ROV_Validity_Table
from ...database import Generic_Table_Test

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


@pytest.mark.skip(reason="new hires will code this")
@pytest.mark.rpki_validator
class Test_Unique_Prefix_Origins_Table(Generic_Table_Test):

    table_class = Unique_Prefix_Origins_Table

    @pytest.mark.skip(reason="new hires will code this")
    def test_fill_table_func(self):
        """Tests fill table function.

        should be able to take in any table name as input
        Should error if table is empty
        Checks distinct
        That's all. Inherited test funcs take care of the rest.
        """

        pass

@pytest.mark.skip(reason="new hires will code this")
@pytest.mark.rpki_validator
class Test_ROV_Validity_Table(Generic_Table_Test):

    table_class = ROV_Validity_Table
