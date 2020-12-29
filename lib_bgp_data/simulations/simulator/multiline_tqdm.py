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

from ..enums import Policies


class Multiline_TQDM:
    """Class that allows for larger descriptions using multiline tqdm
    Note that this is specifically for this simulator
    See https://github.com/tqdm/tqdm/issues/630#issuecomment-469085742
    """

    def __init__(self, total_trials):
        """Creates progress bars. Total num bars = lines in description"""

        descs = self._get_desc()
        self.pbars = [tqdm(total=total_trials, desc=desc) for desc in descs]
        self.total_trials = total_trials
        self.current_trial = 0

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
        self.current_trial += 1

    def update_extrapolator(self):
        """Sets the extrapolator to no longer be running"""

        self.set_desc(self.adopt_pol,
                      self.percent,
                      self.attack,
                      exr_running=False)

    def set_desc(self,
                 adopt_pol,
                 percent,
                 attack,
                 exr_running=True):
        """Sets all descriptions"""

        self.adopt_pol = adopt_pol
        self.percent = percent
        self.attack = attack

        descs = self._get_desc(adopt_pol,
                               percent,
                               attack,
                               exr_running)

        for pbar, desc in zip(self.pbars, descs):
            # Sets description
            pbar.set_description(desc)
            # Note: if you can see them refreshing one after the other
            # Then change this to be a different for loop
            pbar.refresh()

    def _get_desc(self,
                  policy=None,
                  percent=None,
                  attack=None,
                  exr_running=True):
        """Gets descriptions to use in the progress bars"""

        def default(x):
            return x if x is not None else ""

        policy_name = "" if policy is None else Policies(policy.value).name
        # Descriptions
        descs = [f"Attack_cls: {default(attack.__class__.__name__)}",
                 f"Adopt Policy: {policy_name}",
                 f"Adoption Percentage: {default(percent)}",
                 f"Attacker: {'' if not attack else default(attack.attacker)}",
                 f"Victim: {'' if not attack else default(attack.victim)}",
                 f"Extrapolator Running: {exr_running}"]
        # Pads descriptions out to 35 spaces
        return [f"{desc:<42}" for desc in descs]

    def close(self):
        """Closes all progress bars"""

        for pbar in self.pbars:
            pbar.close()
