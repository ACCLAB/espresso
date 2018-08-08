#!/usr/bin/python
# -*-coding: utf-8 -*-
# Author: Joses Ho
# Email : joseshowh@gmail.com


def normalize_ylims(ax_arr, include_zero=False, draw_zero_line=False):
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



def compute_percent_feeding(all_feeds, all_flies, facets, start_hour, end_hour):
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

    filter_feeds = ((all_feeds.RelativeTime_s > start_hour * 3600) &
                   (all_feeds.RelativeTime_s < end_hour * 3600) &
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



def format_timecourse_xaxis(ax, min_x_seconds, max_x_seconds,
                            tick_interval_seconds=3600):
    """
    Convenience function to format a timecourse plot's x-axis.
    """
    import matplotlib.ticker as tk

    ax.set_xlim(min_x_seconds, max_x_seconds)

    ax.xaxis.set_ticks(range(int(min_x_seconds),
                             int(max_x_seconds + tick_interval_seconds/2),
                             tick_interval_seconds))
    ax.xaxis.set_minor_locator(tk.MultipleLocator(base=tick_interval_seconds/2))

    ax.set_xlabel('Time (h)')
    newlabels = [str(int(t/tick_interval_seconds))
                 for t in ax.xaxis.get_ticklocs(minor=False)]
    ax.set_xticklabels(newlabels)




def prep_feeds_for_contrast_plot(feeds, group_by, compare_by, color_by):
    """Convenience function to munge the feeds for contrast plotting."""

    import pandas as pd
    from .._munger import munger as munge

    plot_df = munge.volume_duration_munger(feeds, group_by, compare_by, color_by)

    for col in [*group_by, compare_by]:
        cat_from_feeds = feeds[col].cat.categories
        plot_df.loc[:, col] = pd.Categorical(plot_df[col],
                                            categories=cat_from_feeds,
                                            ordered=True)
    plot_df.sort_values([*group_by, compare_by], axis=0,
                        ascending=True, inplace=True)
    return plot_df


def parse_palette(palette, plot_groups, produce_colormap=False):

    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap, to_rgb
    import seaborn as sns

    if palette is None:
        palette = 'tab10'

    if isinstance(palette, str):
        if palette not in plt.colormaps():
            err1 = 'The specified `palette` {}'.format(palette)
            err2 = ' is not a matplotlib palette. Please check.'
            raise ValueError(err1 + err2)
        if produce_colormap:
            palette = ListedColormap(sns.color_palette(
                                        palette=palette,
                                        n_colors=len(plot_groups)),
                                    N=len(plot_groups))
        else:
            palette = dict(zip(plot_groups,
                               sns.color_palette(palette=palette,
                                                 n_colors=len(plot_groups))
                              )
                           )

    elif isinstance(palette, list):
        if len(plot_groups) != len(palette):
            errstring = ('The number of colors ' +
                         'in the palette {} '.format(palette) +
                         ' does not match the' +
                         'number of facets `{}`. '.format(plot_groups) +
                         ' Please check')
            raise ValueError(errstring)
        if produce_colormap:
            color_list = [to_rgb(a.strip()) for a in palette]
            palette = ListedColormap(color_list, N=len(plot_groups))
        else:
            palette = dict(zip(plot_groups,
                               palette[0: len(plot_groups)]
                              )
                           )

    elif isinstance(palette, dict):
        # check that all the keys in palette are found in the color column.
        col_grps = {k for k in plot_groups}
        pal_grps = {k for k in palette.keys()}
        not_in_pal = pal_grps.difference(col_grps)

        if len(not_in_pal) > 0:
            errstring = ('The custom palette keys {} '.format(not_in_pal) +
                   'are not found in `{}`. Please check.'.format(plot_groups))
            raise ValueError(errstring)

        if produce_colormap:
            palette = ListedColormap(palette.values(), N=len(plot_groups))

    return palette


def generic_contrast_plotter(plot_df, yvar,
                               color_by,
                               fig_size=None,
                               palette_type='categorical',
                               contrastplot_kwargs=None):

    import numpy as np
    import dabest
    from .._munger import munger as munge

    # Handle contrastplot keyword arguments.
    default_kwargs = dict(fig_size=(12,9),
                          float_contrast=False,
                          font_scale=1.4)
    if contrastplot_kwargs is None:
        contrastplot_kwargs = default_kwargs
    else:
        contrastplot_kwargs = munge.merge_two_dicts(default_kwargs,
            contrastplot_kwargs)

    # Select palette.
    if palette_type == 'categorical':
        color_palette = _make_categorial_palette(plot_df, color_by)
    elif palette_type == 'sequential':
        color_palette = _make_sequential_palette(plot_df, color_by)

    custom_pal = dict(zip(plot_df[color_by].unique(),
                          color_palette))

    # Properly arrange idx for grouping.
    unique_ids = plot_df.plot_groups_with_contrast.unique()
    split_idxs = np.array_split(unique_ids, len(plot_df.plot_groups.unique()))
    idx = [tuple(i) for i in split_idxs]

    # Make sure the ylims don't stretch below zero but still capture all
    # the datapoints.
    ymax = np.max(plot_df[yvar])*1.1

    f,b = dabest.plot(plot_df,
                      x='plot_groups_with_contrast',
                      y=yvar,
                      idx=idx,
                      color_col=color_by,
                      custom_palette=custom_pal,
                      swarm_ylim=(-ymax/70, ymax),
                      **contrastplot_kwargs)
    return f, b
