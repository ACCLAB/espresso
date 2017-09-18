#!/usr/bin/python
# -*-coding: utf-8 -*-
# Author: Joses Ho
# Email : joseshowh@gmail.com

"""
Plot functions for espresso objects.
"""

import sys as _sys
import os as _os

import numpy as _np
import scipy as _sp
import pandas as _pd

import matplotlib as _mpl
import matplotlib.pyplot as _plt

import seaborn as _sns
import bootstrap_contrast as _bsc

import plot_helpers as _pth

class EspressoPlotter:
    """
    Plotting class for espresso object.
    """

 #    #    #    #    #####
 #    ##   #    #      #
 #    # #  #    #      #
 #    #  # #    #      #
 #    #   ##    #      #
 #    #    #    #      #

    def __init__(self,espresso): # pass along an espresso instance.
        self._flies=espresso.flies
        self._feeds=espresso.feeds

 ##### ######  ####  #####     ####  #    #   ##   #####  #    # #####  #       ####  #####
   #   #      #        #      #      #    #  #  #  #    # ##  ## #    # #      #    #   #
   #   #####   ####    #       ####  #    # #    # #    # # ## # #    # #      #    #   #
   #   #           #   #           # # ## # ###### #####  #    # #####  #      #    #   #
   #   #      #    #   #      #    # ##  ## #    # #   #  #    # #      #      #    #   #
   #   ######  ####    #       ####  #    # #    # #    # #    # #      ######  ####    #

    def _swarm(self):
        _sns.set(style='ticks',context='talk')
        x=_np.random.random(10)
        y=_np.random.random(10)
        df=_pd.DataFrame([x,y]).T
        ax=_sns.swarmplot(data=df)

        return ax

 #    #   ##   #    # ######    #####    ##   #      ###### ##### ##### ######  ####
 ##  ##  #  #  #   #  #         #    #  #  #  #      #        #     #   #      #
 # ## # #    # ####   #####     #    # #    # #      #####    #     #   #####   ####
 #    # ###### #  #   #         #####  ###### #      #        #     #   #           #
 #    # #    # #   #  #         #      #    # #      #        #     #   #      #    #
 #    # #    # #    # ######    #      #    # ###### ######   #     #   ######  ####

    def _make_categorial_palette(self, group_by):
        """
        Create a categorical color palette.
        """
        _cat_palette=_sns.color_palette( n_colors=len(self._feeds[group_by].unique()) )
        return _cat_palette

    def _make_sequential_palette(self, group_by):
        """
        Create a sequential color palette.
        """
        _seq_palette=_sns.cubehelix_palette( n_colors=len(self._feeds[group_by].unique()) )
        return _seq_palette

 #####  ###### #####   ####  ###### #    # #####    ###### ###### ###### #####  # #    #  ####
 #    # #      #    # #    # #      ##   #   #      #      #      #      #    # # ##   # #    #
 #    # #####  #    # #      #####  # #  #   #      #####  #####  #####  #    # # # #  # #
 #####  #      #####  #      #      #  # #   #      #      #      #      #    # # #  # # #  ###
 #      #      #   #  #    # #      #   ##   #      #      #      #      #    # # #   ## #    #
 #      ###### #    #  ####  ###### #    #   #      #      ###### ###### #####  # #    #  ####

    def percent_feeding(self,group_by,
                        time_start=0,time_end=360,
                        palette_type='categorical'):
        """
        Produces a lineplot depicting the percent of flies feeding for each condition.
        A 95% confidence interval for each proportion of flies feeding is also given.

        Keywords
        --------
        group_by: string, categorical
            The column or label indicating the categorical grouping on the x-axis.

        time_start, time_end: integer, default 0 and 360 respectively
            The time window (in minutes) during which to compute and display the
            percent flies feeding.

        palette_type: string, 'categorical' or 'sequential'.

        Returns
        -------

        A matplotlib Axes instance, and a pandas DataFrame with the statistics.
        """
        # Get plotting variables.
        percent_feeding_summary=_pth.compute_percent_feeding(self._flies,
                                                             self._feeds,
                                                             group_by,
                                                             start=time_start,
                                                             end=time_end)

        # return percent_feeding_summary ## used to debug.

        cilow=percent_feeding_summary.ci_lower.tolist()
        cihigh=percent_feeding_summary.ci_upper.tolist()
        ydata=percent_feeding_summary.percent_feeding.tolist()

        # Select palette.
        if palette_type=='categorical':
            color_palette=self._make_categorial_palette(group_by)
        elif palette_type=='sequential':
            color_palette=self._make_sequential_palette(group_by)

        # Set style.
        _sns.set(style='ticks',context='talk',font_scale=1.1)

        # Initialise figure.
        f,ax=_plt.subplots(1,figsize=(8,5))
        ax.set_ylim(0,110)
        # Plot 95CI first.
        ax.fill_between(range(0,len(percent_feeding_summary)),
                        cilow,cihigh,
                        alpha=0.25,
                        color='grey' )
        # Then plot the line.
        percent_feeding_summary.percent_feeding.plot.line(ax=ax,color='k',lw=1.2)

        for j,s in enumerate(ydata):
            ax.plot(j, s, 'o',
                    color=color_palette[j])

        # Aesthetic tweaks.
        ax.xaxis.set_ticks( [i for i in range( 0,len(percent_feeding_summary) )] )
        ax.xaxis.set_ticklabels( percent_feeding_summary.index.tolist() )

        xmax=ax.xaxis.get_ticklocs()[-1]
        ax.set_xlim(-0.2, xmax+0.2) # Add x-padding.
        _bsc.rotate_ticks(ax, angle=45, alignment='right')
        _sns.despine(ax=ax,trim=True,offset={'left':1})
        ax.set_ylabel('Percent Feeding')

        f.tight_layout()
        return f, percent_feeding_summary


 ###### ###### ###### #####      ####   ####  #    # #    # #####    #####  ###### #####     ###### #      #   #
 #      #      #      #    #    #    # #    # #    # ##   #   #      #    # #      #    #    #      #       # #
 #####  #####  #####  #    #    #      #    # #    # # #  #   #      #    # #####  #    #    #####  #        #
 #      #      #      #    #    #      #    # #    # #  # #   #      #####  #      #####     #      #        #
 #      #      #      #    #    #    # #    # #    # #   ##   #      #      #      #   #     #      #        #
 #      ###### ###### #####      ####   ####   ####  #    #   #      #      ###### #    #    #      ######   #

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
            color_palette=self._make_categorial_palette(group_by)
        elif palette_type=='sequential':
            color_palette=self._make_sequential_palette(group_by)

        total_feeds=_pd.DataFrame(self._feeds[['FlyID',group_by,'FeedVol_nl']].\
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
