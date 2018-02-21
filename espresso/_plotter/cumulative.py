#!/usr/bin/python
# -*-coding: utf-8 -*-
# Author: Joses Ho
# Email : joseshowh@gmail.com

"""
cumulative plotting functions for espresso objects.
"""



class cumulative_plotter:
    """
    cumulative plotting class for espresso object.
    """


    def __init__(self, plotter): # pass along an espresso_plotter instance.
        self.__feeds = plotter._experiment.feeds.copy()
        self.__expt_end_time = plotter._experiment.expt_duration_seconds

    def __cumulative_plotter(self,
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

        # Handle the group_by and color_by keywords.
        col, row, color_by = munge.check_group_by_color_by(col, row,
                                            color_by, self.__feeds)


        resamp_feeds = munge.groupby_resamp_sum(self.__feeds, resample_by)
        plotdf = munge.cumsum_for_cumulative(resamp_feeds)

        # Change relevant columns to categorical.
        try:
            plotdf.loc[:, 'Status'] = pd.Categorical(plotdf.loc[:, 'Status'],
                                                categories=['Sibling','Offspring'],
                                                ordered=True)
        except KeyError:
            pass

        # Change relevant columns to categorical.
        for column in ['Genotype','Temperature',
                       'Sex','FoodChoice']:
            try:
                cats = np.sort(plotdf[column].unique())
                plotdf.loc[:, column] = pd.Categorical(plotdf[column],
                                                       categories=cats,
                                                       ordered=True)
            except KeyError:
                pass

        # print("Coloring cumulative plot by {0}".format(color_by))
        if row is not None:
            # print("Plotting rows by {0}".format(row))
            row_count = int(len(plotdf[row].cat.categories))
        else:
            row_count = 1
        if col is not None:
            # print("Plotting columns by {0}".format(col))
            col_count = int(len(plotdf[col].cat.categories))
        else:
            col_count = 1

        # Compute means
        group_by_cols = [a for a in [col, row, color_by,'time_s']
                        if a is not None]
        plotdf_groupby = plotdf.groupby(group_by_cols)
        plotdf_mean = plotdf_groupby.mean().unstack()[yvar].T

        # Compute CIs
        plotdf_halfci = plotdf_groupby.sem().unstack()[yvar].T * 1.96
        lower_ci = plotdf_mean - plotdf_halfci
        upper_ci = plotdf_mean + plotdf_halfci
        # Make sure no CI drops below zero.
        lower_ci[lower_ci < 0] = 0

        # groupby_grps = plotdf[group_by].cat.categories.tolist()
        # num_plots = int(len(groupby_grps))


        # Initialise figure.
        sns.set(style='ticks',context='poster',font_scale=1.25)
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
            fig, axx = plt.subplots(nrows=row_count, ncols=col_count,
                                    figsize=(x_inches, y_inches),
                                    gridspec_kw={'wspace':0.3,
                                                 'hspace':0.3})
        else:
            axx = ax

        if row is not None and col is not None:
             for r, row_ in enumerate(plotdf[row].cat.categories):
                for c, col_ in enumerate(plotdf[col].cat.categories):
                    plot_ax = axx[r, c] # the axes to plot on.
                    # Plot the means as cumulative lines.
                    plotdf_mean[(col_, row_)].plot(ax=plot_ax, lw=1)
                    # Now, plot the CIs individually.
                    for yvar_type in lower_ci[(col_, row_)].columns:
                        plot_ax.fill_between(plotdf_mean.index,
                                             lower_ci[(col_, row_, yvar_type)],
                                             upper_ci[(col_, row_, yvar_type)],
                                             alpha=0.25)
                    plot_ax.set_title("{}; {}".format(row_, col_))
        else:
            # We only have one dimension here.
            plot_dim = [d for d in [row, col] if d is not None][0]
            for j, dim_ in enumerate(plotdf[plot_dim].cat.categories):
                plot_ax = axx[j] # the axes to plot on.
                # Plot the means as cumulative lines.
                plotdf_mean[(dim_)].plot(ax=plot_ax, lw=1)
                # Now, plot the CIs individually.
                for yvar_type in lower_ci[(dim_)].columns:
                    plot_ax.fill_between(plotdf_mean.index,
                                         lower_ci[(dim_, yvar_type)],
                                         upper_ci[(dim_, yvar_type)],
                                         alpha=0.25)
                plot_ax.set_title(dim_)

        # Normalize all the y-axis limits.
        if row_count + col_count > 1:
            plt_helper.normalize_ylims(axx.flatten(),
                                       include_zero=True)
            for plot_ax in axx.flatten():
                # Format x-axis.
                plt_helper.format_timecourse_xaxis(plot_ax,
                                                   self.__expt_end_time)
                # Set label for y-axis.
                plot_ax.set_ylabel(yvar)
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

    def consumption(self,
                    col=None,
                    row=None,
                    color_by=None,
                    resample_by='5min',
                    fig_size=None,
                    gridlines=True,
                    ax=None):
        """
        Produces a cumulative line plot depicting the average total volume
        consumed per fly for the entire assay. The plot will be tiled
        horizontally according to the `col`, horizontally according to the
        category `row`, and will be colored according to the category `color_by`.
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
            Whether or not vertical gridlines are displayed at each hour.

        ax: array of matplotlib Axes objects, default None
            Given an array of Axes, each category(as dictacted by group_by)
            will be plotted respectively.

        Returns
        -------
        matplotlib AxesSubplot(s)
        """
        out = self.__cumulative_plotter(yvar='Cumulative Volume (nl)',
                                        col=col,
                                        row=row,
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
        Produces a cumulative line plot depicting the average total feed count
        consumed per fly for the entire assay. The plot will be tiled
        horizontally according to the `col`, horizontally according to the
        category `row`, and will be colored according to the category `color_by`.
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
            Whether or not vertical gridlines are displayed at each hour.

        ax: array of matplotlib Axes objects, default None
            Given an array of Axes, each category(as dictacted by group_by)
            will be plotted respectively.

        Returns
        -------
        matplotlib AxesSubplot(s)
        """
        out = self.__cumulative_plotter(yvar='Cumulative Feed Count',
                                        col=col,
                                        row=row,
                                        color_by=color_by,
                                        resample_by=resample_by,
                                        fig_size=fig_size,
                                        gridlines=gridlines,
                                        ax=ax)
        return out
