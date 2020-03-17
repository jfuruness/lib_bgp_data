#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import pytest

from ..tables import Hijacks_Table, Leaks_Table, Outages_Table
from ...database import Generic_Table_Test

class Data_Table_Test(Generic_Table_Test):
    """This class is to be inherited by the other three table testing classes

    It should contain functions for create index and delete duplicates.
    """

    @pytest.mark.skip(reason="New hires work")
    def test_create_index(self):
        """Tests the create index function

        Make sure index is created
        Make sure if ran twice just one index is there
        """

        pass

    @pytest.mark.skip(reason="New hire work")
    def test_delete_duplicates(self):
        """Tetsts the delete duplicates function

        Should delete all duplicates from the table.
        Prob insert dummy data to check this.
        """

        pass

@pytest.mark.bgpstream_website_parser
class Test_Hijacks_Table(Data_Table_Test):

    table_class = Hijacks_Table

@pytest.mark.bgpstream_website_parser
class Test_Leaks_Table(Data_Table_Test):

    table_class = Leaks_Table

@pytest.mark.bgpstream_website_parser
class Test_Outages_Table(Data_Table_Test):

    table_class = Outages_Table
