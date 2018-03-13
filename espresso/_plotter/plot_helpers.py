#!/usr/bin/python
# -*-coding: utf-8 -*-
# Author: Joses Ho
# Email : joseshowh@gmail.com


def normalize_ylims(ax_arr,include_zero = False,draw_zero_line = False):
    """Custom function to normalize ylims for an array of axes."""
    import numpy as np

    ymins = list()
    ymaxs = list()

    for ax in ax_arr:
        ymin = ax.get_ylim()[0]
        ymax = ax.get_ylim()[1]
        ymins.append(ymin)
        ymaxs.append(ymax)
    new_min = np.min(ymins)
    new_max = np.max(ymaxs)

    if include_zero:
        if new_max < 0:
            new_max = 0
        if new_min > 0:
            new_min = 0

    for ax in ax_arr:
        ax.set_ylim(new_min,new_max)

    if draw_zero_line:
        for ax in ax_arr:
            ax.axhline(y = 0,linestyle='solid',linewidth = 0.5,color='k')

def meanci(mean, cilow, cihigh, idx, ax,
            alpha=0.8, marker='o',color='black',
            size=8, ls='solid',lw = 1.2):
    """Custom function to normalize plot the mean and CI as a dot and a \
    vertical line, respectively."""
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
    import numpy as np
    if not exponent:
        exponent = int(np.floor(np.log10(abs(num))))
    coeff = round(num / float(10**exponent), decimal_digits)
    if not precision:
        precision = decimal_digits

    return r"${0:.{2}f}\times10^{{{1:d}}}$".format(coeff, exponent, precision)

def compute_percent_feeding(all_feeds, all_flies, facets, start=0, end=60):
    """
    Used to compute the percent of flies feeding from
    a processed dataset of feedlogs.
    """
    import numpy as np
    import pandas as pd

    if isinstance(facets, list):
        grpby = facets
        feed_boolean_grpby = grpby.copy()
        feed_boolean_grpby.append('FlyID')
    else:
        raise TypeError('`facet` needs to be a list.')
    try:
        flies_group_by = [a for a in facets if a in all_flies.columns]
        fly_counts = all_flies.groupby(flies_group_by)\
                              .count()\
                              .FlyID
    except ValueError: # flies_group_by is []
        fly_counts = len(all_flies)

    filter_feeds = ((all_feeds.RelativeTime_s > start*60) &
                   (all_feeds.RelativeTime_s < end*60) &
                   (all_feeds.Valid))
    feeds_timewin = all_feeds[filter_feeds]
    # To count total flies that fed, I adapted the methods here:
    # https://stackoverflow.com/questions/8364674/python-numpy-how-to-count-the-number-of-true-elements-in-a-bool-array
    feed_boolean_by_fly = ~np.isnan(feeds_timewin\
                                    .groupby(feed_boolean_grpby)\
                                    .sum()['FeedVol_µl'])
    fly_feed_counts = feed_boolean_by_fly\
                        .apply(np.count_nonzero)\
                        .groupby(grpby).sum()
    # Proportion code taken from here:
    # https://onlinecourses.science.psu.edu/stat100/node/56
    percent_feeding = (fly_feed_counts / fly_counts) * 100
    half95ci = np.sqrt((percent_feeding * (100 - percent_feeding)) / fly_counts)
    percent_feeding_summary = pd.DataFrame([percent_feeding,
                                          percent_feeding-half95ci,
                                          percent_feeding+half95ci]).T
    percent_feeding_summary.columns = ['percent_feeding','ci_lower','ci_upper']
    return percent_feeding_summary


def _make_categorial_palette(df, group_by, pal='tab10'):
    """
    Create a categorical color palette.
    Pass a pandas DataFrame and the column to group by.
    """
    import seaborn as sns

    _cat_palette = sns.color_palette(pal, n_colors=len(df[group_by].unique()))
    return _cat_palette



def _make_sequential_palette(df, group_by):
    """
    Create a sequential color palette.
    Pass a pandas DataFrame and the column to group by.
    """
    import seaborn as sns

    _seq_palette = sns.cubehelix_palette(n_colors=len(df[group_by].unique()))
    return _seq_palette



def format_timecourse_xaxis(ax, max_x):
    """
    Convenience function to format a timecourse plot's x-axis.
    """
    import matplotlib.ticker as tk

    ax.set_xlim(0, max_x)
    ax.xaxis.set_ticks(range(0, max_x + 3600, 3600))
    ax.xaxis.set_minor_locator(tk.MultipleLocator(base=1800))
    ax.set_xlabel('Time (h)',fontsize = 17)
    newlabels = [str(int(t/3600)) for t in ax.xaxis.get_ticklocs(minor=False)]
    ax.set_xticklabels(newlabels)
    ax.tick_params(axis='x', which='major', length=10)
    ax.tick_params(axis='x', which='minor', length=6)
