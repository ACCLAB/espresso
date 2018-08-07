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
        self.__expt_end_time = plotter._experiment.expt_duration_minutes


    def __cumulative_plotter(self, yvar, row, col, time_col,
                             min_time_hour, max_time_hour,
                             ylim, color_by, palette=None,
                             resample_by='5min', gridlines=True):


        import matplotlib.pyplot as plt
        import seaborn as sns
        from . import plot_helpers as plothelp
        from .._munger import munger as munge

        # Handle the group_by and color_by keywords.
        munge.check_group_by_color_by(col, row, color_by, self.__feeds)

        # Resample (aka bin by time).
        resamp_feeds = munge.groupby_resamp_sum(self.__feeds, resample_by)

        # Perform cumulative summation.
        plotdf = munge.cumsum_for_cumulative(resamp_feeds)


        # Parse keywords.
        if palette is None:
            palette = 'tab10'

        min_time_sec = min_time_hour * 3600
        max_time_sec = max_time_hour * 3600

        df_win = plotdf[(plotdf.time_s >= min_time_sec) &
                        (plotdf.time_s <= max_time_sec)]

        sns.set(style='ticks')

        g = sns.FacetGrid(b, row=row, col=col,
                          hue=color_by, legend_out=True,
                          palette=palette,
                          xlim=(min_time_sec, max_time_sec),
                          sharex=False, sharey=True,
                          height=5, aspect=1.5,
                          gridspec_kws={'hspace':0.5, 'wspace':0.2})

        g.map(sns.lineplot, time_col, yvar, ci=95)
        g.set_titles("{row_var} = {row_name}; {col_var} = {col_name}",
                     size=20)
        g.add_legend(fontsize=18)
        plt.legend

        for j, ax in enumerate(g.axes.flat):

            plothelp.format_timecourse_xaxis(ax, min_time_sec, max_time_sec)
            ax.tick_params(which='major', length=12, pad=12, labelsize=15)
            ax.tick_params(which='minor', length=6)
            ax.set_ylabel(ax.get_ylabel(), fontsize=18)

            ax.set_ylim(0, ax.get_ylim()[1])
            ax.yaxis.set_tick_params(labelleft=True)

            if gridlines:
                ax.xaxis.grid(True, which='major',
                              linestyle='dotted',
                              alpha=0.75)


        sns.despine(fig=g.fig, offset={'left':5, 'bottom': 5})
        plt.tight_layout()
        sns.set() # reset style.

        # End and return the FacetGrid.
        return g


    def consumption(self, row, col, color_by,
                    max_time_hour, min_time_hour=0,
                    ylim=None, palette=None,
                    resample_by='5min',
                    gridlines=True):
        """
        Produces a cumulative line plot depicting the average total volume
        consumed per fly for the entire assay. The plot will be tiled
        horizontally according to the `col`, horizontally according to the
        category `row`, and will be colored according to the category `color_by`.
        Feed volumes will be binned by the duration in `resample_by`.

        keywords
        --------
        col, row: string
            Accepts a categorical column in the espresso object. Each group in
            this column will be plotted on along the desired axis.

        color_by: string
            Accepts a categorical column in the espresso object. Each group in
            this column will be colored seperately, and stacked as an area plot.

        max_time_hour, min_time_hour: float, default <required>, 0
            Enter the time window (in hours) you want to plot here.

        ylim: tuple, default None
            Enter the desired ylims here.

        palette: matplotlib palette

        resample_by: string, default '5min'
            The time frequency used to bin the timecourse data. For the format,
            please see
            http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases

        fig_size: tuple (width, height), default None
            The size of the final figure, in inches.

        gridlines boolean, default True
            Whether or not vertical gridlines are displayed at each hour.

        Returns
        -------
        seaborn FacetGrid object
        """

        out = self.__cumulative_plotter(yvar='Cumulative Volume (nl)',
                                        col=col,
                                        row=row,
                                        color_by=color_by,
                                        time_col='time_s',
                                        min_time_hour=min_time_hour,
                                        max_time_hour=max_time_hour,
                                        resample_by=resample_by,
                                        ylim=ylim,
                                        fig_size=fig_size,
                                        gridlines=gridlines)
        return out

    def feed_count(self, row, col, color_by,
                    max_time_hour, min_time_hour=0,
                    ylim=None, palette=None,
                    resample_by='5min',
                    gridlines=True):
        """
        Produces a cumulative line plot depicting the average total feed count
        consumed per fly for the entire assay. The plot will be tiled
        horizontally according to the `col`, horizontally according to the
        category `row`, and will be colored according to the category `color_by`.
        Feed counts will be binned by the duration in `resample_by`.

        keywords
        --------
        col, row: string
            Accepts a categorical column in the espresso object. Each group in
            this column will be plotted on along the desired axis.

        color_by: string
            Accepts a categorical column in the espresso object. Each group in
            this column will be colored seperately, and stacked as an area plot.

        max_time_hour, min_time_hour: float, default <required>, 0
            Enter the time window (in hours) you want to plot here.

        ylim: tuple, default None
            Enter the desired ylims here.

        palette: matplotlib palette

        resample_by: string, default '5min'
            The time frequency used to bin the timecourse data. For the format,
            please see
            http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases

        fig_size: tuple (width, height), default None
            The size of the final figure, in inches.

        gridlines boolean, default True
            Whether or not vertical gridlines are displayed at each hour.

        Returns
        -------
        seaborn FacetGrid object
        """

        out = self.__cumulative_plotter(yvar='Cumulative Feed Count',
                                        col=col,
                                        row=row,
                                        color_by=color_by,
                                        time_col='time_s',
                                        min_time_hour=min_time_hour,
                                        max_time_hour=max_time_hour,
                                        resample_by=resample_by,
                                        ylim=ylim,
                                        fig_size=fig_size,
                                        gridlines=gridlines)
        return out
