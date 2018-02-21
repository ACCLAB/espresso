#!/usr/bin/python
# -*-coding: utf-8 -*-
# Author: Joses Ho
# Email : joseshowh@gmail.com

"""
timecourse plot functions for espresso objects.
"""

# import sys as _sys
# _sys.path.append("..") # so we can import espresso from the directory above.


class timecourse_plotter():
    """
    timecourse plotting class for espresso object.
    """


    def __init__(self, plotter): # pass along an espresso_plotter instance.
        self.__feeds = plotter._experiment.feeds.copy()
        self.__expt_end_time = plotter._experiment.expt_duration_seconds

    def __pivot_for_plot(self, resampdf, row, col, color_by):
        import pandas as pd

        group_by_cols = [a for a in [row, col, color_by, 'time_s']
                        if a is not None]
        out = pd.DataFrame(resampdf.groupby(group_by_cols).sum())
        out.drop('FlyCountInChamber', axis=1, inplace=True)

        return out


    def __timecourse_plotter(self,
                             yvar,
                             col=None,
                             row=None,
                             color_by=None,
                             resample_by='5min',
                             fig_size=None,
                             gridlines=True,
                             ax=None):

        import numpy as np
        import pandas as pd
        import matplotlib.pyplot as plt
        import seaborn as sns
        from . import plot_helpers as plt_helper
        from .._munger import munger as munge

        feeds = self.__feeds.copy()

        # Handle the group_by and color_by keywords.
        col, row, color_by = munge.check_group_by_color_by(col, row,
                                            color_by, feeds)

        ## DICTIONARY FOR MATCHING YVAR TO APPROPRIATE YLABEL.
        yvar_ylabel_dict = {'AverageFeedVolumePerFly_µl':'Average Feed Volume Per Fly (µl)',
                           'AverageFeedCountPerFly':'Average Feed Count Per Fly',
                           'AverageFeedSpeedPerFly_µl/s':'Average Feed Speed Per Fly (µl/s)'}

        ylab = yvar_ylabel_dict[yvar]

        resamp_feeds = munge.groupby_resamp_sum(feeds, '5min')
        resamp_feeds_sum = munge.sum_for_timecourse(resamp_feeds)
        plotdf = self.__pivot_for_plot(resamp_feeds_sum, row, col, color_by)

        # print("Coloring time course by {0}".format(color_by))
        if row is not None:
            # print("Plotting rows by {0}".format(row))
            row_count = int(len(feeds[row].cat.categories))
        else:
            row_count = 1
        if col is not None:
            # print("Plotting columns by {0}".format(col))
            col_count = int(len(feeds[col].cat.categories))
        else:
            col_count = 1


        # DICTIONARY FOR MATCHING YVAR TO APPROPRIATE YLABEL.
        yvar_ylabel_dict = {'AverageFeedVolumePerFly_µl':'Average Feed Volume Per Fly (µl)',
                           'AverageFeedCountPerFly':'Average Feed Count Per Fly',
                           'AverageFeedSpeedPerFly_µl/s':'Average Feed Speed Per Fly (µl/s)'}


        # Initialise figure.
        sns.set(style='ticks',context='poster')
        if fig_size is None:
            x_inches = 10 * col_count
            y_inches = 7 * row_count
        else:
            if isinstance(fig_size, tuple) or isinstance(fig_size, list):
                x_inches = fig_size[0]
                y_inches = fig_size[1]
            else:
                raise TypeError('Please make sure figsize is a tuple of the '
                'form (w,h) in inches.')

        if ax is None:
            fig,axx = plt.subplots(nrows=row_count, ncols=col_count,
                                   figsize=(x_inches,y_inches),
                                   gridspec_kw={'wspace':0.3,
                                               'hspace':0.3})
        else:
            axx = ax

        if row is not None and col is not None:
            for r, row_ in enumerate(feeds[row].cat.categories):
                for c, col_ in enumerate(feeds[col].cat.categories):
                    plot_ax = axx[r, c] # the axes to plot on.

                    # Reshape the current data to be plotted.
                    current_plot_df = plotdf.loc[(row_, col_), yvar]

                    # We unstack and transpose to create a 'long' dataset,
                    # where each column is a timecourse dataset to be plotted.
                    current_plot_df = current_plot_df.unstack().T

                    # Create the plot.
                    current_plot_df.plot.area(ax=plot_ax, stacked=True)
                    plot_ax.set_title("{}; {}".format(row_, col_))

        else:
            # We only have one dimension here.
            plot_dim = [d for d in [row, col] if d is not None][0]
            for j, dim_ in enumerate(feeds[plot_dim].cat.categories):

                plot_ax = axx[j]

                current_plot_df = plotdf.loc[dim_, yvar]
                current_plot_df = current_plot_df.unstack().T

                current_plot_df.plot.area(ax=plot_ax, stacked=True)
                plot_ax.set_title(dim_)

        # Normalize all the y-axis limits.
        if row_count + col_count > 1:
            plt_helper.normalize_ylims(axx.flatten(),
                                     include_zero=True)
            for plot_ax in axx.flatten():
                # Format x-axis.
                plt_helper.format_timecourse_xaxis(plot_ax, 21600)
                # Set label for y-axis.
                plot_ax.set_ylabel(ylab)
                # Plot vertical grid lines if desired.
                if gridlines:
                    plot_ax.xaxis.grid(True, which='major',
                                       linestyle='dotted', #linewidth=1,
                                       alpha=0.5)
                # Despine and offset each axis.
                sns.despine(ax=plot_ax, trim=True, offset=3)

        for ax in axx.flatten()[:-1]:
            ax.legend().set_visible(False)

        axx.flatten()[-1].legend(loc='upper left',
                                 title=color_by,
                                 bbox_to_anchor=(-0.05, -0.15))

        # End and return the figure.
        if ax is None:
            return axx




    def feed_volume(self,
                    col=None,
                    row=None,
                    color_by=None,
                    resample_by='5min',
                    fig_size=None,
                    gridlines=True,
                    ax=None):
        """
        Produces a timecourse area plot depicting the average feed volume per
        fly for the entire assay. The plot will be tiled horizontally
        according to the `col`, horizontally according to the category `row`,
        and will be colored according to the category `color_by`.
        Feed volumes will be binned by the duration in `resample_by`.

        keywords
        --------
        col, row: string, default None
            Accepts a categorical column in the espresso object. Each group in
            this column will be plotted on along the desired axis.

        color_by: string, default None
            Accepts a categorical column in the espresso object. Each group in
            this column will be colored seperately, and stacked as an area plot.

        resample_by: string, default '5min'
            The time frequency used to bin the timecourse data. For the format,
            please see
            http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases

        fig_size: tuple (width, height), default None
            The size of the final figure, in inches.

        gridlines boolean, default True
            Whether or not vertical gridlines are displayed at each hour..

        ax: array of matplotlib Axes objects, default None
            Given an array of Axes, each category (as dictacted by group_by)
            will be plotted respectively.

        Returns
        -------
        matplotlib AxesSubplot(s)
        """
        out = self.__timecourse_plotter('AverageFeedVolumePerFly_µl' ,
                                        row=row,
                                        col=col,
                                        color_by=color_by,
                                        resample_by=resample_by,
                                        fig_size=fig_size,
                                        gridlines=gridlines,
                                        ax=ax)

        return out




    def feed_count(self,
                    col=None,
                    row=None,
                    color_by=None,
                    resample_by='5min',
                    fig_size=None,
                    gridlines=True,
                    ax=None):
        """
        Produces a timecourse area plot depicting the average feed count per fly
        for the entire assay. The plot will be tiled horizontally
        according to the `col`, horizontally according to the category `row`,
        and will be colored according to the category `color_by`.
        Feed counts will be binned by the duration in `resample_by`.

        keywords
        --------
        col, row: string, default None
            Accepts a categorical column in the espresso object. Each group in
            this column will be plotted on along the desired axis.

        color_by: string, default None
            Accepts a categorical column in the espresso object. Each group in
            this column will be colored seperately, and stacked as an area plot.

        resample_by: string, default '5min'
            The time frequency used to bin the timecourse data. For the format,
            please see
            http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases

        fig_size: tuple (width, height), default None
            The size of the final figure, in inches.

        gridlines boolean, default True
            Whether or not vertical gridlines are displayed at each hour..

        ax: array of matplotlib Axes objects, default None
            Given an array of Axes, each category (as dictacted by group_by)
            will be plotted respectively.

        Returns
        -------
        matplotlib AxesSubplot(s)
        """
        out = self.__timecourse_plotter('AverageFeedCountPerFly',
                                        row=row,
                                        col=col,
                                        color_by=color_by,
                                        resample_by=resample_by,
                                        fig_size=fig_size,
                                        gridlines=gridlines,
                                        ax=ax)
        return out




    def feed_speed(self,
                    col=None,
                    row=None,
                    color_by=None,
                    resample_by='5min',
                    fig_size=None,
                    gridlines=True,
                    ax=None):
        """
        Produces a timecourse area plot depicting the average feed speed per fly
        in µl/s for the entire assay. The plot will be tiled horizontally
        according to the `col`, horizontally according to the category `row`,
        and will be colored according to the category `color_by`.
        Feed speeds will be binned by the duration in `resample_by`.

        keywords
        --------
        col, row: string, default None
            Accepts a categorical column in the espresso object. Each group in
            this column will be plotted on along the desired axis.

        color_by: string, default None
            Accepts a categorical column in the espresso object. Each group in
            this column will be colored seperately, and stacked as an area plot.

        resample_by: string, default '5min'
            The time frequency used to bin the timecourse data. For the format,
            please see
            http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases

        fig_size: tuple (width, height), default None
            The size of the final figure, in inches.

        gridlines boolean, default True
            Whether or not vertical gridlines are displayed at each hour..

        ax: array of matplotlib Axes objects, default None
            Given an array of Axes, each category (as dictacted by group_by)
            will be plotted respectively.

        Returns
        -------
        matplotlib AxesSubplot(s)
        """
        out = self.__timecourse_plotter('AverageFeedSpeedPerFly_µl/s',
                                        row=row,
                                        col=col,
                                        color_by=color_by,
                                        resample_by=resample_by,
                                        fig_size=fig_size,
                                        gridlines=gridlines,
                                        ax=ax)
        return out
