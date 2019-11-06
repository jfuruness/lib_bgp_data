#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module runs all command line arguments"""

from argparse import ArgumentParser
from .roas_collector import ROAs_Collector
from .relationships_parser import Relationships_Parser
from .mrt_parser import MRT_Parser

__author__ = "Justin Furuness", "Matt Jaccino"
__credits__ = ["Justin Furuness", "Matt Jaccino"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"


def main():
    """Does all the command line options available"""

    parser = ArgumentParser(description="lib_bgp_data, see github")
    add_args(parser)
    args = vars(parser.parse_args())
    run_parsers(args)


def add_args(parser):
    """Adds all arguments to the parser"""

    _add_roas_args(parser)
    _add_rel_par_args(parser)
    _add_mrt_parser_args(parser)


def run_parsers(args):
    """Runs all parsers for arguments passed in"""

    _run_roas_parser(args)
    _run_rel_parser(args)
    _run_mrt_parser(args)


################################
### ROAs_Collector Functions ###
################################


def _run_roas_parser(args):
    """Runs the ROAs_Collector if arg passed in as true"""

    for permutation in _roas_collector_permutations():
        for key in args.keys():
            if args[key]:
                if key in permutation:
                    ROAs_Collector().parse_roas()
                    return


def _add_roas_args(parser):
    """Adds all roas permutations to the parser"""

    roas_permutations = _roas_collector_permutations()
    for permutation in roas_permutations:
        parser.add_argument(permutation, action="store_true", default=False)


def _roas_collector_permutations():
    """Gets every possible combination of arg for useability"""

    possible_permutations = []
    for i in [" ", "-", "--"]:
        for j in ["ROA", "roa"]:
            for k in ["S", "s", ""]:
                # I know l is bad but this function sucks anways
                for l in ["-", "_", " "]:
                    for m in ["Collector", "COLLECTOR", "collector",
                              "Parser", "parser", "PARSER"]:
                        possible_permutations.append(i + j + k + l + m)
    return possible_permutations

######################################
### Relationships_Parser Functions ###
######################################


def _run_rel_parser(args):
    """Runs the Relationships_Parser if arg passed in as true"""

    for permutation in _rel_parser_permutations():
        for key in args.keys():
            if args[key]:
                if key in permutation:
                    Relationships_Parser().parse_files()
                    return


def _add_rel_par_args(parser):
    """Adds all relationships parser permutations to the parser"""

    rel_par_permutations = _rel_parser_permutations()
    for permutation in rel_par_permutations:
        parser.add_argument(permutation, action="store_true", default=False)


def _rel_parser_permutations():
    """Gets every possible combination of arg for usability"""

    possible_permutations = []
    for i in [" ", "-", "--"]:
        for j in ["Relationship", "relationship", "rel", "Rel"]:
            for k in ["S", "s", ""]:
                for l in ["-", "_", " "]:
                    for m in ["Parser", "parser", "Par", "par"]:
                        possible_permutations.append(i + j + k + l + m)
    return possible_permutations


############################
### MRT_Parser Functions ###
############################


def _run_mrt_parser(args):
    """Runs the MRT Parser if arg passed in as true"""

    for perm in _mrt_parser_permutations():
        for key in args.keys():
            if args[key]:
                if key in perm:
                    MRT_Parser().parse_files()
                    return


def _add_mrt_parser_args(parser):
    """Adds all MRT Parser permutations to the parser"""

    mrt_parser_permutations = _mrt_parser_permutations()
    for perm in mrt_parser_permutations:
        parser.add_argument(perm, action="store_true", default=False)


def _mrt_parser_permutations():
    """Gets every possible combination of arg for usability"""

    possible_permutations = []
    for i in [" ", "-", "--"]:
        for j in ["MRT", "mrt"]:
            for k in ["S", "s", ""]:
                for l in ["-", " ", "_"]:
                    for m in ["Parser", "parser", "par"]:
                        possible_permutations.append(i + j + k + l + m)
    return possible_permutations


if __name__ == "__main__":
    main()
