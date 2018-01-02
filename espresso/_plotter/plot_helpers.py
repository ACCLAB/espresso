#!/usr/bin/python
# -*-coding: utf-8 -*-
# Author: Joses Ho
# Email : joseshowh@gmail.com

import sys as _sys
import os as _os

import numpy as _np
import scipy as _sp
import pandas as _pd

import matplotlib.pyplot as _plt
import matplotlib.ticker as _tk
import seaborn as _sns

#####  #       ####  #####    #    # ###### #      #####  ###### #####   ####
#    # #      #    #   #      #    # #      #      #    # #      #    # #
#    # #      #    #   #      ###### #####  #      #    # #####  #    #  ####
#####  #      #    #   #      #    # #      #      #####  #      #####       #
#      #      #    #   #      #    # #      #      #      #      #   #  #    #
#      ######  ####    #      #    # ###### ###### #      ###### #    #  ####

def normalize_ylims(ax_arr,include_zero=False,draw_zero_line=False):
    """Custom function to normalize ylims for an array of axes."""
    ymins=list()
    ymaxs=list()
    for ax in ax_arr:
        ymin=ax.get_ylim()[0]
        ymax=ax.get_ylim()[1]
        ymins.append(ymin)
        ymaxs.append(ymax)
    new_min=_np.min(ymins)
    new_max=_np.max(ymaxs)
    if include_zero:
        if new_max<0:
            new_max=0
        if new_min>0:
            new_min=0
    for ax in ax_arr:
        ax.set_ylim(new_min,new_max)
    if draw_zero_line:
        for ax in ax_arr:
            ax.axhline(y=0,linestyle='solid',linewidth=0.5,color='k')

def meanci(mean, cilow, cihigh, idx, ax, alpha=0.8, marker= 'o',color='black', size=8, ls='solid',lw=1.2):
    """Custom function to normalize plot the mean and CI as a dot and a vertical line, respectively."""
    # Plot the summary measure.
    ax.plot(idx, mean,
             marker=marker,
             markerfacecolor=color,
             markersize=size,
             alpha=alpha
            )
    # Plot the CI.
    ax.plot([idx, idx],
             [cilow, cihigh],
             color=color,
             alpha=alpha,
             linestyle=ls,
            linewidth=lw
            )

# Define function for string formatting of scientific notation.
def sci_nota(num, decimal_digits=2, precision=None, exponent=None):
    """
    Returns a string representation of the scientific
    notation of the given number formatted for use with
    LaTeX or Mathtext, with specified number of significant
    decimal digits and precision (number of decimal digits
    to show). The exponent to be used can also be specified
    explicitly.

    Found on https://stackoverflow.com/questions/21226868/superscript-in-python-plots
    """
    if not exponent:
        exponent = int(_np.floor(_np.log10(abs(num))))
    coeff = round(num / float(10**exponent), decimal_digits)
    if not precision:
        precision = decimal_digits

    return r"${0:.{2}f}\times10^{{{1:d}}}$".format(coeff, exponent, precision)

def compute_percent_feeding(metadata,feeds,group_by,start=0,end=30):
    """
    Used to compute the percent of flies feeding from
    a processed dataset of feedlogs.
    """
    feeds_plot=feeds.copy()

    fly_counts=metadata.groupby(group_by).count().FlyID
    data_timewin=feeds_plot[ (feeds_plot.RelativeTime_s > start*60) &
                             (feeds_plot.RelativeTime_s < end*60) ]
    # To count total flies that fed, I adapted the methods here:
    # https://stackoverflow.com/questions/8364674/python-numpy-how-to-count-the-number-of-true-elements-in-a-bool-array
    feed_boolean_by_fly=~_np.isnan( data_timewin.groupby([group_by,'FlyID']).sum()['FeedVol_µl'] )
    fly_feed_counts=feed_boolean_by_fly.apply(_np.count_nonzero).groupby(group_by).sum()
    # Proportion code taken from here:
    # https://onlinecourses.science.psu.edu/stat100/node/56
    percent_feeding=(fly_feed_counts/fly_counts)*100
    half95ci=_np.sqrt( (percent_feeding*(100-percent_feeding))/fly_counts )
    percent_feeding_summary=_pd.DataFrame([percent_feeding,
                                          percent_feeding-half95ci,
                                          percent_feeding+half95ci]).T
    percent_feeding_summary.columns=['percent_feeding','ci_lower','ci_upper']
    return percent_feeding_summary


 #    #   ##   #    # ######    #####    ##   #      ###### ##### ##### ######  ####
 ##  ##  #  #  #   #  #         #    #  #  #  #      #        #     #   #      #
 # ## # #    # ####   #####     #    # #    # #      #####    #     #   #####   ####
 #    # ###### #  #   #         #####  ###### #      #        #     #   #           #
 #    # #    # #   #  #         #      #    # #      #        #     #   #      #    #
 #    # #    # #    # ######    #      #    # ###### ######   #     #   ######  ####


def _make_categorial_palette(df, group_by, pal='tab10'):
    """
    Create a categorical color palette.
    Pass a pandas DataFrame and the column to group by.
    """
    _cat_palette=_sns.color_palette( pal, n_colors=len(df[group_by].unique()) )
    return _cat_palette

def _make_sequential_palette(df, group_by):
    """
    Create a sequential color palette.
    Pass a pandas DataFrame and the column to group by.
    """
    _seq_palette=_sns.cubehelix_palette( n_colors=len(df[group_by].unique()) )
    return _seq_palette

def format_timecourse_xaxis(ax):
    """
    Convenience function to format a timecourse plot's x-axis.
    """
    ax.set_xlim(0,21600)
    ax.xaxis.set_ticks(range(0,25200,3600))
    ax.xaxis.set_minor_locator( _tk.MultipleLocator(base=1800) )
    ax.set_xlabel('Time (h)',fontsize=17)
    newlabels=[ str(int(t/3600)) for t in ax.xaxis.get_ticklocs(minor=False) ]
    ax.set_xticklabels(newlabels)
    ax.tick_params(axis='x', which='major',length=10)
    ax.tick_params(axis='x', which='minor',length=6)
