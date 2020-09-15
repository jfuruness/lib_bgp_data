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

from ..parser import Parser


@pytest.mark.base_classes
class Test_Parser:
    """Tests all functions within the Parser class."""

    @pytest.mark.skip(reason="New hire work")
    def test_init_subclass(self):
        """Test the __init_sublcass method.

        Make sure that all inherited classes are in the parsers list.
        """

    @pytest.mark.skip(reason="New hire work")
    def test__innit__(self):
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
        assert not os.listdir(path)
        assert not os.listdir(csv_dir)
       
        # reset, otherwise logging can only be configured once
        logging.root.handlers = []

        # with kwargs
        stream_level = logging.ERROR 
        path = './foo'
        csv_dir = './csv'
        sp = Subparser(stream_level=stream_level, path=path, csv_dir=csv_dir)
        assert logging.root.level == logging.ERROR
        assert not os.listdir(path)
        assert not os.listdir(csv_dir)

    def assert_cleanup(self, parser):
        assert not os.path.exists(parser.path)
        assert not os.path.exists(parser.csv_dir)


    @pytest.mark.skip(reason="New hire work")
    def test_run(self):
        """Tests the run function

        One test where there is an exception - do not raise, but log
            -test should still clean out dirs
        One test should be where there is no exception
            -tests should still clean out dirs
        """

    @pytest.mark.skip(reason="New hire work")
    def test_end_parser(self):
        """tests end_parser func

        Make's sure that dirs are cleaned out. Don't worry about the time.
        """

    @pytest.mark.skip(reason="New hire work")
    def test_argparse_call(self):
        """Tests argparse call method.

        See how __main__.py uses this function. Read the docstrings.
        Attempt to have a class be able to be called with this. Make
        sure that it works.
        """

        # Add Foo_Parser to an existing parser file
        # Run it, and assert its _run function is called

        # this gets us up to /base_classes
        p = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

        p = os.path.join(os.path.dirname(p), 'bgpstream_website_parser',
            'bgpstream_website_parser.py')

        with open(p, 'r') as f:
            og_cpy = f.read()

        sample = 'sample.txt'
        code = ("class Foo_Parser(Parser):\n\tdef _run(self):\n\t\t"
                f"with open('{sample}', 'w+') as f: f.write('abc')")

        with open(p, 'a') as f:
            f.write('\n')
            f.write(code)

        os.system('lib_bgp_data --foo_parser')
        with open(sample, 'r') as f:
            assert f.read() == 'abc'

        with open(p, 'w') as f:
            f.write(og_cpy)
        os.remove(sample)
