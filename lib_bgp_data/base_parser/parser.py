#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Parser

This class runs all parsers. See README for more details"""


__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "MIT"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from .decometa import DecoMeta
from ..utils import Thread_Safe_Logger as Logger
from ..utils import utils, set_global_section_header

class Parser:
    """This class is the base class for all parsers.

    See README for in depth explanation.
    """

    __slots__ = ['path', 'csv_dir', 'logger']
    # This will add an error_catcher decorator to all methods
    __metaclass__ = DecoMeta

    def __init__(self, **kwargs):
        """Initializes logger and path variables.

        Section is the arg for the config. You can run on entirely
        separate databases with different sections."""

        kwargs["section"] = kwargs.get("section", "bgp")

        # The class name. This because when parsers are done,
        # they aggressively clean up. We do not want parser to clean up in
        # the same directories and delete files that others are using
        name = f"{kwargs['section']}_{self.__class__.__name__}"
        # Set global section header varaible in Config's init
        set_global_section_header(kwargs["section"])
        self.logger = kwargs.get("logger", Logger(**kwargs))

        # Path to where all files willi go. It does not have to exist
        self.path = kwargs.get("path", f"/tmp/{name}")
        self.csv_dir = kwargs.get("csv_dir", f"/dev/shm/{name}")
        # Recreates empty directories
        utils.clean_paths(self.logger, [self.path, self.csv_dir])
        self.logger.debug(f"Initialized {name} at {utils.now()}")
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
            self.logger.error(e)
        finally:
            self.end_parser(start_time)

    def end_parser(self, start_time):
        """Ends parser, prints time and deletes files"""

        utils.clean_paths(self.logger,
                          [self.path, self.csv_dir],
                          recreate=False)
        # https://www.geeksforgeeks.org/python-difference-between-two-
        # dates-in-minutes-using-datetime-timedelta-method/
        _min, _sec = divmod((utils.now() - start_time).total_seconds(), 60)
        self.logger.info(f"{self.__class__.__name__} took {_min}m {_sec}s")

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
