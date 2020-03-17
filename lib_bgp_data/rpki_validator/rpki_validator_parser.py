#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This file contains the RPKI_Validator_Parser.

This class parses info from the RPKI_Validator_Wrapper.
See README for more in depth details.
"""

__author__ = "Justin Furuness", "Cameron Morris"
__credits__ = ["Cameron Morris", "Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import logging

from .rpki_validator_wrapper import RPKI_Validator_Wrapper
from .tables import ROV_Validity_Table
from ..base_classes import Parser
from ..utils import utils


class RPKI_Validator_Parser(Parser):
    """Parses information from the RPKI Validator.

    This class is separate from the rpki validator itself because
    the RPKI Validator class is really meant to be it's standalone
    wrapper. It's possible that later someone else will want to use it.
    """

    def _run(self):
        """Downloads and stores roas from a json"""

        with RPKI_Validator_Wrapper() as _rpki_validator:
            # First we wait for the validator to load the data
            _rpki_validator.load_trust_anchors()
            # Writes validator to database
            logging.debug("validator load completed")
            rpki_data = _rpki_validator.get_validity_data()
            utils.rows_to_db([self._format_asn_dict(x) for x in rpki_data],
                             f"{self.csv_dir}/validity.csv",  # CSV
                             ROV_Validity_Table)

    def _format_asn_dict(self, asn: dict) -> list:
        """Formats json objects for csv rows"""

        valid = RPKI_Validator_Wrapper.get_validity_dict()
        return [int(asn["asn"][2:]), asn["prefix"], valid.get(asn["validity"])]
