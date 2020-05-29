#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__authors__ = ["Matt Jaccino", "Justin Furuness"]
__credits__ = ["Matt Jaccino", "Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


import pytest
import os
from ..file import File


@pytest.mark.base_classes
class Test_File:
    """Tests the functions within the File class"""

    def file_params():
        params = []
        for path in ['.','/' +  os.getcwd().split('/')[1]]:
            for csv_dir in ['/tmp/', os.getcwd()]:
                for url in ['no_ext', 'file.py']:
                    for num in [False, '2']:
                        ext = '.py' if url == 'file.py' else ''
                        n = num if num else '1'
                        expected = path + '/' + n + ext
                        params.append((path, csv_dir, url, num, expected))
        return params
        
    @pytest.mark.parametrize('path, csv_dir, url, num, expected', file_params())
    def test_init(self, path, csv_dir, url, num, expected):
        """Tests the init func of the file

        Make sure path is what you expect.
        """
        # testing parameters
        # path: current directory or one below root
        # csv_dir: tmp directory or current directory
        # url: no extension or .py extension
        # num: default or 2
        if num:
            f = File(path, csv_dir, url, num)
        else:
            f = File(path, csv_dir, url)
        assert f.path == expected

    def test_lt(self):
        """Tests the comparator operator for sorting"""

        # create a small file and large file
        sm = File('.', '/tmp/', 'file.txt')
        big = File('.', '/tmp/', 'file.txt', 2)

        with open(sm.path, 'w+') as small_file, open(
                  big.path, 'w+') as big_file:
            for i in range(4):
                small_file.write(str(i))
            for i in range(4 ** 4):
                big_file.write(str(i))

        assert sm < big

        # clean-up
        os.remove(sm.path)
        os.remove(big.path)
            
