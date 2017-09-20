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
import seaborn as _sns
import bootstrap_contrast as _bsc

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

def latency_ingestion_plots(feeds,first_x_min=180):
    """
    Convenience function to enable ipython interact to modify contrast plots
    for the latency to feed, and total volume ingested, in the `first_x_min`.
    """
    allfeeds_timewin=feeds[feeds.feed_time_s<first_x_min*60]

    latency=_pd.DataFrame(allfeeds_timewin[['FlyID','starved_time',
                                           'feed_time_s','feed_duration_s']].\
                         dropna().\
                         groupby(['starved_time','FlyID']).\
                         apply(_np.min).drop(['starved_time','FlyID','feed_duration_s'],axis=1).\
                         to_records())
    latency['feed_time_min']=latency['feed_time_s']/60
    latency.rename(columns={"feed_time_min": "Latency to\nfirst feed (min)"}, inplace=True)
    max_latency=_np.round(latency.max()["Latency to\nfirst feed (min)"],decimals=-2)

    total_ingestion=_pd.DataFrame(allfeeds_timewin[['FlyID','starved_time','FeedVol_nl']].\
                                 dropna().\
                                 groupby(['starved_time','FlyID']).\
                                 sum().to_records())
    total_ingestion.rename(columns={"FeedVol_nl": "Total Ingestion (nl)"}, inplace=True)
    max_ingestion=_np.round(total_ingestion.max()["Total Ingestion (nl)"],decimals=-2)

    f1,b1=_bsc.contrastplot(data=latency,x='starved_time',y="Latency to\nfirst feed (min)",
                          swarm_ylim=(-20,max_latency),
                          **bs_kwargs)
    f1.suptitle('Latency to feed in first {0} min'.format(first_x_min),fontsize=20)
    _plt.show()
    print(b1)

    f2,b2=_bsc.contrastplot(data=total_ingestion,
                          x='starved_time',y='Total Ingestion (nl)',
                          swarm_ylim=(-20,max_ingestion),
                          **bs_kwargs)
    f2.suptitle('Total Volume (nl) ingested in first {0} min'.format(first_x_min),fontsize=20)
    _plt.show()
    print(b2)

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

def timecourse_feed_vol(df, group_by, resample_by='10min'):
    """
    Produces a Pandas DataFrame with the feed volume per group
    in `group_by`, for each time interval as indicated by `resample_by`.
    """
    temp=df.copy()

    if isinstance(group_by, str):
        group_by=[group_by]

    out_cols=['RelativeTime_s','FeedVol_µl']
    out_cols.extend(group_by)

    out=_pd.DataFrame( temp.\
                        groupby(group_by).\
                        resample(resample_by,on='RelativeTime_s').\
                        sum().to_records() )
    out=out.loc[:,out_cols]
    out.fillna(0,inplace=True)
    out['feed_time_s']=out.RelativeTime_s.dt.hour*3600+\
                        out.RelativeTime_s.dt.minute*60+\
                        out.RelativeTime_s.dt.second
    return out

def timecourse_feed_count(df, group_by, resample_by='10min'):
    """
    Produces a Pandas DataFrame with the feed volume per group
    in `group_by`, for each time interval as indicated by `resample_by`.
    """
    temp=df.copy()

    if isinstance(group_by, str):
        group_by=[group_by]

    out_cols=['RelativeTime_s','FeedVol_µl']
    out_cols.extend(group_by)

    out=_pd.DataFrame( temp.\
                        groupby(group_by).\
                        resample(resample_by,on='RelativeTime_s').\
                        sum().to_records() )
    out=out.loc[:,out_cols]
    out.fillna(0,inplace=True)
    out['feed_time_s']=out.RelativeTime_s.dt.hour*3600+\
                        out.RelativeTime_s.dt.minute*60+\
                        out.RelativeTime_s.dt.second
    return out
