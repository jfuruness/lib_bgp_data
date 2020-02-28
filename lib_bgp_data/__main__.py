#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module runs all command line arguments"""

from argparse import ArgumentParser, Action
from sys import argv
from .mrt_parser import MRT_Parser
from .relationships_parser import Relationships_Parser

__authors__ = ["Justin Furuness", "Matt Jaccino"]
__credits__ = ["Justin Furuness", "Matt Jaccino"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


def main():
    """Does all the command line options available"""

    # See function documention
    change_sys_args()

    parser = ArgumentParser(description="lib_bgp_data, see github")
    for cls in get_parsers():
        # This will override the argparse action class
        # Now when the arg is passed, the func __call__ will be called
        # In this case, __call__ is set to the parsers run method
        # Note that this is dynamically creating the class using type
        # https://www.tutorialdocs.com/article/python-class-dynamically.html
        # https://stackoverflow.com/a/40409974
        argparse_action_cls = type(cls.__name__,  # Class name
                                   (Action, ),  # Classes inherited
                                   {'__call__': cls.argparse_call()})  # __dict__
        parser.add_argument(f"--{cls.__name__.lower()}",
                            nargs=0,
                            action=argparse_action_cls)
    parser.parse_args()


def change_sys_args():
    """This function changes the sys args to be recognizable by argparse

    The reason we do this is so that we can dynamically add the parser
    classes names to the setup.py file as entry_points, and instead
    of adding a __main__ file to each submodule, we can instead direct
    all of those calls to this singular file, and parse in the same we
    we would with argparse.

    https://stackoverflow.com/a/55961848/8903959
    """

    names = [x.__name__.lower() for x in get_parsers()]
    # This means we must be calling it from the command line
    # without python3 -m lib_bgp_data --parser
    if "lib_bgp_data" not in argv[0] and len(argv) == 1:
        for name in names:  
            if name in argv[0]:
                argv.append("--" + name)
                argv[0] = "dummy arg"

def get_parsers() -> list:
    return [MRT_Parser, Relationships_Parser]


if __name__ == "__main__":
    main()
