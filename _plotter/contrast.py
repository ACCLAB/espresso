#!/usr/bin/python
# -*-coding: utf-8 -*-
# Author: Joses Ho
# Email : joseshowh@gmail.com

"""
contrast plot functions for espresso objects.
"""

 #      # #####  #####    ##   #####  #   #    # #    # #####   ####  #####  #####
 #      # #    # #    #  #  #  #    #  # #     # ##  ## #    # #    # #    #   #
 #      # #####  #    # #    # #    #   #      # # ## # #    # #    # #    #   #
 #      # #    # #####  ###### #####    #      # #    # #####  #    # #####    #
 #      # #    # #   #  #    # #   #    #      # #    # #      #    # #   #    #
 ###### # #####  #    # #    # #    #   #      # #    # #       ####  #    #   #

import sys as _sys
import os as _os

import numpy as _np
import scipy as _sp
import pandas as _pd

import matplotlib as _mpl
import matplotlib.pyplot as _plt
import matplotlib.ticker as _tk

import seaborn as _sns
import bootstrap_contrast as _bsc

from . import plot_helpers as _pth

class contrast_plotter:
    """
    contrast plotting class for espresso object.
    """

    #    #    #    #    #####
    #    ##   #    #      #
    #    # #  #    #      #
    #    #  # #    #      #
    #    #   ##    #      #
    #    #    #    #      #

    def __init__(self,plotter): # pass along an espresso_plotter instance.
        self._experiment=plotter._experiment

    def __generic_contrast_plotter():
        pass

    def feed_count_per_fly(self, group_by, palette_type='categorical',contrastplot_kwargs=None):

        """
        Produces a contrast plot depicting the mean differences in the feed counts between groups.
        Place any contrast plot keywords in a dictionary and pass in through `contrastplot_kwargs`.

        Keywords
        --------
        group_by: string, categorical
            The column or label indicating the categorical grouping on the x-axis.

        palette_type: string, 'categorical' or 'sequential'.

        contrastplot_kwargs: dict, default None
            All contrastplot keywords will be entered here.

        Returns
        -------

        A matplotlib Axes instance, and a pandas DataFrame with the statistics.
        """

        default_kwargs=dict(fig_size=(12,9),
                            float_contrast=False,
                            font_scale=1.4,
                            swarmplot_kwargs={'size':6})
        if contrastplot_kwargs is None:
            contrastplot_kwargs=default_kwargs
        else:
            contrastplot_kwargs=_bsc.merge_two_dicts(default_kwargs,contrastplot_kwargs)

        # Select palette.
        if palette_type=='categorical':
            color_palette=_pth._make_categorial_palette(self._experiment.feeds,group_by)
        elif palette_type=='sequential':
            color_palette=_pth._make_sequential_palette(self._experiment.feeds,group_by)

        total_feeds=_pd.DataFrame(self._experiment.feeds[['FlyID',group_by,'FeedVol_nl']].\
                                    groupby([group_by,'FlyID']).count().\
                                    to_records())
        total_feeds.columns=[group_by,'FlyID','Total feed count\nper fly']
        max_feeds=_np.round(total_feeds.max()['Total feed count\nper fly'],decimals=-2)

        f,b=_bsc.contrastplot(data=total_feeds,
                              x=group_by,y='Total feed count\nper fly',
                              idx=_np.sort(total_feeds.loc[:,group_by].unique()),
                              **contrastplot_kwargs)

        f.suptitle('Contrast Plot Total Feed Count Per Fly')

        return f,b
