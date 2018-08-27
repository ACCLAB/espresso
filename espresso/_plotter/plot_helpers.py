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
    ax.plot(idx, mean, marker=marker, markerfacecolor=color, markersize=size,
            alpha=alpha )
    # Plot the CI.
    ax.plot([idx, idx], [cilow, cihigh], color=color, alpha=alpha,
            linestyle=ls, linewidth=lw )



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



# def _make_categorial_palette(df, group_by, pal='tab10'):
#     """
#     Create a categorical color palette.
#     Pass a pandas DataFrame and the column to group by.
#     """
#     import seaborn as sns
#
#     _cat_palette = sns.color_palette(pal, n_colors=len(df[group_by].unique()))
#     return _cat_palette
#
#
#
# def _make_sequential_palette(df, group_by):
#     """
#     Create a sequential color palette.
#     Pass a pandas DataFrame and the column to group by.
#     """
#     import seaborn as sns
#
#     _seq_palette = sns.cubehelix_palette(n_colors=len(df[group_by].unique()))
#     return _seq_palette



def format_timecourse_xaxis(ax, min_x_seconds, max_x_seconds,
                            tick_length=15, tick_pad=9,
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

    ax.tick_params(length=tick_length, pad=tick_pad)



def prep_feeds_for_contrast_plot(feeds, flies, added_labels,
                                group_by, compare_by, color_by,
                                start_hour, end_hour, type):
    """Convenience function to munge the feeds for contrast plotting."""

    import pandas as pd
    from .._munger import munger as munge

    from warnings import Warning
    if start_hour > 0.:
        raise Warning("Selecting a time slice not starting from 0 " +
                      "currently leads to nonfeeders getting dropped. " +
                      "A patch will be available in v0.4.2.")

    plot_df = munge.contrast_plot_munger(feeds, flies, added_labels,
                                         group_by, compare_by, color_by,
                                         start_hour, end_hour, type)

    if isinstance(group_by, str):
        to_make_cat = [group_by, compare_by]
    elif isinstance(group_by, (tuple, list)):
        to_make_cat = [*group_by, compare_by]

    for col in to_make_cat:
        cat_from_feeds = feeds[col].cat.categories
        plot_df.loc[:, col] = pd.Categorical(plot_df[col],
                                            categories=cat_from_feeds,
                                            ordered=True)

    plot_df.sort_values(to_make_cat, axis=0, ascending=True, inplace=True)

    return plot_df



def create_palette(palette, plot_groups, produce_colormap=False):
    """
    Create matplotlib-friendly palettes for plotting easily!
    matplotlib palettes:
    https://matplotlib.org/examples/color/colormaps_reference.html
    """
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



def check_time_window(start_hour, end_hour, expt_duration_hours):
    import numpy as np

    if end_hour is None:
        end_hour = expt_duration_hours

    elif np.any(np.array([start_hour, end_hour]) < 0):
        raise ValueError("Both `start_hour and `end_hour` must be positive.")

    return start_hour, end_hour



def get_unit_multiplier(unit, convert_from='nano'):
    """Convenience function to extract prefix from unit of volume."""
    from numpy import ceil, floor

    exponent_dict = {'centi': -2,  'milli': -3, 'micro': -6, 'nano': -9,
                    'pico': -12}

    convert_to = unit.strip().split('lit')[0]

    if convert_to not in exponent_dict.keys():
        units = [a + "liter" for a in exponent_dict.keys()]
        err1 = "{} is not a valid unit. ".format(unit)
        err2 = "Acceptable units are {}".format(units)
        raise ValueError(err1 + err2)

    exponent = exponent_dict[convert_from] - exponent_dict[convert_to]

    return 10 ** exponent



def get_new_prefix(unit):

    prefix_dict = {'centi': 'c',  'milli': 'm', 'micro': 'μ', 'nano': 'n',
                  'pico': 'p'}

    prefix = unit.strip().split('lit')[0]

    if prefix not in prefix_dict.keys():
        units = [a + "liter" for a in prefix_dict.keys()]
        err1 = "{} is not a valid unit. ".format(unit)
        err2 = "Acceptable units are {}".format(units)
        raise ValueError(err1 + err2)

    return prefix_dict[prefix]



def generic_contrast_plotter(plot_df, yvar, color_by, fig_size=None,
                             palette=None, title=None, contrastplot_kwargs=None):

    import numpy as np
    import dabest
    from .._munger import munger as munge
    import warnings
    warnings.filterwarnings("ignore", module='mpl_toolkits')

    # Handle contrastplot keyword arguments.
    default_kwargs = dict(float_contrast=False, font_scale=1.)
    if contrastplot_kwargs is None:
        contrastplot_kwargs = default_kwargs
    else:
        contrastplot_kwargs = munge.merge_two_dicts(default_kwargs,
            contrastplot_kwargs)

    if palette is None:
        palette = 'tab10'
    plot_groups = plot_df[color_by].unique()
    custom_pal = create_palette(palette, plot_groups)

    # Properly arrange idx for grouping.
    unique_ids = plot_df.plot_groups_with_contrast.unique()
    split_idxs = np.array_split(unique_ids, len(plot_df.plot_groups.unique()))
    idx = [tuple(i) for i in split_idxs]

    # Make sure the ylims don't stretch below zero but still capture all
    # the datapoints.
    ymax = np.max(plot_df[yvar]) * 1.1

    f,b = dabest.plot(plot_df, x='plot_groups_with_contrast',
                      y=yvar, idx=idx, color_col=color_by,
                      custom_palette=custom_pal,
                      fig_size=fig_size,
                      swarm_ylim=(-ymax/10, ymax),
                      **contrastplot_kwargs)
    return f, b
