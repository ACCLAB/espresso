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

    To produce timecourse plots, use the `timecourse` method.
    e.g `my_espresso_experiment.plot.timecourse`

        Plots available:
            TBA
    """

    def __init__(self,espresso): # pass along an espresso instance.

        # Add submodules below. The respective .py scripts
        # should be in the same folder as espresso_plotter.py.
        from . import contrast as contrast
        from . import cumulative as cumulative
        from . import timecourse as timecourse

        # Create attribute so the other methods below can access the espresso object.
        self._experiment = espresso
        self.__expt_end_time = espresso.expt_duration_seconds
        # call obj.plot.xxx to access these methods.
        self.contrast = contrast.contrast_plotter(self)
        self.timecourse = timecourse.timecourse_plotter(self)
        self.cumulative = cumulative.cumulative_plotter(self)

    def __plot_rasters(self, current_facet_feeds, current_facet_flies,
                       maxflycount, color_by, palette,
                       plot_ax, add_flyid_labels):
        """
        Helper function that actually plots the rasters.
        """
        from . import plot_helpers as plt_help
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
            rasterplot_kwargs = dict(
                    ymin = (1/maxflycount) * (maxflycount-k-1),
                    ymax = (1/maxflycount) * (maxflycount-k),
                    alpha = 0.8)
            try:
                _current_facet_fly = _current_facet_fly_index.loc[fly]
                if isinstance(_current_facet_fly, pd.Series):
                    rasterplot_kwargs['xmin'] = _current_facet_fly.RelativeTime_s
                    rasterplot_kwargs['xmax'] = _current_facet_fly.RelativeTime_s + \
                                                _current_facet_fly.FeedDuration_s
                    if color_by is not None:
                        rasterplot_kwargs['color'] = palette[_current_facet_fly[color_by]]
                    plot_ax.axvspan(**rasterplot_kwargs)

                elif isinstance(_current_facet_fly, pd.DataFrame):
                    start = _current_facet_fly.RelativeTime_s.tolist()
                    duration = _current_facet_fly.FeedDuration_s.tolist()

                    for j, feed_start in enumerate(start):
                        rasterplot_kwargs['xmin'] = feed_start
                        rasterplot_kwargs['xmax'] = feed_start + duration[j]
                        if color_by is not None:
                            current_color_cat = _current_facet_fly[color_by].iloc[j]
                            rasterplot_kwargs['color'] = palette[current_color_cat]
                        plot_ax.axvspan(**rasterplot_kwargs)

            except KeyError:
                pass

            if add_flyid_labels:
                if fly in _non_feeding_flies:
                    label_color = 'grey'
                else:
                    label_color = 'black'
                label = fly.split('_')[-1]
                plot_ax.text(-85,
                              (1/maxflycount)*(maxflycount-k-1) + (1/maxflycount)*.5,
                               label,
                               color=label_color,
                               verticalalignment='center',
                               horizontalalignment='right',
                               fontsize=8)


    def rasters(self,
                col=None,
                row=None,
                color_by=None,
                add_flyid_labels=True,
                fig_size=None,
                ax=None,
                gridlines=True):
        """
        Produces a raster plot of feed events.

        Keywords
        --------

        col, row: string, default None
            Accepts a categorical column in the espresso object. Each group in
            this column will be plotted on along the desired axis.

        color_by: string, default None
            The categorical column in the espresso object used to color
            individual feeds.

        add_flyid_labels: boolean, default True
            If True, the FlyIDs for each fly will be displayed on the left of
            each raster row.

        fig_size: tuple (width, height), default None
            The size of the final figure, in inches.

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

        from . import plot_helpers as plt_help
        from .._munger import munger as munge

        # make a copy of the metadata and the feedlog.
        allfeeds = self._experiment.feeds.copy()
        allflies = self._experiment.flies.copy()

        # Check that col, row and color_by keywords are Attributes of the feeds.
        munge.check_group_by_color_by(col, row, color_by, allfeeds)

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
        sns.set(style='ticks',context='poster',font_scale=1.25)
        if fig_size is None:
            x_inches = 9 * col_count
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
                                    gridspec_kw={'wspace':0.2,
                                                 'hspace':0.4})
        else:
            axx = ax

        # Create the palette if so desired.
        if color_by is not None:
            colors = plt_help._make_categorial_palette(allfeeds, color_by)
            palette = dict(zip(allfeeds[color_by].cat.categories, colors))
            # Create custom handles for the foodchoice.
            # See http://matplotlib.org/users/legend_guide.html#using-proxy-artist
            raster_legend_handles = []
            for key in palette.keys():
                patch = mpatches.Patch(color=palette[key], label=key)
                raster_legend_handles.append(patch)
        else:
            palette = None

        if row is not None and col is not None:
            for r, row_ in enumerate(faceted_feeds.index.get_level_values(row).unique()):
                for c, col_ in enumerate(faceted_feeds.index.get_level_values(col).unique()):
                    print("Plotting {} {}".format(row_, col_))
                    plot_ax = axx[r, c] # the axes to plot on.
                    # Select the data of interest to plot.
                    try:
                        current_facet_feeds = faceted_feeds.loc[col_].loc[row_]
                        current_facet_flies = faceted_flies.loc[col_].loc[row_]
                    except TypeError:
                        # Sometimes there might be an error if one uses an integer to index
                        # a Categorical index... so index step-by-step instead.
                        _temp_facet_feeds = faceted_feeds.loc[col_]
                        current_facet_feeds = _temp_facet_feeds[_temp_facet_feeds.index == row_]
                        _temp_facet_flies = faceted_flies.loc[col_]
                        current_facet_flies = _temp_facet_flies[_temp_facet_flies.index == row_]
                    # Get valid feeds.
                    current_facet_feeds = current_facet_feeds[current_facet_feeds.Valid]
                    self.__plot_rasters(current_facet_feeds, current_facet_flies,
                                        maxflycount, color_by, palette,
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
                plot_ax = axx[j] # the axes to plot on.
                current_facet_feeds = faceted_feeds[(faceted_feeds.index == dim_) &
                                                    (faceted_feeds.Valid)]
                current_facet_flies = faceted_flies[faceted_flies.index == dim_]
                self.__plot_rasters(current_facet_feeds, current_facet_flies,
                                    maxflycount, color_by, palette,
                                    plot_ax, add_flyid_labels)
                plot_ax.set_title(dim_)


        # Plot gridlines.
        # Position the raster color legend, and despine accordingly.
        # Note the we remove the left spine (set to True).
        grid_kwargs = dict(linestyle=':', alpha=0.5)
        despine_kwargs = dict(left=True,trim=True,offset=5)
        if len(axx) > 1:
            for a in axx.flatten():
                # Plot vertical grid lines if desired.
                if gridlines:
                    a.xaxis.grid(which='major',
                                        linewidth=0.25, **grid_kwargs)
                plt_help.format_timecourse_xaxis(a, self.__expt_end_time ) ## CHANGE ##
                a.yaxis.set_visible(False)
                sns.despine(ax=a, **despine_kwargs)
            rasterlegend_ax = axx.flatten()[-1]

        else:
            if gridlines:
                axx.xaxis.grid(which='major',
                            linewidth=0.25, **grid_kwargs)
            plt_help.format_timecourse_xaxis(axx, self.__expt_end_time ) ## CHANGE ##
            axx.yaxis.set_visible(False)
            sns.despine(ax=axx, **despine_kwargs)
            rasterlegend_ax = axx

        if color_by is not None:
            rasterlegend_ax.legend(loc='upper left',
                                   bbox_to_anchor=(0,-0.15),
                                   handles=raster_legend_handles)

        # End and return the figure.
        if ax is None:
            return axx


    def percent_feeding(self, group_by, compare_by,
                        start_minute=0,
                        end_minute=360):
        """
        Produces a lineplot depicting the percent of flies feeding for each condition.
        A 95% confidence interval for each proportion of flies feeding is also given.

        Keywords
        --------
        group_by: string,
            The column or label indicating the variable used to group the
            subplots.

        compare_by: string,
            The percent feeding will be compared between the categories in this
            column or label.

        start_minute, end_minute: integer, default 0 and 360
            The time window (in minutes) during which to compute and display the
            percent flies feeding.

        Returns
        -------
        A matplotlib Axes instance, and a pandas DataFrame with the statistics.
        """
        import numpy as np
        import matplotlib as mpl
        import matplotlib.pyplot as plt
        from .plot_helpers import compute_percent_feeding
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

        percent_feeding_summary = compute_percent_feeding(all_feeds, all_flies,
                                                          facets,
                                                          start=start_minute,
                                                          end=end_minute)

        # Set style.
        sns.set(style='ticks',context='talk',font_scale=1.1)
        subplots = percent_feeding_summary.index.levels[0].categories
        subplot_title_preface = percent_feeding_summary.index.levels[0].name

        # Initialise figure.
        f, ax = plt.subplots(ncols=len(subplots),
                             figsize=(8,5),
                             sharey=True)

        if isinstance(ax, np.ndarray):
            axx = ax
        elif isinstance(ax, mpl.axes.Axes):
            axx = [ax]

        for j, group_by in enumerate(subplots):
            plot_ax = axx[j]

            plot_df = percent_feeding_summary.loc[group_by]
            cilow = plot_df.ci_lower.tolist()
            cihigh = plot_df.ci_upper.tolist()
            ydata = plot_df.percent_feeding.tolist()

            plot_ax.set_ylim(0,100)
            # Plot 95CI first.
            if len(plot_df) > 1:
                plot_ax.fill_between(range(0,len(plot_df)),
                                     cilow,cihigh,
                                     alpha=0.25,
                                     color='grey')
            else:
                plot_ax.axvline(x=0,
                                ymin=cilow[0]/100,
                                ymax=cihigh[0]/100,
                                color='grey')
            # Then plot the line.
            plot_df.percent_feeding.plot.line(ax=plot_ax, color='k', lw=1.2)

            for j, s in enumerate(ydata):
                plot_ax.plot(j, s, 'o', clip_on=False, color='k')

            # Aesthetic tweaks.
            plot_ax.xaxis.set_ticks([i for i in range(0,len(plot_df))])
            plot_ax.xaxis.set_ticklabels(plot_df.index.tolist())

            xmax = plot_ax.xaxis.get_ticklocs()[-1]
            plot_ax.set_xlim(-0.2, xmax+0.2) # Add x-padding.

            sns.despine(ax=plot_ax, trim=True, offset={'left':1})

            for tick in plot_ax.get_xticklabels():
                tick.set_rotation(45)
                tick.set_horizontalalignment('right')

            plot_ax.set_title('{0}: {1}'.format(subplot_title_preface, group_by))
            plot_ax.set_ylabel('Percent Feeding (%)')
        f.suptitle('Percent flies feeding from {} min to {} min'.format(start_minute,
                                                                 end_minute))
        return f, percent_feeding_summary
