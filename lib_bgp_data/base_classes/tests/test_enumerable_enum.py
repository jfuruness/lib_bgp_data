#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the enumerable_enum.py file.
For specifics on each test, see docstrings under each function.
"""

import pytest
from ..enumerable_enum import Enumerable_Enum


__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

@pytest.mark.base_classes
class Test_Enumerable_Enum:
    """Tests all local functions within the Enumerable_enum class."""

    def test_list_values(self):
        """Test that the values of the enum are listed"""

        class Foo(Enumerable_Enum):
            STRING = 'x'
            INT = 1
            FLOAT = 3.14
            LIST = ['x', 'y', 'z', 1, 2, 3]

        assert Foo.list_values() == ['x', 1, 3.14, ['x', 'y', 'z', 1, 2, 3]]
