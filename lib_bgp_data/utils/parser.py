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

import types

# https://stackoverflow.com/a/3468410
class DecoMeta(type):
    """This meta class just overrides all methods with a decorator.

    This decorator catches all errors and logs them properly.
    """


    def __new__(cls, name, bases, attrs):

        for attr_name, attr_value in attrs.iteritems():
            if isinstance(attr_value, types.FunctionType):
                attrs[attr_name] = cls.error_catcher(attr_value)

        return super(DecoMeta, cls).__new__(cls, name, bases, attrs)

    @classmethod
    # This decorator wraps all funcs in a try except statement
    # Note that it can only be put outside of funcs with self
    # The point of the decorator is so code errors nicely with useful information
    def error_catcher(cls, func):
        def wrapper(self, *args, **kwargs):
            # Inside the decorator
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                # Gets traceback object and error information
                error_class, error_desc, tb = sys.exc_info()
                # Makes sure it's not a system exit call
                if not str(error_desc) == '1':
                    for msg in traceback.format_tb(tb):
                        self.logger.debug(msg)
                    # Gets last call from program
                    tb_to_re = [x for x in str(traceback.format_tb(tb))
                                .split("File") if "lib_bgp_data" in x][-1]
                    # Performs regex to capture useful information
                    capture = tb_re.search(tb_to_re)
                    # Formats error string nicely
                    err_str = ("\n{0}{1}{0}\n"
                               "      msg: {2}\n"
                               "      {3}: {4}\n"
                               "      file_name: {5}\n"
                               "      function:  {6}\n"
                               "      line #:    {7}\n"
                               "      line:      {8}\n"
                               "{0}______{0}\n"
                               ).format("_"*36,
                                        "ERROR!",
                                        msg,
                                        error_class,
                                        error_desc,
                                        capture.group("file_name"),
                                        capture.group("function"),
                                        capture.group("line_num"),
                                        capture.group("line"))
                    self.logger.error(err_str)
                    # hahaha so professional
                    print('\a')
                # Exit program and also kills all parents/ancestors
                if (hasattr(pytest, 'global_running_test')
                    and pytest.global_running_test):
                    raise e
                else:
                    sys.exit(1)  # Turning this on breaks pytest - figure it out
        return wrapper

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

        # The class name. This because when parsers are done,
        # they aggressively clean up. We do not want parser to clean up in
        # the same directories and delete files that others are using
        name = f"{kwargs['section']}_{self.__class__.__name__}"
        kwargs["section"] = kwargs.get("section", "BGP")
        # Set global section header varaible in Config's init
        set_global_section_header(kwargs["section"])

        self._logger = kwargs.get("logger", Logger(kwargs))

        # Path to where all files willi go. It does not have to exist
        self.path = kwargs.get("path", f"/tmp/{namee}"
        self.csv_dir = kwargs.get("csv_dir", f"/dev/shm/{name}")
        # Recreates empty directories
        clean_paths(self.logger, [self.path, self.csv_dir])
        self.logger.debug(f"Initialized {name} at {now()}")
        assert hasattr(self._run), "Needs _run, see Parser.py's run method"

    def run(self *args, **kwargs):
        """Times main function of parser, errors nicely"""

        start_time = now()
        try:
            self._run(*args, **kwargs)
        except Exception as e:
            self.end_parser(self, start_time)
            self.logger.error(e)
        finally:
            self.end_parser(self, start_time)

    def end_parser(self, start_time):
        """Ends parser, prints time and deletes files"""

        self.clean_paths(self.logger,
                         [self.path, self.csv_dir],
                         recreate=False)
        # https://www.geeksforgeeks.org/python-difference-between-two-
        # dates-in-minutes-using-datetime-timedelta-method/
        _min, _sec = divmod((now() - start_time).total_seconds(), 60)
        self.logger.info(f"{self.__class__.__name__} took {_min}m {_sec}s")
