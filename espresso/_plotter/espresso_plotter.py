#!/usr/bin/python
# -*-coding: utf-8 -*-
# Author: Joses Ho
# Email : joseshowh@gmail.com

"""
Plot functions for espresso objects.
"""

# import sys as _sys
# _sys.path.append("..") # so we can import munger from the directory above.


class espresso_plotter():
    """
    Plotting class for espresso object.

    Plots available:
        rasters
        percent_feeding

    To produce contrast plots, use the `contrast` method.
    e.g `my_espresso_experiment.plot.contrast`
    Plots available:
        feed_count_per_fly
        feed_duration_per_fly
        feed_volume_per_fly
        feed_speed_per_fly
        latency_to_feed_per_fly

    """

    # To produce timecourse plots, use the `timecourse` method.
    # e.g `my_espresso_experiment.plot.timecourse`
    # Plots available:
    #     feed_count
    #     feed_volume
    #     feed_speed

    def __init__(self, espresso): # pass along an espresso instance.

        # Add submodules below. The respective .py scripts
        # should be in the same folder as espresso_plotter.py.
        from . import contrast as contrast
        from . import cumulative as cumulative

        # Create attribute so the other methods below can access the espresso object.
        self._experiment = espresso

        # call obj.plot.xxx to access these methods.
        self.contrast = contrast.contrast_plotter(self)
        self.cumulative = cumulative.cumulative_plotter(self)

        # Timecourse plots are temporarily disabled.
        # from . import timecourse as timecourse
        # self.timecourse = timecourse.timecourse_plotter(self)




    def __plot_rasters(self, current_facet_feeds, current_facet_flies,
                       maxflycount, color_by, palette,
                       plot_ax, add_flyid_labels):
        """
        Helper function that actually plots the rasters.
        """
        from . import plot_helpers as plothelp
        import pandas as pd

        # Identify legitimate feeds; sort by time of first feed.
        _feeding_flies = current_facet_feeds.sort_values(['RelativeTime_s','FeedDuration_s'])\
                                            .FlyID.drop_duplicates()\
                                            .tolist()
        # Index the current faceted feeds by FlyID.
        _current_facet_fly_index = current_facet_feeds.reset_index().set_index('FlyID')

        # Next, identify which flies did not feed (aka not in list above.)
        _non_feeding_flies = current_facet_flies[current_facet_flies.AtLeastOneFeed == False].FlyID.tolist()
        _flies_in_order = _feeding_flies + _non_feeding_flies

        for k, fly in enumerate(_flies_in_order):
            rasterplot_kwargs = dict(alpha = 0.75, linewidth = 0,
                                     ymin = (1/maxflycount) * (maxflycount-k-1),
                                     ymax = (1/maxflycount) * (maxflycount-k))


            if color_by is None:
                rasterplot_kwargs['facecolor'] = 'grey'
                rasterplot_kwargs['edgecolor'] = 'grey'


            try:
                _current_facet_fly = _current_facet_fly_index.loc[fly]
                if isinstance(_current_facet_fly, pd.Series):
                    rasterplot_kwargs['xmin'] = _current_facet_fly.RelativeTime_s
                    rasterplot_kwargs['xmax'] = _current_facet_fly.RelativeTime_s + \
                                                _current_facet_fly.FeedDuration_s
                    if color_by is not None:
                        color = palette[_current_facet_fly[color_by]]
                        rasterplot_kwargs['facecolor'] = color
                        rasterplot_kwargs['edgecolor'] = color
                    plot_ax.axvspan(**rasterplot_kwargs)


                elif isinstance(_current_facet_fly, pd.DataFrame):
                    start = _current_facet_fly.RelativeTime_s.tolist()
                    duration = _current_facet_fly.FeedDuration_s.tolist()

                    for j, feed_start in enumerate(start):
                        rasterplot_kwargs['xmin'] = feed_start
                        rasterplot_kwargs['xmax'] = feed_start + duration[j]
                        if color_by is not None:
                            current_color_cat = _current_facet_fly[color_by].iloc[j]
                            color = palette[current_color_cat]
                            rasterplot_kwargs['facecolor'] = color
                            rasterplot_kwargs['edgecolor'] = color
                        plot_ax.axvspan(**rasterplot_kwargs)

            except KeyError:
                pass

            if add_flyid_labels:
                if fly in _non_feeding_flies:
                    label_color = 'grey'
                else:
                    label_color = 'black'
                label = fly.split('_')[-1]
                ypos = (1/maxflycount)*(maxflycount-k-1) + (1/maxflycount)*.5
                plot_ax.text(-85, ypos, label, color=label_color,
                             verticalalignment='center',
                             horizontalalignment='right',
                             fontsize=8)



    def rasters(self, start_hour, end_hour, color_by=None, col=None, row=None,
                height=10, width=10, add_flyid_labels=True, palette=None,
                ax=None, gridlines=True):
        """
        Produces a raster plot of feed events.

        Keywords
        --------
        start_hour, end_hour: float
            The time window (in hours) during which to compute and display the
            percent flies feeding.

        color_by: string, default None
            The categorical column in the espresso object used to color
            individual feeds.

        col, row: string, default None
            Accepts a categorical column in the espresso object. Each group in
            this column will be plotted on along the desired axis.

        add_flyid_labels: boolean, default True
            If True, the FlyIDs for each fly will be displayed on the left of each raster row.

        height, width: float, default 10, 10
            The height and width of each panel in inches.

        fig_size: tuple (width, height), default None
            The size of the final figure, in inches.

        palette: matplotlib palette OR a list of named matplotlib colors.
            Full list of matplotlib palettes
            https://matplotlib.org/examples/color/colormaps_reference.html
            Full list of named matplotlib colors
            https://matplotlib.org/gallery/color/named_colors.html

        ax: matplotlib Axes, default None
            Plot on specified matplotlib Axes.

        gridlines: boolean, default True
            Whether or not vertical gridlines are displayed at each major
            (hourly) tick.

        Returns
        -------
        matplotlib AxesSubplot(s)
        """
        import numpy as np
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches # for custom legends.
        import pandas as pd
        import seaborn as sns

        from . import plot_helpers as plothelp
        from .._munger import munger as munge

        # make a copy of the metadata and the feedlog.
        allfeeds = self._experiment.feeds.copy()
        allflies = self._experiment.flies.copy()

        # Check that col, row and color_by keywords are Attributes of the feeds.
        munge.check_group_by_color_by(col, row, color_by, allfeeds)

        if row is None and col is None:
            err1 = "Either `row` or `col` must be specified. "
            err2 = "If you do not want to facet along the rows or columns, "
            err3 = "supply one of the single-category variables (eg. Sex)."
            raise ValueError(err1 + err2 + err3)

        if row is not None:
            # print("Plotting rows by {0}".format(row))
            row_count = int(len(allfeeds[row].cat.categories))
        else:
            row_count = 1
        if col is not None:
            # print("Plotting columns by {0}".format(col))
            col_count = int(len(allfeeds[col].cat.categories))
        else:
            col_count = 1

        # Change relevant columns to categorical.
        cat_cols = [col, row, color_by]
        for column in [c for c in cat_cols if c is not None]:
            try:
                cats = np.sort(allfeeds[column].unique())
                allfeeds.loc[:, column] = pd.Categorical(allfeeds[column],
                                                       categories=cats,
                                                       ordered=True)
            except KeyError:
                pass

        # Reindex the feeds DataFrame for plotting.
        facets = [a for a in [col, row] if a is not None]
        faceted_feeds = allfeeds.set_index(facets)
        # Reindex the flies DataFrame for plotting.
        facets_metadata = [a for a in facets if a in allflies.columns]
        faceted_flies = allflies.set_index(facets_metadata)

        # Get the number of flies for each group, then identify which is
        # the most numerous group. This is then used to scale the individual
        # facets.
        allflies_grpby = allflies.groupby(facets_metadata)
        maxflycount = allflies_grpby.count().FlyID.max()

        # Get the total flycount.
        try:
            in_allflies = [a for a in facets if a in allflies.columns]
            allflies_grpby = allflies.groupby(in_allflies)
            maxflycount = allflies_grpby.count().FlyID.max()
        except KeyError:
            # group_by is not a column in the metadata,
            # so we assume that the number of flies in the raster plot
            # is simply the total number of flies.
            maxflycount = len(allflies)

        # Initialise the figure.
        sns.set(style='ticks',context='poster')
        x_inches = width * col_count
        y_inches = height * row_count
        if ax is None:
            fig, axx = plt.subplots(nrows=row_count, ncols=col_count,
                                    figsize=(x_inches, y_inches),
                                    gridspec_kw={'wspace':0.25,
                                                 'hspace':0.25})
        else:
            axx = ax

        # Handle the palette.
        if color_by is not None:
            color_groups = allfeeds[color_by].cat.categories
            if palette is None:
                palette = 'tab10'
            color_pal = plothelp.create_palette(palette, color_groups)

            # Add custom legend and title.
            legend_kwargs = {'frameon': False,
                             'borderaxespad': 1,
                             'loc': 'upper left',
                             'edgecolor': 'white'}
            raster_legend_handles = []
            for key in color_pal.keys():
                patch = mpatches.Patch(color=color_pal[key], label=key)
                raster_legend_handles.append(patch)

        else:
            color_pal = None


        if row is not None and col is not None:
            INDEX = faceted_feeds.index
            ROWS = INDEX.get_level_values(row).unique()
            COLUMNS = INDEX.get_level_values(col).unique()
            for r, row_ in enumerate(ROWS):
                for c, col_ in enumerate(COLUMNS):
                    print("Plotting {} {}".format(row_, col_))
                    plot_ax = axx[r, c] # the axes to plot on.
                    # Select the data of interest to plot.
                    try:
                        current_facet_feeds = faceted_feeds.loc[col_].loc[row_]
                        current_facet_flies = faceted_flies.loc[col_].loc[row_]
                    except TypeError:
                        # Sometimes there might be an error if one uses an
                        # integer to index a Categorical index...
                        # so index step-by-step instead.
                        _temp_facet_feeds = faceted_feeds.loc[col_]
                        FEED_INDEX = _temp_facet_feeds.index
                        current_facet_feeds = _temp_facet_feeds[FEED_INDEX == row_]

                        _temp_facet_flies = faceted_flies.loc[col_]
                        FLIES_INDEX = _temp_facet_flies.index
                        current_facet_flies = _temp_facet_flies[FLIES_INDEX == row_]

                    # Get valid feeds.
                    current_facet_feeds = current_facet_feeds[current_facet_feeds.Valid]
                    self.__plot_rasters(current_facet_feeds, current_facet_flies,
                                        maxflycount, color_by, color_pal,
                                        plot_ax, add_flyid_labels)
                    plot_ax.set_title("{}; {}".format(col_, row_))

        else:
            # We only have one dimension here.
            plot_dim = [d for d in [row, col] if d is not None][0]
            # check how many panels in the single row/column.
            panels = faceted_feeds.index.get_level_values(plot_dim).unique().tolist()
            more_than_one_panel = len(panels) > 1

            for j, dim_ in enumerate(panels):
                # Get the axes to plot on.
                if more_than_one_panel:
                    plot_ax = axx[j]
                else:
                    plot_ax = axx
                print("Plotting {}".format(dim_))
                current_facet_feeds = faceted_feeds[(faceted_feeds.index == dim_) &
                                                    (faceted_feeds.Valid)]
                current_facet_flies = faceted_flies[faceted_flies.index == dim_]
                self.__plot_rasters(current_facet_feeds, current_facet_flies,
                                    maxflycount, color_by, color_pal,
                                    plot_ax, add_flyid_labels)
                plot_ax.set_title(dim_)


        # Plot gridlines.
        # Position the raster color legend, and despine accordingly.
        # Note the we remove the left spine (set to True).
        grid_kwargs = dict(alpha=0.75, which='major', linewidth=1)
        despine_kwargs = dict(left=True, trim=False, offset=5)
        if more_than_one_panel:
            for a in axx.flatten():
                # Plot vertical grid lines if desired.
                if gridlines:
                    a.xaxis.grid(**grid_kwargs)
                plothelp.format_timecourse_xaxis(a, min_x_seconds=start_hour*3600,
                                                 max_x_seconds=end_hour*3600)
                a.yaxis.set_visible(False)
                sns.despine(ax=a, **despine_kwargs)
            rasterlegend_ax = axx.flatten()[-1]

        else:
            if gridlines:
                axx.xaxis.grid(**grid_kwargs)
            plothelp.format_timecourse_xaxis(axx, min_x_seconds=start_hour*3600,
                                             max_x_seconds=end_hour*3600)
            axx.yaxis.set_visible(False)
            sns.despine(ax=axx, **despine_kwargs)
            rasterlegend_ax = axx

        if color_by is not None:
            rasterlegend_ax.legend(bbox_to_anchor=(0,-0.15), ncol=1,
                                   handles=raster_legend_handles, **legend_kwargs)

        # End and return the figure.
        if ax is None:
            return axx



    def percent_feeding(self, group_by, compare_by,
                        start_hour, end_hour,
                        height=10, width=10,
                        tight_layout=False, gridlines=True,
                        plot_along="column", palette=None):
        """
        Produces a lineplot depicting the percent of flies feeding for each condition.
        A 95% confidence interval for each proportion of flies feeding is also given.

        Keywords
        --------
        group_by: string
            The column or label indicating the variable used to group the
            subplots.

        compare_by: string
            The percent feeding will be compared between the categories in this
            column or label.

        start_hour, end_hour: float
            The time window (in hours) during which to compute and display the
            percent flies feeding.

        height, width: float, default 10, 10
            The height and width of each panel in inches.

        plot_along: "row" or "column", default "column"
            Tiles the subplots for each "group_by" group along the row or column.

        tight_layout: boolean, default False
            Might improve layout if set to True.

        gridlines: boolean, default True
            If plotting along column, draws gridlines at the major ticks on y-axes.

        palette: matplotlib palette OR a list of named matplotlib colors.
            Full list of matplotlib palettes
            https://matplotlib.org/examples/color/colormaps_reference.html
            Full list of named matplotlib colors
            https://matplotlib.org/gallery/color/named_colors.html

        Returns
        -------
        A matplotlib Axes instance, and a pandas DataFrame with the statistics.
        """

        import numpy as np

        import matplotlib as mpl
        import matplotlib.pyplot as plt
        # for custom legend?
        from matplotlib.patches import Patch
        from matplotlib.lines import Line2D

        from .plot_helpers import compute_percent_feeding, create_palette
        import seaborn as sns

        # make a copy of the metadata and the feedlog.
        all_feeds = self._experiment.feeds.copy()
        all_flies = self._experiment.flies.copy()
        facets = [group_by, compare_by]

        for z in facets:
            if z not in all_feeds.columns:
                raise KeyError('{} is not a column in FeedLog. Please check'.format(z))
            if z not in all_flies.columns:
                raise KeyError('{} is not a column in CountLog. Please check'.format(z))

        if plot_along not in ["row", "column"]:
            err1 = "You specified plot_along={}".format(plot_along)
            err2 = " It should only be 'row' or 'column'."
            raise ValueError(err1 + err2)

        percent_feeding_summary = compute_percent_feeding(all_feeds, all_flies,
                                                          facets,
                                                          start_hour=start_hour,
                                                          end_hour=end_hour)

        subplots = percent_feeding_summary.index.levels[0].categories
        subplot_title_preface = percent_feeding_summary.index.levels[0].name

        # Set style.
        sns.set(style='ticks', context="poster")

        palette = create_palette(palette, subplots)

        # Initialise figure.
        if plot_along == 'column':
            f, ax = plt.subplots(ncols=len(subplots),
                                 figsize=(width * len(subplots), height),
                                 gridspec_kw={'wspace': 0},
                                 )
        elif plot_along == 'row':
            f, ax = plt.subplots(nrows=len(subplots),
                                 figsize=(width, height * len(subplots)))
                                 # gridspec_kw={'hspace':0.25},
                                 # sharex=True)

        if isinstance(ax, np.ndarray):
            axx = ax
        elif isinstance(ax, mpl.axes.Axes):
            axx = [ax]

        legend_elements = []

        compareby_groups = percent_feeding_summary.index.levels[1].categories
        if np.max([len(str(a)) for a in compareby_groups]) > 8:
            rotate_ticks = True
        else:
            rotate_ticks = False


        for j, group_by in enumerate(subplots):
            plot_ax = axx[j]
            plot_color = palette[group_by]
            legend_elements.append(Line2D([0], [0], color=plot_color,
                                          lw=4, label=group_by)
                                  ),


            plot_df = percent_feeding_summary.loc[group_by]
            cilow = plot_df.ci_lower.tolist()
            cihigh = plot_df.ci_upper.tolist()
            ydata = plot_df.percent_feeding.tolist()

            plot_ax.set_ylim(0, 100)
            # Plot 95CI first.
            if len(plot_df) > 1:
                plot_ax.fill_between(range(0,len(plot_df)), cilow, cihigh,
                                     alpha=0.25, color=plot_color)
            else:
                plot_ax.axvline(x=0, ymin=cilow[0]/100, ymax=cihigh[0]/100,
                                alpha=0.5, color=plot_color)
            # Then plot the line.
            plot_df.percent_feeding.plot.line(ax=plot_ax, lw=1.2,
                                              color=plot_color,
                                              alpha=0.25)

            for k, s in enumerate(ydata):
                plot_ax.plot(k, s, 'o', clip_on=False, color=plot_color)

            # Aesthetic tweaks.
            plot_ax.xaxis.set_ticks([i for i in range(0,len(plot_df))])
            plot_ax.xaxis.set_ticklabels(plot_df.index.tolist())

            xmax = plot_ax.xaxis.get_ticklocs()[-1]
            plot_ax.set_xlim(-0.2, xmax + 0.2) # Add x-padding.

            plot_ax.set_xlabel('')

            line_kwargs = {'color': 'k', 'linewidth': 1,
                          'linestyle':'dotted', 'alpha':0.75}
            if plot_along == 'column':
                if j == 0:
                    plot_ax.set_ylabel('Percent Feeding (%)')
                else:
                    plot_ax.set_ylabel('')
                    plot_ax.get_yaxis().set_visible(False)

                if gridlines is True:
                    if j == 0:
                        plot_ax.yaxis.grid(True, which='major', **line_kwargs)
                    else:
                        for tt in plot_ax.get_yticks():
                            plot_ax.axhline(y=tt, **line_kwargs)

                sns.despine(ax=plot_ax, trim=True, left=(j > 0),
                            offset={'left':1})

            elif plot_along == 'row':
                plot_ax.set_ylabel('Percent Feeding (%)')
                if gridlines is True:
                    plot_ax.yaxis.grid(True, which='major', **line_kwargs)
                sns.despine(ax=plot_ax, trim=True, offset={'left':1})

        if plot_along == 'row':
            for a in axx[:-1]:
                a.set_xticklabels('')

        if rotate_ticks is True:
            if plot_along == 'column':
                axes_to_rotate_xticks = axx
            elif plot_along == 'row':
                axes_to_rotate_xticks = [axx[-1]]

            for ax in axes_to_rotate_xticks:
                for tick in ax.get_xticklabels():
                    tick.set_rotation(45)
                    tick.set_horizontalalignment('right')

        title = 'Percent flies feeding\nt = {}hr to t = {}hr'.format(start_hour,
                                                                     end_hour)
        f.suptitle(title, y=1.04)

        # Add custom legend and title.
        legend_kwargs = {'frameon': False,
                         'borderaxespad': 1,
                         'loc': 'center',
                         'edgecolor': 'white'}

        if rotate_ticks is True:
            yanchor = -0.87
        else:
            yanchor = -0.3

        if plot_along == 'column':
            nc = len(subplots)
            if (nc % 2) != 0:
                # If we have an odd number of columns,
                # find the middle axes, and xposition the legend in its middle.
                if rotate_ticks:
                    xanchor = 0.6
                else:
                    xanchor = 0.5
                legend_ax = int((nc + 1) / 2 - 1)
            else:
                xanchor = 1
                # # If we have an even number of columns,
                # # find the left of middle axes,
                # # and xposition the legend at its lower right corner.
                # if rotate_ticks:
                #     xanchor = 1.1
                # else:
                #     xanchor = 1
                legend_ax = int(nc / 2 - 1)

            axx[legend_ax].legend(handles=legend_elements, ncol=nc,
                                  bbox_to_anchor=(xanchor, yanchor),
                                  **legend_kwargs)

        elif plot_along == 'row':
            if rotate_ticks:
                xanchor = 0.6
            else:
                xanchor = 0.5
            axx[-1].legend(handles=legend_elements, ncol=1,
                          bbox_to_anchor=(xanchor, yanchor), **legend_kwargs)

        if tight_layout:
            plt.tight_layout()

        # Reset aesthetics.
        sns.set()

        return f, percent_feeding_summary
