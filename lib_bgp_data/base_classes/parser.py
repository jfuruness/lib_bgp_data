#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Parser

This class runs all parsers. See README for more details"""


__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import logging

import pytest

from ..utils import utils, config_logging
from ..database.config import set_global_section_header


class Parser:
    """This class is the base class for all parsers.

    See README for in depth explanation.
    """

    __slots__ = ['path', 'csv_dir', 'kwargs']
    # This will add an error_catcher decorator to all methods

    parsers = []
    # https://stackoverflow.com/a/43057166/8903959
    def __init_subclass__(cls, **kwargs):
        """This method essentially creates a list of all subclasses

        This is incredibly useful for a few reasons. Mainly, you can
        strictly enforce proper templating with this. And also, you can
        automatically add all of these things to things like argparse
        calls and such. Very powerful tool.
        """

        super().__init_subclass__(**kwargs)
        cls.parsers.append(cls)

    def __init__(self, **kwargs):
        """Initializes logger and path variables.

        Section is the arg for the config. You can run on entirely
        separate databases with different sections."""

        set_global_section_header(kwargs.get("section"))
        from ..database.config import global_section_header
        kwargs["section"] = kwargs.get("section", global_section_header)
        # The class name. This because when parsers are done,
        # they aggressively clean up. We do not want parser to clean up in
        # the same directories and delete files that others are using
        name = f"{kwargs['section']}_{self.__class__.__name__}"
        # Set global section header varaible in Config's init
        set_global_section_header(kwargs["section"])
        config_logging(kwargs.get("stream_level", logging.INFO),
                       kwargs["section"])

        # Path to where all files willi go. It does not have to exist
        self.path = kwargs.get("path", f"/tmp/{name}")
        self.csv_dir = kwargs.get("csv_dir", f"/dev/shm/{name}")
        # Recreates empty directories
        utils.clean_paths([self.path, self.csv_dir])
        self.kwargs = kwargs
        logging.debug(f"Initialized {name} at {utils.now()}")
        assert hasattr(self, "_run"), ("Needs _run, see Parser.py's run func "
                                       "Note that this is also used by default"
                                       " for running argparse. The main method"
                                       " for the parser must be labelled run")

    def run(self, *args, **kwargs):
        """Times main function of parser, errors nicely"""

        start_time = utils.now()
        try:
            self._run(*args, **kwargs)
        except Exception as e:
            self.end_parser(start_time)
            logging.exception(e)
        finally:
            self.end_parser(start_time)

    def end_parser(self, start_time):
        """Ends parser, prints time and deletes files"""

        utils.delete_paths([self.path, self.csv_dir])
        # https://www.geeksforgeeks.org/python-difference-between-two-
        # dates-in-minutes-using-datetime-timedelta-method/
        _min, _sec = divmod((utils.now() - start_time).total_seconds(), 60)
        logging.info(f"{self.__class__.__name__} took {_min}m {_sec}s")

    @classmethod
    def argparse_call(cls):
        """This function returns method to override argparse action

        To run a function when argparse is called, you must create an
        argparse.action class. This class must have a __call__ method
        that contains your function. This will return that method so
        that we can dynamically add to the argparse parser args.

        https://stackoverflow.com/a/18431364
        """

        def argparse_call_override(*args, **kwargs):
            cls().run()
        return argparse_call_override
