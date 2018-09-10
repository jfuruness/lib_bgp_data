#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains a class BGPStream_Website_Parser.

This class can parse BGPStream events from bgpstream.com.
"""

import re
import multiprocessing
from multiprocessing import Process, Queue
from .bgpstream_row_parser import BGPStream_Row_Parser


class BGPStream_Website_Parser(BGPStream_Row_Parser):
    """Parses events from bgpstream.com, in parallel

    Also contains function from BGPStream_Row_Parser that parse rows
    """

    def __init__(self, logger, args):
        """Initializes regex expressions and arguments

        Row limit is the amount of entries to parse from bgpstream.com
        """

        # This regex parses out the AS number and name from a string of both
        self.as_regex = re.compile(r'''
                                   (?P<as_name>.+?)\s\(AS\s(?P<as_number>\d+)\)
                                   |
                                   (?P<as_number2>\d+).*?\((?P<as_name2>.+?)\)
                                   ''', re.VERBOSE
                                   )
        # This regex returns a string that starts and ends with numbers
        self.nums_regex = re.compile(r'(\d[^a-zA-Z\(\)\%]*\d*)')
        # This is for a queue to collect results from multithreaded module
        self.q = Queue()
        # The amount of entries from bgpstream.com to parse, mainly for testing
        self.row_limit = args.get("row_limit")  # Can be None
        self.logger = logger
        # I think you can only do about 100 in parallel then website cuts off
        self.parallel = args.get("parallel")

#################################
### Parsing Process Functions ###
#################################

    def parse(self, max_processes=multiprocessing.cpu_count()):
        """Parses html into a returned dict (in parallel if self.parallel)"""

        try:
            rows = self._get_tags("https://bgpstream.com", "tr")
            if self.row_limit is None or self.row_limit > (len(rows) - 3):
                # The - 3 is because the last couple of rows in the website are
                # screwed up, probably an html error or something who knows
                self.row_limit = len(rows) - 3
            if self.parallel is not None:
                return self._parallel_parse(rows, max_processes)
            else:
                return self._single_threaded_parse(rows)
        except Exception as e:
            self.logger.critical("Problem parsing bgpstream data: {}"\
                .format(e))
            raise e

    def _single_threaded_parse(self, rows):
        """Processes html into a returned dict"""

        vals = []
        for i in range(self.row_limit):
            val = self._parse_row(rows[i])
            self.logger.info(
                "Now processing row {}/{}".format(i, self.row_limit))
            vals.append(val)
        return vals

    def _parallel_parse(self, rows, max_processes):
        """Processes html into a returned dict in parallel

        Note that we can't use multiprocessing.pool here because it can't
        pickle properly, and pathos.multiprocessing is full of bugs. Because
        of this we impliment our own pool that cannot have more than the max
        amount of processes running at any given time. Note that if
        self.parallel=None, parallel parsing will not occur.
        """

        vals = []
        self.processes = []
        self.num_running = 0
        self.latest_unjoined = 0
        self.logger.info("Total number of rows: {}".format(self.row_limit))
        # This is the for loop to start the processes
        for i in range(self.row_limit):
            self._start_process(rows[i])
            # To make sure not too many processes are running
            self._wait_for_process(max_processes)
        # Join all processes still running
        self._join_remaining_processes()
        while(self.q.empty() is False):
            vals.append(self.q.get())
        return vals

    def _start_process(self, row):
        """Starts a process for parsing a row"""

        self.processes.append(Process(target=self._parse_row, args=(row,)))
        self.processes[-1].start()
        self.logger.info("Now processing row {}/{}"\
            .format(len(self.processes), self.row_limit))
        self.num_running += 1

    def _wait_for_process(self, max_processes):
        """Joins process if too many processes are running"""

        if self.num_running > max_processes:
            self.processes[self.latest_unjoined].join()
            self.num_running -= 1
            self.latest_unjoined += 1

    def _join_remaining_processes(self):
        """Joins all processes still running"""

        # After we are done starting processes, we have to join any remaining
        for i in range(self.latest_unjoined, self.row_limit):
            self.processes[i].join()
