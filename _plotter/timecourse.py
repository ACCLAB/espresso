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
        self._group_by=["Genotype","FoodChoice"]
        self._resample_by='10min'

    def __groupby_resamp(self,group_by=None,resample_by=None):
        if resample_by is not None:
            self._resample_by=resample_by

        if group_by is not None:
            if isinstance(group_by, str):
                g_by=[group_by]
            # make sure group_by is a column in feeds
            if len( [g for g in g_by if g in self.__feeds.columns] )==0:
                raise KeyError("{0} is/are not a column(s) in the feedlog.".format(g_by))
            self._group_by=self._group_by.extend(g_by)

        # Convert RelativeTime_s to datetime if not done so already.
        if self.__feeds.RelativeTime_s.dtype=='float64':
            self.__feeds.loc[:,'RelativeTime_s']=_pd.to_datetime(self.__feeds['RelativeTime_s'],
                                                                 unit='s')

        out_cols=['RelativeTime_s','FeedVol_µl']
        out_cols.extend(self._group_by)
        self._out_cols=out_cols # columns to print.

        return self.__feeds\
                   .groupby(self._group_by)\
                   .resample(self._resample_by,
                            on='RelativeTime_s')

    def __format_timecourse_dataframe(self, dataframe):
        """
        Convenience function to format timecourse dataframes before output.
        """
        df=dataframe[self._out_cols].copy()
        df.fillna(0,inplace=True)
        rt=df.loc[:,'RelativeTime_s']
        df['feed_time_s']=rt.dt.hour*3600+rt.dt.minute*60+rt.dt.second
        return df

    def _area_plot(dfplot, group_by, figsize, show_feed_color=True):
        """
        Convenience function to create an area plot from the munged feed vols/feed counts.
        """
        _sns.set(style='ticks',context='poster')
        grps=dfplot[group_by].unique()

        if figsize is None:
            x_inches=12
            y_inches=9
        else:
            if isinstance(figsize, tuple) or isinstance(figsize, list):
                x_inches=figsize[0]
                y_inches=figsize[1]
            else:
                raise ValueError('Please make sure figsize is a tuple of the form (w,h) in inches.')

        if show_feed_color:
            foodchoice_colors=_plot_helpers._make_categorial_palette(self.__feeds, 'FoodChoice')

        if ax is None:
            fig,axx=_plt.subplots(nrows=1,
                                  ncols=int( len(grps) ),
                                  figsize=(x_inches,y_inches),
                                  gridspec_kw={'wspace':0.2} )
        else:
            axx=ax

        for c, grp in enumerate( grps ):
            if len(grps)>1:
                feedvolax=axx[c]
            else:
                feedvolax=axx

            temp_df=df[df[group_by]==grp]
            df_grpby_sum=pd.DataFrame( temp_df\
                                        .groupby(['FoodChoice','feed_time_s'])\
                                        .sum().to_records() )
            df_grpby_sum_pivot=df_grpby_sum.pivot(index='feed_time_s',
                                                  columns='FoodChoice',
                                                  values='FeedVol_µl')
            df_grpby_sum_pivot.plot.area(ax=feedvolax,
                                        color=foodchoice_colors,
                                        lw=1)

            feedvolax.set_ylim(0,df['FeedVol_µl'].max())
            if c==0:
                feedvolax.set_ylabel('Total Consumption (µl)\n10 min bins')

        _plot_helpers.format_timecourse_xaxis(feedvolax)

        if ax is None:
            return fig

    def _make_feed_volume_dataframe(self,group_by=None,resample_by='10min'):
        """
        Produces a Pandas DataFrame with the feed volume per group
        in `group_by`, for each time interval as indicated by `resample_by`.
        """
        rsp=self.__groupby_resamp(group_by, resample_by)
        out=_pd.DataFrame( rsp.sum().to_records() )
        out=self.__format_timecourse_dataframe(out)

        return out

    def feed_volume(self,group_by=None,resample_by='10min',fig_size=None):
        """
        Produces a timecourse area plot depicting the feed volume for the entire assay.
        The plot will be tiled horizontally according to the category "group_by", and
        feed volumes will be binned by the duration in `resample_by`.

        keywords
        --------
        TBA

        Returns
        -------
        A matplotlib Figure.
        """
        dfplot=self._make_feed_volume_dataframe(group_by=group_by,
                                                resample_by=resample_by)
        self.__area_plot(dfplot,
                         self._group_by,
                         fig_size)


    # def _make_feed_count_dataframe(self,group_by,resample_by):
    #     """
    #     Produces a Pandas DataFrame with the feed count per group
    #     in `group_by`, for each time interval as indicated by `resample_by`.
    #     """
    #     self.__groupby_resamp(group_by, resample_by)
    #     out=_pd.DataFrame( self.groupby_resamp.count().to_records() )
    #     out=self.__format_timecourse_dataframe(out)
    #
    #     return out

    # def feed_count(self,group_by=None,resample_by='10min',figsize=None):
    #     dfplot=self.__make_feed_count_dataframe(group_by,resample_by)
    #     self.__area_plot(dfplot, group_by, figsize)
