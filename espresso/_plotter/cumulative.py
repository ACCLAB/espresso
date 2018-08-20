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
        self.__flies = plotter._experiment.flies
        self.__expt_end_time = plotter._experiment.expt_duration_minutes
        # try:
        #     self.__added_labels = plotter._experiment.added_labels
        # except AttributeError:
        #     self.__added_labels = [None]


    def __cumulative_plotter(self, yvar, row, col, time_col,
                             start_hour, end_hour,  ylim, color_by,
                             volume_unit=None, font_scale=1.5,
                             height=10, width=10, palette=None,
                             resample_by='5min', gridlines=True):

        import sys
        import matplotlib.pyplot as plt
        from pandas import merge
        import seaborn as sns
        from . import plot_helpers as plothelp
        from .._munger import munger as munge

        import warnings
        warnings.filterwarnings("ignore", category=FutureWarning) # from scipy
        warnings.filterwarnings("ignore", category=UserWarning) # from matplotlib

        # Handle the group_by and color_by keywords.
        sys.stdout.write('Munging.')
        munge.check_group_by_color_by(col, row, color_by, self.__feeds)

        # Resample (aka bin by time).
        sys.stdout.write('.')
        resamp_feeds = munge.groupby_resamp_sum(self.__feeds, resample_by)

        # Perform cumulative summation.
        sys.stdout.write('.')
        plotdf = munge.cumsum_for_cumulative(resamp_feeds)

        # merge with metadata.
        sys.stdout.write('.')
        plotdf = merge(left=self.__flies, right=plotdf,
                       left_on='FlyID', right_on='FlyID')


        if volume_unit is not None:
            if volume_unit.strip().split('lit')[0] == 'micro':
                y = yvar
            else:
                multiplier = plothelp.get_unit_multiplier(volume_unit,
                                                          convert_from='micro')
                new_unit = plothelp.get_new_prefix(volume_unit)
                y = 'Cumulative Volume ({}l)'.format(new_unit)
                plotdf[y] = plotdf[yvar] * multiplier
        else:
            y = yvar

        # Parse keywords.
        if palette is None:
            palette = 'tab10'

        # Convert hour input to seconds.
        min_time_sec = start_hour * 3600
        max_time_sec = end_hour * 3600

        # Filter the cumsum dataframe for the desired time window.
        sys.stdout.write('.')
        df_win = plotdf[(plotdf.time_s >= min_time_sec) &
                        (plotdf.time_s <= max_time_sec)]

        # initialise FacetGrid.
        sns.set(style='ticks', context='poster')

        sys.stdout.write('\nPlotting.')
        g = sns.FacetGrid(df_win, row=row, col=col,
                          hue=color_by, legend_out=True,
                          palette=palette,
                          xlim=(min_time_sec, max_time_sec),
                          sharex=False, sharey=True,
                          height=height, aspect=width/height,
                          gridspec_kws={'hspace':0.3, 'wspace':0.3}
                          )

        sys.stdout.write('.')
        g.map(sns.lineplot, time_col, y, ci=95)

        if row is None:
            g.set_titles("{col_var} = {col_name}")
        elif col is None:
            g.set_titles("{row_var} = {row_name}")
        elif row is not None and col is not None:
            g.set_titles("{row_var} = {row_name}\n{col_var} = {col_name}")

        g.add_legend()

        # Aesthetic tweaks.
        sys.stdout.write('.')
        for j, ax in enumerate(g.axes.flat):

            plothelp.format_timecourse_xaxis(ax, min_time_sec, max_time_sec)
            ax.tick_params(which='major', length=12, pad=12)
            ax.tick_params(which='minor', length=6)
            ax.set_ylabel(ax.get_ylabel())

            ax.set_ylim(0, ax.get_ylim()[1])
            ax.yaxis.set_tick_params(labelleft=True)

            if gridlines:
                ax.xaxis.grid(True, which='major',
                              linestyle='dotted',
                              alpha=0.75)

        sys.stdout.write('.')
        sns.despine(fig=g.fig, offset={'left':5, 'bottom': 5})
        sns.set() # reset style.

        # End and return the FacetGrid.
        return g


    def consumption(self, row, col, color_by,
                    end_hour, start_hour=0,
                    ylim=None, palette=None,
                    resample_by='5min', volume_unit='nanoliter',
                    height=10, width=10,
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
            this column will be plotted on along the desired axis. If None,
            the plots will be arranged in the other orthogonal dimension.

        color_by: string
            Accepts a categorical column in the espresso object. Each group in
            this column will be colored seperately, and stacked as an area plot.

        end_hour, start_hour: float, default <required>, 0
            Enter the time window (in hours) you want to plot here.

        ylim: tuple, default None
            Enter the desired ylims here.

        palette: matplotlib palette OR a list of named matplotlib colors.
            Full list of matplotlib palettes
            https://matplotlib.org/examples/color/colormaps_reference.html
            Full list of named matplotlib colors
            https://matplotlib.org/gallery/color/named_colors.html

        resample_by: string, default '5min'
            The time frequency used to bin the timecourse data. For the format,
            please see
            http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases

        volume_unit: string, default 'nanoliter'
            Accepts 'centiliter' (10^-2 liters), 'milliliter (10^-3 liters)',
            'microliter'(10^-6 liters), 'nanoliter' (10^-9 liters), and
            'picoliter' (10^-12 liters).

        font_scale: float, default 1.5
            The fontsize will be multiplied by this amount.

        height, width: float, default 10, 10
            The height and width of each panel in inches.

        gridlines boolean, default True
            Whether or not vertical gridlines are displayed at each hour.

        Returns
        -------
        seaborn FacetGrid object
        """
        from . import plot_helpers as plothelp

        out = self.__cumulative_plotter(yvar='Cumulative Volume (µl)',
                                        col=col,
                                        row=row,
                                        color_by=color_by,
                                        time_col='time_s',
                                        volume_unit=volume_unit,
                                        start_hour=start_hour,
                                        end_hour=end_hour,
                                        palette=palette,
                                        resample_by=resample_by,
                                        ylim=ylim, height=height, width=width,
                                        gridlines=gridlines)
        return out


    def feed_count(self, row, col, color_by,
                    end_hour, start_hour=0,
                    ylim=None, palette=None,
                    resample_by='5min', height=10, width=10,
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

        end_hour, start_hour: float, default <required>, 0
            Enter the time window (in hours) you want to plot here.

        ylim: tuple, default None
            Enter the desired ylims here.

        palette: matplotlib palette

        resample_by: string, default '5min'
            The time frequency used to bin the timecourse data. For the format,
            please see
            http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases

        font_scale: float, default 1.5
            The fontsize will be multiplied by this amount.

        height, width: float, default 10, 10
            The height and width of each panel in inches.

        gridlines: boolean, default True
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
                                        volume_unit=None,
                                        start_hour=start_hour,
                                        end_hour=end_hour,
                                        palette=palette,
                                        resample_by=resample_by,
                                        ylim=ylim, height=height, width=width,
                                        gridlines=gridlines)
        return out
