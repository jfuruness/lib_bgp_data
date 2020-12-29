#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generates policy lines"""

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

import itertools

from .line_format import Line_Format


class Line_Formatter:
    def __init__(self, policies):
        self.policy_format_dict = {}
        marks_styles_colors = self.markers_styles_colors
        for i, policy in enumerate(policies):
            self.policy_format_dict[policy] = Line_Format(*marks_styles_colors)

    @property
    def markers_styles_colors(self):
        # We can't use a simple for loop here
        # Since we want them to both change as much as possible
        # so instead we zip together markers and styles
        # with every possible ordering of each
        marker_perms = itertools.permutations(self.markers, len(self.markers))
        style_perms = [self.styles] * len(marker_perms)
        color_perms = itertools.permutations(self.colors, len(self.colors))
        markers = self.flatten_list(marker_perms)
        styles = self.flatten_list(style_perms)
        colors = self.flatten_list(list(color_perms)[::-1])
        return list(zip(markers, styles, colors))

    def get_format_kwargs(self, policy):
        return {"label": policy,
                "ls": self.policy_format_dict[policy].style,
                "marker": self.policy_format_dict[policy].marker,
                "color": self.policy_format_dict[policy].color}

    def flatten_list(self, _list):
        return list(itertools.chain.from_iterable(list(_list)))

    @property
    def markers(self):
        return [".", "1", "*", "x", "d", "2", "3", "4"]

    @property
    def styles(self):
        return ["-", "--", "-.", ":", "solid", "dotted", "dashdot", "dashed"]

    @property
    def colors(self):
        # https://matplotlib.org/2.0.2/api/colors_api.html
        return ["b", "g", "r", "c", "m", "y", "k", "w"]
