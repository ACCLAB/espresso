#!/usr/bin/python
# -*-coding: utf-8 -*-
# Author: Joses Ho
# Email : joseshowh@gmail.com

"""
timecourse plot functions for espresso objects.
"""

 #      # #####  #####    ##   #####  #   #    # #    # #####   ####  #####  #####
 #      # #    # #    #  #  #  #    #  # #     # ##  ## #    # #    # #    #   #
 #      # #####  #    # #    # #    #   #      # # ## # #    # #    # #    #   #
 #      # #    # #####  ###### #####    #      # #    # #####  #    # #####    #
 #      # #    # #   #  #    # #   #    #      # #    # #      #    # #   #    #
 ###### # #####  #    # #    # #    #   #      # #    # #       ####  #    #   #

import sys as _sys
_sys.path.append("..") # so we can import espresso from the directory above.

import os as _os

import numpy as _np
import scipy as _sp
import pandas as _pd

import matplotlib as _mpl
import matplotlib.pyplot as _plt
import matplotlib.ticker as _tk

import seaborn as _sns
import bootstrap_contrast as _bsc

from . import plot_helpers as _plot_helpers
from _munger import munger as _munger

class timecourse_plotter():
    """
    timecourse plotting class for espresso object.
    """

#    #    #    #    #####
#    ##   #    #      #
#    # #  #    #      #
#    #  # #    #      #
#    #   ##    #      #
#    #    #    #      #

    def __init__(self,plotter): # pass along an espresso_plotter instance.
        self.__feeds=plotter._experiment.feeds.copy()

    def __pivot_for_plot(self,resampdf,group_by,color_by):
        return _pd.DataFrame( resampdf.groupby([group_by,
                                                color_by,
                                                'feed_time_s']).sum().to_records() )

####  ###### #    # ###### #####  #  ####
#    # #      ##   # #      #    # # #    #
#      #####  # #  # #####  #    # # #
#  ### #      #  # # #      #####  # #
#    # #      #   ## #      #   #  # #    #
####  ###### #    # ###### #    # #  ####
##### # #    # ######  ####   ####  #    # #####   ####  ######
#   # ##  ## #      #    # #    # #    # #    # #      #
#   # # ## # #####  #      #    # #    # #    #  ####  #####
#   # #    # #      #      #    # #    # #####       # #
#   # #    # #      #    # #    # #    # #   #  #    # #
#   # #    # ######  ####   ####   ####  #    #  ####  ######
#####  #       ####  ##### ##### ###### #####
#    # #      #    #   #     #   #      #    #
#    # #      #    #   #     #   #####  #    #
#####  #      #    #   #     #   #      #####
#      #      #    #   #     #   #      #   #
#      ######  ####    #     #   ###### #    #
    def __generic_timecourse_plotter(self,
                                     yvar,
                                     group_by=None,
                                     color_by=None,
                                     resample_by='10min',
                                     fig_size=None,
                                     gridlines_major=True,
                                     gridlines_minor=True,
                                     ax=None):

        # Handle the group_by and color_by keywords.
        group_by, color_by = _munger.check_group_by_color_by(group_by, color_by, self.__feeds)

        print( "Coloring feed volume time course by {0}".format(color_by) )
        print( "Grouping feed volume time course by {0}".format(group_by) )

        if color_by==group_by: # catch as exception:
            raise ValueError('color_by and group_by both have the same value. They should be 2 different column names in the feedlog.')

        resampdf=_munger.groupby_resamp(self.__feeds, group_by, color_by, resample_by)
        plotdf=self.__pivot_for_plot(resampdf,group_by,color_by)

        groupby_grps=_np.sort( plotdf[group_by].unique() )
        num_plots=int( len(groupby_grps) )

        # Initialise figure.
        _sns.set(style='ticks',context='poster')
        if fig_size is None:
            x_inches=10*num_plots
            y_inches=7
        else:
            if isinstance(fig_size, tuple) or isinstance(fig_size, list):
                x_inches=fig_size[0]
                y_inches=fig_size[1]
            else:
                raise TypeError('Please make sure figsize is a tuple of the form (w,h) in inches.')

        if ax is None:
            fig,axx=_plt.subplots(nrows=1,
                                  ncols=num_plots,
                                  figsize=(x_inches,y_inches),
                                  gridspec_kw={'wspace':0.2} )
        else:
            axx=ax

        # Loop through each panel.
        for c, grp in enumerate( groupby_grps ):
            if len(groupby_grps)>1:
                plotax=axx[c]
            else:
                plotax=axx

            ## Plot the raster plots.
            ### Plot vertical grid lines if desired.
            if gridlines_major:
                plotax.xaxis.grid(True,linestyle='dotted',which='major',alpha=1)
            if gridlines_minor:
                plotax.xaxis.grid(True,linestyle='dotted',which='minor',alpha=0.5)
                ## Filter plotdf according to group_by.
                temp_plotdf=plotdf[plotdf[group_by]==grp]
                temp_plotdf_pivot=temp_plotdf.pivot(index='feed_time_s',
                                                     columns=color_by,
                                                     values=yvar)

                ### and make area plot.
                temp_plotdf_pivot.plot.area(ax=plotax,lw=1)
            ## Add the group name as title.
            plotax.set_title(grp)
            ## Format x-axis.
            _plot_helpers.format_timecourse_xaxis(plotax)

        # Normalize all the y-axis limits.
        if num_plots>1:
            _plot_helpers.normalize_ylims(axx)
            ## Despine and offset each axis.
            for a in axx:
                _sns.despine(ax=a,trim=True,offset=5)
        else:
            _sns.despine(ax=axx,trim=True,offset=5)

        # Position the raster color legend,
        # and label the y-axis appropriately.
        if num_plots>1:
            rasterlegend_ax=axx
        else:
            rasterlegend_ax=[ axx ]
        for a in rasterlegend_ax:
            a.legend(loc='upper left',bbox_to_anchor=(0,-0.15))
            ## Add additional timecourse plot definitions below.
            if yvar=='AverageFeedVolumePerFly_µl':
                a.set_ylabel('Average Feed Volume Per Fly (µl)')
            elif yvar=='AverageFeedCountPerFly':
                a.set_ylabel('Average Feed Count Per Fly')
            elif yvar=='AverageFeedSpeedPerFly_µl/s':
                a.set_ylabel('Average Feed Speed Per Fly (µl/s)')

        # End and return the figure.
        if ax is None:
            return axx

###### ###### ###### #####     #    #  ####  #      #    # #    # ######
#      #      #      #    #    #    # #    # #      #    # ##  ## #
#####  #####  #####  #    #    #    # #    # #      #    # # ## # #####
#      #      #      #    #    #    # #    # #      #    # #    # #
#      #      #      #    #     #  #  #    # #      #    # #    # #
#      ###### ###### #####       ##    ####  ######  ####  #    # ######

    def feed_volume(self,
                    group_by=None,
                    color_by=None,
                    resample_by='10min',
                    fig_size=None,
                    gridlines_major=True,
                    gridlines_minor=True,
                    ax=None):
        """
        Produces a timecourse area plot depicting the average feed volume per fly
        for the entire assay. The plot will be tiled horizontally according to the
        category "group_by", and will be stacked and colored according to the category
        "color_by". Feed volumes will be binned by the duration in `resample_by`.

        keywords
        --------
        group_by: string, default None
            Accepts a categorical column in the espresso object. Each group in this column
            will be plotted on its own axes.

        color_by: string, default None
            Accepts a categorical column in the espresso object. Each group in this column
            will be colored seperately, and stacked as an area plot.

        resample_by: string, default '10min'
            The time frequency used to bin the timecourse data. For the format, please see
            http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases

        fig_size: tuple (width, height), default None
            The size of the final figure, in inches.

        gridlines_major, gridlines_minor: boolean, default True
            Whether or not major and minor vertical gridlines are displayed.

        ax: array of matplotlib Axes objects, default None
            Given an array of Axes, each category (as dictacted by group_by) will be plotted
            respectively.

        Returns
        -------
        matplotlib AxesSubplot(s)
        """
        out=self.__generic_timecourse_plotter('AverageFeedVolumePerFly_µl' ,
                                               group_by=group_by,
                                               color_by=color_by,
                                               resample_by=resample_by,
                                               fig_size=fig_size,
                                               gridlines_major=gridlines_major,
                                               gridlines_minor=gridlines_minor,
                                               ax=ax)

        return out

###### ###### ###### #####      ####   ####  #    # #    # #####
#      #      #      #    #    #    # #    # #    # ##   #   #
#####  #####  #####  #    #    #      #    # #    # # #  #   #
#      #      #      #    #    #      #    # #    # #  # #   #
#      #      #      #    #    #    # #    # #    # #   ##   #
#      ###### ###### #####      ####   ####   ####  #    #   #

    def feed_count(self,
                    group_by=None,
                    color_by=None,
                    resample_by='10min',
                    fig_size=None,
                    gridlines_major=True,
                    gridlines_minor=True,
                    ax=None):
        """
        Produces a timecourse area plot depicting the average feed count per fly
        for the entire assay. The plot will be tiled horizontally according to the
        category "group_by", and will be stacked and colored according to the category
        "color_by". Feed counts will be binned by the duration in `resample_by`.

        keywords
        --------
        group_by: string, default None
            Accepts a categorical column in the espresso object. Each group in this column
            will be plotted on its own axes.

        color_by: string, default None
            Accepts a categorical column in the espresso object. Each group in this column
            will be colored seperately, and stacked as an area plot.

        resample_by: string, default '10min'
            The time frequency used to bin the timecourse data. For the format, please see
            http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases

        fig_size: tuple (width, height), default None
            The size of the final figure, in inches.

        gridlines_major, gridlines_minor: boolean, default True
            Whether or not major and minor vertical gridlines are displayed.

        ax: array of matplotlib Axes objects, default None
            Given an array of Axes, each category (as dictacted by group_by) will be plotted
            respectively.

        Returns
        -------
        matplotlib AxesSubplot(s)
        """
        out=self.__generic_timecourse_plotter('AverageFeedCountPerFly',
                                              group_by=group_by,
                                              color_by=color_by,
                                              resample_by=resample_by,
                                              fig_size=fig_size,
                                              gridlines_major=gridlines_major,
                                              gridlines_minor=gridlines_minor,
                                              ax=ax)
        return out

###### ###### ###### #####      ####  #####  ###### ###### #####
#      #      #      #    #    #      #    # #      #      #    #
#####  #####  #####  #    #     ####  #    # #####  #####  #    #
#      #      #      #    #         # #####  #      #      #    #
#      #      #      #    #    #    # #      #      #      #    #
#      ###### ###### #####      ####  #      ###### ###### #####

    def feed_speed(self,
                    group_by=None,
                    color_by=None,
                    resample_by='10min',
                    fig_size=None,
                    gridlines_major=True,
                    gridlines_minor=True,
                    ax=None):
        """
        Produces a timecourse area plot depicting the average feed speed per fly in µl/s
        for the entire assay. The plot will be tiled horizontally according to the
        category "group_by", and will be stacked and colored according to the category
        "color_by". Feed speeds will be binned by the duration in `resample_by`.

        keywords
        --------
        group_by: string, default None
            Accepts a categorical column in the espresso object. Each group in this column
            will be plotted on its own axes.

        color_by: string, default None
            Accepts a categorical column in the espresso object. Each group in this column
            will be colored seperately, and stacked as an area plot.

        resample_by: string, default '10min'
            The time frequency used to bin the timecourse data. For the format, please see
            http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases

        fig_size: tuple (width, height), default None
            The size of the final figure, in inches.

        gridlines_major, gridlines_minor: boolean, default True
            Whether or not major and minor vertical gridlines are displayed.

        ax: array of matplotlib Axes objects, default None
            Given an array of Axes, each category (as dictacted by group_by) will be plotted
            respectively.

        Returns
        -------
        matplotlib AxesSubplot(s)
        """
        out=self.__generic_timecourse_plotter('AverageFeedSpeedPerFly_µl/s',

                                              group_by=group_by,
                                              color_by=color_by,
                                              resample_by=resample_by,
                                              fig_size=fig_size,
                                              gridlines_major=gridlines_major,
                                              gridlines_minor=gridlines_minor,
                                              ax=ax)
        return out
