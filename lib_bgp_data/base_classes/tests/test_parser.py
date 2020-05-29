#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains tests for the parser.py file.
For specifics on each test, see the docstrings under each function.
"""


__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import pytest
import os
import logging
from ...utils import utils
from ..parser import Parser


@pytest.mark.base_classes
class Test_Parser:
    """Tests all functions within the Parser class."""

    def test_init_subclass(self):
        """Test the __init_sublcass method.

        Make sure that all inherited classes are in the parsers list.
        """
        class Foo(Parser):
            def _run():
                pass

        assert Foo in Parser.parsers

    def test__init__(self):
        """Tests init function.

        Should have a section.
        Logging should be configured.
        path and csv directories should be created and empty
        should fail if _run not present, and vice versa.
        """
        class Foo(Parser):
            pass
        
        with pytest.raises(AssertionError):
            f = Foo()

        # defaults
        class Subparser(Parser):
            def _run(self):
                pass

        sp = Subparser()
        assert sp.kwargs['section'] == 'test'
        assert logging.root.level == logging.INFO
        path = '/tmp/test_Subparser'
        csv_dir = '/dev/shm/test_Subparser'
        assert len(os.listdir(path)) == 0
        assert len(os.listdir(csv_dir)) == 0
       
        # reset, otherwise logging can only be configured once
        logging.root.handlers = []

        # with kwargs
        stream_level = logging.ERROR 
        path = './foo'
        csv_dir = './csv'
        sp = Subparser(stream_level=stream_level, path=path, csv_dir=csv_dir)
        assert logging.root.level == logging.ERROR
        assert len(os.listdir(path)) == 0
        assert len(os.listdir(csv_dir)) == 0

    def assert_cleanup(self, parser):
        assert not os.path.exists(parser.path)
        assert not os.path.exists(parser.csv_dir)

    def test_run(self):
        """Tests the run function

        One test where there is an exception - do not raise, but log
            -test should still clean out dirs
        One test should be where there is no exception
            -tests should still clean out dirs
        """
        class Foo(Parser):
            def _run():
                raise Exception
        f = Foo()
        f.run()

        class Subparser(Parser):
            def _run():
                pass
        sp = Subparser()
        sp.run()
        
        for parser in [f, sp]:
            self.assert_cleanup(parser)

    def test_end_parser(self):
        """tests end_parser func

        Make's sure that dirs are cleaned out. Don't worry about the time.
        """
        class Foo(Parser):
            def _run(self):
                pass
        f = Foo()
        f.end_parser(utils.now())
        self.assert_cleanup(f)

        path = './foo'
        csv_dir = './csv'
        f = Foo(path=path, csv_dir=csv_dir)
        f.end_parser(utils.now())
        self.assert_cleanup(f)

    def test_argparse_call(self):
        """Tests argparse call method.

        See how __main__.py uses this function. Read the docstrings.
        Attempt to have a class be able to be called with this. Make
        sure that it works.
        """
        # This is the only way I've been able to to get it work
        # It would not work defining a class here
        # or writing a class in a new file
        path = '../../bgpstream_website_parser/bgpstream_website_parser.py'
        with open(path, 'r') as f:
            og_cpy = f.read()

        sample = 'sample.txt'
        code = ("class Foo_Parser(Parser):\n\tdef _run(self):\n\t\t"
                f"with open('{sample}', 'w+') as f: f.write('abc')")

        with open(path, 'a') as f:
            f.write('\n')
            f.write(code)

        os.system('lib_bgp_data --foo_parser')
        with open(sample, 'r') as f:
            assert f.read() == 'abc'

        with open(path, 'w') as f:
            f.write(og_cpy)
        os.remove(sample)
