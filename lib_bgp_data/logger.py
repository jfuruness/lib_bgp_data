#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class Logger with logging functionality"""

__author__ = "Justin Furuness"

import logging
import os


class Logger:
    def _initialize_logger(self,
                           log_name,
                           file_level,
                           stream_level,
                           log_dir="/var/log/bgp/"):
        """Initializes logger

        Logging levels are, in order:
        logging.CRITICAL
        logging.ERROR
        logging.WARNING
        logging.INFO
        logging.DEBUG

        Anything equal to or higher than file_level will be appended to path
        Anything equal to or higher than stream_level will be printed
        """

        path = os.path.join(log_dir, log_name)
        # Initialize logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # Initialize File Handler
        file_handler = logging.FileHandler('path')
        file_handler.setLevel(file_level)
        file_handler_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        file_handler.setFormatter(file_handler_formatter)
        self.logger.addHandler(file_handler)

        #Initialize Stream Handler
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(stream_level)
        stream_handler_formatter = logging.Formatter(
            '%(levelname)s - %(name)s - %(message)s')
        stream_handler.setFormatter(stream_handler_formatter)
        self.logger.addHandler(stream_handler)

