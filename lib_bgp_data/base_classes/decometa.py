#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains metaclass decometa.

This class decorates all functions with error_catcher.
See README for more details"""


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
