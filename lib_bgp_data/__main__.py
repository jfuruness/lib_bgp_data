#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module runs all command line arguments.

There is no real good place to include this documentation in the readme
so I will include it here. First see the main function, We override
__init_subclass__ in the Parser class to essentially just create a list
of all parsers as a class attribute called parsers. This is just
essentially just a list of all objects that inherited the Parser
class. All Parser classes have a method called argparse_call, which
if used in argparse will call the run method on the class. Then the
argparse call, in association with the lowercase name of the class,
are added to the argparse method. Essentially, you can type in any
lib_bgp_data with --{lowercase name of a parser class}, and the run
method will be called. The reason it was done this way was to make the
module extendable, so that anyone could simply inherit the Parser class
and have all of this taken care of behind the scenes.
"""

__authors__ = ["Justin Furuness", "Matt Jaccino"]
__credits__ = ["Justin Furuness", "Matt Jaccino"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from argparse import ArgumentParser, Action
from logging import DEBUG
from sys import argv

from .base_classes import Parser
from .utils import config_logging


def main():
    """Does all the command line options available

    See top of file for in depth description"""

    parser = ArgumentParser(description="lib_bgp_data, see github")
    for cls in Parser.parsers:
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

    # Configure logging to be debug if passed in
    # I know this should be done differently, but to make the module extendable
    # Sacrafices had to be made, and destroying argparse was one of them
    for i, arg in enumerate(argv):
        if "--debug" == arg.lower():
            config_logging(DEBUG)
            argv.pop(i)
            break

    parser.parse_args()


if __name__ == "__main__":
    main()
