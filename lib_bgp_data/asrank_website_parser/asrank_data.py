#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains a way to store the asrank.caida.org data.

The ASRankData class contains the functionality to insert
asrank data from asrank.caida.org into five respective
lists that represent the five columns found on the website.
These five lists are then converted into a csv file
and then the csv file is inserted into a database.

Possible Future Extensions:
    -Add test cases
"""


__author__ = "Abhinna Adhikari"
__credits__ = ["Abhinna Adhikari"]
__Lisence__ = "MIT"
__maintainer__ = "Abhinna Adhikari"
__email__ = "abhinna.adhikari@uconn.edu"
__status__ = "Development"

import logging
import csv
import os

from ..utils import utils
from .constants import Constants
from .tables import ASRank_Table
from .mt_tqdm import MtTqdm


class ASRankData:
    """Class where the parsed rows of asrank.caida.org are saved.
    For a more in depth explanation see the top of the file.

    Attributes:
        _as_rank: list, Stores the AS Rank column of the
            main asrank.caida.org table.
        _as_num: list, Stores the AS Number column of the
            main asrank.caida.org table.
        _org: list, Stores the Organization column of the
            main asrank.caida.org table.
        _country: list, Stores the column that contains
            the country codes of the various country flags
            found on a column on the main asrank_caida.org table.
        _cone_size: list, Stores the Cone Size column of the
            main asrank.caida.org table.
        _elements_lst: list, Stores the _as_rank, _as_num,
            _org, _country, _cone_size lists.
        _total_entries: int, The total rows of the main table
            on asrank.caida.org.
        _mt_tqdm: MtTqdm, An instance of a the thread safe, manually
            updating tqdm.
    """

    def __init__(self, total_entries):
        self._as_rank = None
        self._as_num = None
        self._org = None
        self._country = None
        self._cone_size = None

        self._elements_lst = None
        self._total_entries = total_entries
        self._mt_tqdm = MtTqdm(100 / self._total_entries)
        self._init()

    def _init(self):
        """Initialize the lists where the five columns of
        information found on asrank.caida.org will be stored.
        """
        self._as_rank = [0] * self._total_entries
        self._as_num = [0] * self._total_entries
        self._org = [0] * self._total_entries
        self._country = [0] * self._total_entries
        self._cone_size = [0] * self._total_entries

        self._elements_lst = [self._as_rank,
                              self._as_num,
                              self._org,
                              self._country,
                              self._cone_size]

    def insert_data(self, page_num, tds_lst):
        """Given a list of HTML table cells (tds),
        insert into the respective element list.

        Args:
            page_num: int, The number of the page of the main table
                found on asrank.caida.org with Constants.ENTRIES_PER_PAGE
                entries per page.
            tds_lst: list, Contains all the HTML table cells found on
                the HTML of the page_num on asrank.caida.org.
        """
        for i in range(0, len(tds_lst) // len(self._elements_lst)):
            for j, element in enumerate(self._elements_lst):
                temp_ind = i * len(self._elements_lst) + j
                el_ind = page_num * Constants.ENTRIES_PER_PAGE + i

                if j != 3:
                    if j == 2 and len(tds_lst[temp_ind].text) == 0:
                        element[el_ind] = 'unknown'
                    else:
                        element[el_ind] = tds_lst[temp_ind].text
                else:
                    element[el_ind] = str(tds_lst[temp_ind])[-16:-14]
            self._mt_tqdm.update()

        total_pages = self._total_entries // Constants.ENTRIES_PER_PAGE

    def _write_csv(self, csv_path):
        """Convert the stored data into a tab
        separated csv file at path, csv_path.

        Args:
            csv_path: str, the full path of the csv file where the
                parsed asrank main table will be stored.
        """
        with open(csv_path, mode='w') as temp_csv:
            csv_writer = csv.writer(temp_csv,
                                    delimiter='\t',
                                    quotechar='"',
                                    quoting=csv.QUOTE_MINIMAL)
            for i in range(len(self._as_rank)):
                row = [lst[i] for lst in self._elements_lst]
                csv_writer.writerow(row)

        logging.debug(f"Wrote {csv_path}")

    def insert_data_into_db(self):
        """Create a CSV file with asrank data and then
        use the csv file to insert into the database.
        """
        self._mt_tqdm.close()
        csv_path = os.path.join(Constants.FILE_PATH, Constants.CSV_FILE_NAME)
        self._write_csv(csv_path)
        utils.csv_to_db(ASRank_Table, csv_path, True)

        logging.debug("Inserted data into the database")
        print('Done.')
