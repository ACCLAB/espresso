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

from . import plot_helpers as _pth

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


    def __groupby_resamp(self,group_by,resample_by):
        self._resample_by=resample_by

        if group_by is None:
            self._group_by=["Genotype"]
        else:
            if isinstance(group_by, str):
                group_by=[group_by]
            # make sure group_by is a column in feeds
            if len( [g for g in group_by if g in self.__feeds.columns] )==0:
                raise KeyError("{0} is/are not a column(s) in the feedlog.".format(group_by))
            self._group_by=group_by

        # Convert RelativeTime_s to datetime if not done so already.
        if self.__feeds.RelativeTime_s.dtype=='float64':
            self.__feeds.loc[:,'RelativeTime_s']=_pd.to_datetime(self.__feeds['RelativeTime_s'],
                                                                 unit='s')

        out_cols=['RelativeTime_s','FeedVol_µl']
        out_cols.extend(self._group_by)
        self._out_cols=out_cols # columns to print.
        self.groupby_resamp=self.__feeds.groupby(self._group_by).resample(self._resample_by,on='RelativeTime_s')

    def __format_timecourse_dataframe(self, dataframe):
        """
        Convenience function to format timecourse dataframes before output.
        """
        df=dataframe[self._out_cols].copy()
        df.fillna(0,inplace=True)
        rt=df.loc[:,'RelativeTime_s']
        df['feed_time_s']=rt.dt.hour*3600+rt.dt.minute*60+rt.dt.second
        return df

    def feed_count(self,group_by=None,resample_by='10min'):
        """
        Produces a Pandas DataFrame with the feed count per group
        in `group_by`, for each time interval as indicated by `resample_by`.
        """
        self.__groupby_resamp(group_by, resample_by)
        out=_pd.DataFrame( self.groupby_resamp.count().to_records() )
        out=self.__format_timecourse_dataframe(out)

        return out

    def feed_volume(self,group_by=None,resample_by='10min'):
        """
        Produces a Pandas DataFrame with the feed volume per group
        in `group_by`, for each time interval as indicated by `resample_by`.
        """
        self.__groupby_resamp(group_by, resample_by)
        out=_pd.DataFrame( self.groupby_resamp.sum().to_records() )
        out=self.__format_timecourse_dataframe(out)

        return out
