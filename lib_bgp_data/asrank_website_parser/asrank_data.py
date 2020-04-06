#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains a way to store the asrank.caida.org data.

The ASRankData class contains the functionality to insert asrank data from
asrank.caida.org into the _rows list which consists of lists that each
represent a row on the main table of asrank.caida.org. The _rows list
that contains all the rows, of the asrank.caida.org table is then
added to the database.

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
import os

from ..utils import utils
from .tables import ASRankTable
from .mt_tqdm import MtTqdm


class ASRankData:
    """Class where the parsed rows of asrank.caida.org are saved.
    For a more in depth explanation see the top of the file.

    Attributes:
        _rows: list, Stores lists that each represent a row
            of the main asrank.caida.org table.
        _mt_tqdm: MtTqdm, An instance of a the thread safe, manually
            updating tqdm.
    """

    __slots__ = ['_rows', '_mt_tqdm']

    def __init__(self, total_rows):
        self._rows = []
        self._mt_tqdm = MtTqdm(100 / total_rows)

    def insert_data(self, tds_lst):
        """Given a list of five HTML table cells (tds)
        that make up a single row on asrank.caida.org,
        insert the information into the _rows list.

        Args:
            tds_lst: list, Contains five HTML table cells found on
                a row in the HTML of a page_num on asrank.caida.org.
        """
        new_row = []
        for col_ind, attr in enumerate(tds_lst):
            # A column index of 3 represents the country column
            if col_ind == 3:
                country = str(attr)[-16:-14]
                new_row.append(country)
            else:
                new_row.append(attr.text)
        self._rows.append(new_row)
        self._mt_tqdm.update()

    def insert_data_into_db(self, csv_dir):
        """The _rows data is inserted into the database under the
        table created in ASRankTable.

        The data will only be inserted into the db if the
        progress bar is complete. A full progress bar determines
        that no errors have occured/ no rows have been dropped.
        """
        complete = self._mt_tqdm.close()
        if not complete:
            logging.debug("Errors occured. Didn't insert into database.")
            return
        csv_path = os.path.join(csv_dir, self.__class__.__name__) + '.csv'
        utils.rows_to_db(self._rows, csv_path, ASRankTable, True)
        logging.debug("Inserted data into the database.")
