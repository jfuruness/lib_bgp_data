#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains functionality for a multiline tqdm"""

__author__ = "Justin Furuness"
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from tqdm import tqdm

class Multiline_TQDM:
    """Class that allows for larger descriptions using multiline tqdm

    Note that this is specifically for this simulator

    See https://github.com/tqdm/tqdm/issues/630#issuecomment-469085742
    """

    def __init__(self, total_trials, num_lines=5, initial_desc="Simulating"):
        """Creates progress bars. Total num bars = lines in description"""

        descs = self._get_desc()
        self.pbars = [tqdm(total=total_trials, desc=desc) for desc in descs]

    def __enter__(self):
        """Context manager to do upon entering"""
        return self

    def __exit__(self, type, value, traceback):
        """Context manager to do upon exiting"""

        self.close()

    def update(self):
        """Update all progress bars"""

        for pbar in self.pbars:
            pbar.update()

    def set_description(self, scenario, adopt_pol, percent, attack):
        """Sets all descriptions"""

        descs = self._get_desc(scenario, adopt_pol, percent, attack)

        for pbar, desc in zip(self.pbars, descs):
            # Sets description
            pbar.set_description(desc)
            # Note: if you can see them refreshing one after the other
            # Then change this to be a different for loop
            pbar.refresh()

    def _get_desc(self, scenario=None, policy=None, percent=None, attack=None):
        """Gets descriptions to use in the progress bars"""

        # Gets adoption policy name
        adopt_pol_name = Policies(policy.value).name if adopt_pol else ""

        # Descriptions
        descs = [f"Scenario: {scenario.value if scenario else ''}"
                 f"Adopt Policy: {adopt_pol_name}"
                 f"Adoption Percentage: {percent if percent else ''}"
                 f"Attacker: {attack.attacker_asn if attack else ''}"
                 f"Victim: {attack.victim_asn if attack else ''}"]
        # Pads descriptions out to 35 spaces
        return [f"{desc}{:<35}" for desc in descs]


    def close(self):
        """Closes all progress bars"""

        for pbar in self.pbars:
            pbar.close()
