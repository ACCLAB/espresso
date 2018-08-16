#!/usr/bin/python
# -*-coding: utf-8 -*-
# Author: Joses Ho
# Email : joseshowh@gmail.com

"""
timecourse plot functions for espresso objects.
"""



class timecourse_plotter():
    """
    contrast plotting class for espresso object.

    Available methods
    -----------------
    feed_count
    feed_volume
    feed_speed
    """


    def __init__(self, plotter): # pass along an espresso_plotter instance.
        self.__feeds = plotter._experiment.feeds.copy()
        self.__expt_end_time = plotter._experiment.expt_duration_minutes



    def __timecourse_plotter(self, yvar, col, row, color_by, start_hour,
                             end_hour, volume_unit=None,
                             resample_by='5min', fig_size=None, palette=None,
                             height=10, width=10,
                             gridlines=True, ax=None):

        import numpy as np
        import pandas as pd
        import matplotlib.pyplot as plt
        import seaborn as sns
        from . import plot_helpers as plothelp
        from .._munger import munger as munge

        feeds = self.__feeds.copy()

        # Handle the group_by and color_by keywords.
        munge.check_group_by_color_by(col, row, color_by, feeds)


        ## DICTIONARY FOR MATCHING YVAR TO APPROPRIATE YLABEL.
        yvar_ylabel_dict = {
            'AverageFeedVolumePerFly_µl':'Average Feed Volume Per Fly (µl)',
            'AverageFeedCountPerFly':'Average Feed Count Per Fly',
            'AverageFeedSpeedPerFly_µl/s':'Average Feed Speed Per Fly (µl/s)'
            }

        ylab = yvar_ylabel_dict[yvar]

        resamp_feeds = munge.groupby_resamp_sum(feeds, resample_by)
        resamp_feeds_sum = munge.sum_for_timecourse(resamp_feeds)
        plotdf = munge.pivot_for_timecourse(resamp_feeds_sum, row, col, color_by)

        if volume_unit is not None:
            if volume_unit.strip().split('lit')[0] == 'micro':
                y = yvar

            else:
                multiplier = plothelp.get_unit_multiplier(volume_unit,
                                                          convert_from='micro')
                new_unit = plothelp.get_new_prefix(volume_unit)

                y = yvar.replace('µ', new_unit)
                ylab = ylab.replace('µ', new_unit)
                plotdf[y] = plotdf[yvar] * multiplier

        else:
            y = yvar


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

        if palette is None:
            palette = 'tab10'

        if color_by is None:
            color_groups = ['__placeholder__']
        else:
            color_groups = plotdf.index.levels[-2].tolist()
        col_map = plothelp.create_palette(palette, color_groups,
                                         produce_colormap=True)


        # Initialise figure.
        sns.set(style='ticks',context='poster')
        x_inches = width * col_count
        y_inches = height * row_count


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
                    current_plot_df = plotdf.loc[(row_, col_), y]

                    # We unstack and transpose to create a 'long' dataset,
                    # where each column is a timecourse dataset to be plotted.
                    current_plot_df = current_plot_df.unstack().T

                    # Create the plot.
                    current_plot_df.plot.area(ax=plot_ax, colormap=col_map,
                                              stacked=True)
                    plot_ax.set_title("{}; {}".format(row_, col_))

        else:
            # We only have one dimension here.
            plot_dim = [d for d in [row, col] if d is not None][0]
            for j, dim_ in enumerate(feeds[plot_dim].cat.categories):

                plot_ax = axx[j]

                current_plot_df = plotdf.loc[dim_, y]
                current_plot_df = current_plot_df.unstack().T

                current_plot_df.plot.area(ax=plot_ax, colormap=col_map,
                                          stacked=True)
                plot_ax.set_title(dim_)

        # Normalize all the y-axis limits.
        if row_count + col_count > 1:
            plothelp.normalize_ylims(axx.flatten(),
                                     include_zero=True)
            for plot_ax in axx.flatten():
                # Format x-axis.
                plothelp.format_timecourse_xaxis(plot_ax,
                                                   start_hour * 3600,
                                                   end_hour * 3600)
                # Set label for y-axis.
                plot_ax.set_ylabel(ylab)
                # Plot vertical grid lines if desired.
                if gridlines:
                    plot_ax.xaxis.grid(True, which='major',
                                       linestyle='dotted', #linewidth=1,
                                       alpha=0.5)

        for ax in axx.flatten()[:-1]:
            ax.legend().set_visible(False)

        if color_by is not None:
            legend_title = color_by
        else:
            legend_title = ''
        axx.flatten()[-1].legend(loc='upper left',
                                 frameon=False,
                                 title=legend_title,
                                 bbox_to_anchor=(-0.05, -0.15))

        # Despine and offset each axis.
        for ax in axx.flatten():
            sns.despine(ax=ax, trim=True, offset=5)

        # End and return the figure.
        if ax is None:
            return axx



    def feed_count(self, col, row, color_by, start_hour, end_hour,
                   palette=None, gridlines=True, resample_by='5min',
                   height=10, width=10, ax=None):
        """
        Produces a timecourse area plot depicting the average feed count per fly
        for the entire assay. The plot will be tiled horizontally
        according to the `col`, horizontally according to the category `row`,
        and will be colored according to the category `color_by`.
        Feed counts will be binned by the duration in `resample_by`.

        Keywords
        --------
        col, row: string
            Accepts a categorical column in the espresso object. Each group in
            this column will be plotted on along the desired axis.

        color_by: string
            Accepts a categorical column in the espresso object. Each group in
            this column will be colored seperately, and stacked as an area plot.

        start_hour, end_hour: float, defaults 0 and None
            The time window of the experiment to plot. If end_hour is None,
            all feeds until the end of the experiment will be included.

        palette: matplotlib palette OR a list of named matplotlib colors.
            Full list of matplotlib palettes
            https://matplotlib.org/examples/color/colormaps_reference.html
            Full list of named matplotlib colors
            https://matplotlib.org/gallery/color/named_colors.html

        gridlines: boolean, default True
            Whether or not vertical gridlines are displayed at each hour..

        resample_by: string, default '5min'
            The time frequency used to bin the timecourse data. For the format,
            please see
            http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases

        height, width: float, default 10, 10
                The height and width of each panel in inches.

        ax: array of matplotlib Axes objects, default None
            Given an array of Axes, each category (as dictacted by group_by)
            will be plotted respectively.

        Returns
        -------
        matplotlib AxesSubplot(s)
        """
        out = self.__timecourse_plotter('AverageFeedCountPerFly',
                                        row=row, col=col,
                                        volume_unit=None,
                                        start_hour=start_hour, end_hour=end_hour,
                                        color_by=color_by,
                                        resample_by=resample_by,
                                        height=height, width=width,
                                        gridlines=gridlines,
                                        palette=palette,
                                        ax=ax)
        return out



    def feed_volume(self, col, row, color_by, start_hour, end_hour,
                    volume_unit='nanoliter', palette=None, gridlines=True,
                    resample_by='5min', height=10, width=10, ax=None):
        """
        Produces a timecourse area plot depicting the average feed volume per
        fly for the entire assay. The plot will be tiled horizontally
        according to the `col`, horizontally according to the category `row`,
        and will be colored according to the category `color_by`.
        Feed volumes will be binned by the duration in `resample_by`.

        Keywords
        --------
        col, row: string
            Accepts a categorical column in the espresso object. Each group in
            this column will be plotted on along the desired axis.

        color_by: string
            Accepts a categorical column in the espresso object. Each group in
            this column will be colored seperately, and stacked as an area plot.

        start_hour, end_hour: float, defaults 0 and None
            The time window of the experiment to plot. If end_hour is None,
            all feeds until the end of the experiment will be included.

        volume_unit: string, default 'nanoliter'
            Accepts 'centiliter' (10^-2 liters), 'milliliter (10^-3 liters)',
            'microliter'(10^-6 liters), 'nanoliter' (10^-9 liters), and
            'picoliter' (10^-12 liters).

        palette: matplotlib palette OR a list of named matplotlib colors.
            Full list of matplotlib palettes
            https://matplotlib.org/examples/color/colormaps_reference.html
            Full list of named matplotlib colors
            https://matplotlib.org/gallery/color/named_colors.html

        gridlines: boolean, default True
            Whether or not vertical gridlines are displayed at each hour..

        resample_by: string, default '5min'
            The time frequency used to bin the timecourse data. For the format,
            please see
            http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases

        height, width: float, default 10, 10
                The height and width of each panel in inches.

        ax: array of matplotlib Axes objects, default None
            Given an array of Axes, each category (as dictacted by group_by)
            will be plotted respectively.

        Returns
        -------
        matplotlib AxesSubplot(s)
        """
        out = self.__timecourse_plotter('AverageFeedVolumePerFly_µl',
                                        row=row, col=col,
                                        volume_unit=volume_unit,
                                        start_hour=start_hour, end_hour=end_hour,
                                        color_by=color_by,
                                        resample_by=resample_by,
                                        height=height, width=width,
                                        gridlines=gridlines,
                                        palette=palette,
                                        ax=ax)

        return out



    def feed_speed(self, col, row, color_by, start_hour, end_hour,
                   volume_unit='nanoliter', palette=None, gridlines=True,
                   resample_by='5min', height=10, width=10, ax=None):
        """
        Produces a timecourse area plot depicting the average feed speed per fly
        in µl/s for the entire assay. The plot will be tiled horizontally
        according to the `col`, horizontally according to the category `row`,
        and will be colored according to the category `color_by`.
        Feed speeds will be binned by the duration in `resample_by`.

        Keywords
        --------
        col, row: string
            Accepts a categorical column in the espresso object. Each group in
            this column will be plotted on along the desired axis.

        color_by: string
            Accepts a categorical column in the espresso object. Each group in
            this column will be colored seperately, and stacked as an area plot.

        start_hour, end_hour: float, defaults 0 and None
            The time window of the experiment to plot. If end_hour is None,
            all feeds until the end of the experiment will be included.

        volume_unit: string, default 'nanoliter'
            Accepts 'centiliter' (10^-2 liters), 'milliliter (10^-3 liters)',
            'microliter'(10^-6 liters), 'nanoliter' (10^-9 liters), and
            'picoliter' (10^-12 liters).

        palette: matplotlib palette OR a list of named matplotlib colors.
            Full list of matplotlib palettes
            https://matplotlib.org/examples/color/colormaps_reference.html
            Full list of named matplotlib colors
            https://matplotlib.org/gallery/color/named_colors.html

        gridlines: boolean, default True
            Whether or not vertical gridlines are displayed at each hour..

        resample_by: string, default '5min'
            The time frequency used to bin the timecourse data. For the format,
            please see
            http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases

        height, width: float, default 10, 10
                The height and width of each panel in inches.

        ax: array of matplotlib Axes objects, default None
            Given an array of Axes, each category (as dictacted by group_by)
            will be plotted respectively.

        Returns
        -------
        matplotlib AxesSubplot(s)
        """
        out = self.__timecourse_plotter('AverageFeedSpeedPerFly_µl/s',
                                        row=row, col=col,
                                        volume_unit=volume_unit,
                                        start_hour=start_hour, end_hour=end_hour,
                                        color_by=color_by,
                                        resample_by=resample_by,
                                        height=height, width=width,
                                        gridlines=gridlines,
                                        palette=palette,
                                        ax=ax)
        return out
