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

    def __plot_rasters(current_facet_feeds, current_facet_flies,color_by,
                       plot_ax, add_flyid_labels):
    """
    Helper function that actually plots the rasters.
    """
    from . import plot_helpers as plt_help

    # Identify legitimate feeds; sort by time of first feed.
    _feeding_flies = current_facet_feeds.sort_values(['RelativeTime_s','FeedDuration_s'])\
                                        .FlyID.drop_duplicates()\
                                        .tolist()
    # Index the current faceted feeds by FlyID.
    _current_facet_fly_index = current_facet_feeds.reset_index().set_index('FlyID')

    # Next, identify which flies did not feed (aka not in list above.)
    _non_feeding_flies = current_facet_flies[current_facet_flies.AtLeastOneFeed == False].FlyID.tolist()
    _flies_in_order = _feeding_flies + _non_feeding_flies

    # Create the palette.
    if color_by is not None:
        colors = plt_help._make_categorial_palette(allfeeds, color_by)
        palette = dict(zip(allfeeds[color_by].cat.categories, colors))

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
                rasterplot_kwargs['label'] = "_" * k + _current_facet_fly[color_by]
                if color_by is not None:
                    rasterplot_kwargs['color'] = palette[_current_facet_fly[color_by]]
                plot_ax.axvspan(**rasterplot_kwargs)

            elif isinstance(_current_facet_fly, pd.DataFrame):
                start = _current_facet_fly.RelativeTime_s.tolist()
                duration = _current_facet_fly.FeedDuration_s.tolist()

                for j, feed_start in enumerate(start):
                    current_color_cat = _current_facet_fly[color_by].iloc[j]
                    rasterplot_kwargs['xmin'] = feed_start
                    rasterplot_kwargs['xmax'] = feed_start + duration[j]
                    rasterplot_kwargs['label'] = "_" * k + current_color_cat
                    if color_by is not None:
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
                add_flyid_labels=False,
                fig_size=None,
                ax=None,
                gridlines_major=True,
                gridlines_minor=True):
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

        gridlines_major, gridlines_minor: boolean, default True
            Whether or not major and minor vertical gridlines are displayed.

        Returns
        -------
        matplotlib AxesSubplot(s)
        """
        import numpy as np
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches # for custom legends.
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
            row_count = int(len(plotdf[row].cat.categories))
        else:
            row_count = 1
        if col is not None:
            # print("Plotting columns by {0}".format(col))
            col_count = int(len(plotdf[col].cat.categories))
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

        # Create custom handles for the foodchoice.
        # See http://matplotlib.org/users/legend_guide.html#using-proxy-artist
        raster_legend_handles = []
        for key in palette.keys():
            patch = mpatches.Patch(color=palette[key], label=key)
            raster_legend_handles.append(patch)

        # Initialise the figure.
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
                                    gridspec_kw={'wspace':0.2,
                                                 'hspace':0.4})
        else:
            axx = ax

        if row is not None and col is not None:
            for r, row_ in enumerate(faceted_feeds.index.get_level_values(row).unique()):
                for c, col_ in enumerate(faceted_feeds.index.get_level_values(col).unique()):
                    print("Plotting {} {}".format(row_, col_))
                    plot_ax = axx[r, c] # the axes to plot on.
                    # Select the data of interest to plot.
                    try:
                        current_facet_feeds = faceted_feeds.loc[col_].loc[row_].dropna()
                        current_facet_flies = faceted_flies.loc[col_].loc[row_]
                    except TypeError:
                        # Sometimes there might be an error if one uses an integer to index
                        # a Categorical index... so index step-by-step instead.
                        _temp_facet = faceted_feeds.loc[col_]
                        current_facet = _temp_facet[_temp_facet.index == row_]
                    __plot_rasters(current_facet_feeds, current_facet_flies,
                                   palette, plot_ax, add_flyid_labels)
                    plot_ax.set_title("{}; {}".format(col_, row_))

        else:
            # We only have one dimension here.
            plot_dim = [d for d in [row, col] if d is not None][0]
            for j, dim_ in enumerate(plot_feeds.index.get_level_values(plot_dim).unique()):
                print("Plotting {}".format(dim_))
                plot_ax = axx[j] # the axes to plot on.
                current_facet_feeds = faceted_feeds[faceted_feeds.index == dim_].dropna()
                __plot_rasters(current_facet_feeds, current_facet_flies,
                              palette, plot_ax, add_flyid_labels)
                plot_ax.set_title(dim_)




        # Plot gridlines.
        # Position the raster color legend, and despine accordingly.
        # Note the we remove the left spine (set to True).
        grid_kwargs = dict(linestyle=':', alpha=0.5)
        despine_kwargs = dict(left=True,trim=True,offset=5)
        if len(axx) > 1:
            for a in axx.flatten():
                # Plot vertical grid lines if desired.
                if gridlines_major:
                    a.xaxis.grid(which='major',
                                        linewidth=0.25, **grid_kwargs)
                plt_help.format_timecourse_xaxis(a, 21600) ## CHANGE ##
                a.yaxis.set_visible(False)
                sns.despine(ax=a, **despine_kwargs)
            rasterlegend_ax = axx.flatten()[-1]

        else:
            if gridlines_major:
                axx.xaxis.grid(which='major',
                            linewidth=0.25, **grid_kwargs)
            plt_help.format_timecourse_xaxis(axx, 21600) ## CHANGE ##
            axx.yaxis.set_visible(False)
            sns.despine(ax=axx, **despine_kwargs)
            rasterlegend_ax = axx

        rasterlegend_ax.legend(loc='upper left',
                               bbox_to_anchor=(0,-0.15),
                               handles=raster_legend_handles)



        # # print("Coloring rasters by {0}".format(color_by))
        # # print("Grouping rasters by {0}".format(group_by))
        #
        # # Get the total flycount.
        # try:
        #     group_by_cols = [a for a in [col, row] if a is not None]
        #     check_grpby_col = allflies.groupby(group_by_cols)
        #     maxflycount = check_grpby_col.count().FlyID.max()
        # except KeyError:
        #     # group_by is not a column in the metadata,
        #     # so we assume that the number of flies in the raster plot
        #     # is simply the total number of flies.
        #     maxflycount = len(allflies)
        #
        # # Get the groups we will be grouping on, and coloring on.
        # plot_rows = np.sort(allfeeds[group_by].unique())
        # plot_cols = np.sort(allfeeds[color_by].unique())
        # num_plots = int(len(groupby_grps))
        #
        # # Create the palette.
        # colors = plt_help._make_categorial_palette(allfeeds,color_by)
        # palette = dict(zip(color_grps, colors))
        #
        # # Create custom handles for the foodchoice.
        # # See http://matplotlib.org/users/legend_guide.html#using-proxy-artist
        # raster_legend_handles = []
        # for key in palette.keys():
        #     patch = mpatches.Patch(color=palette[key], label=key)
        #     raster_legend_handles.append(patch)
        #
        # # Initialise the figure.
        # # Initialise figure.
        # sns.set(style='ticks',context='poster',font_scale=1.25)
        # if fig_size is None:
        #     x_inches = 10 * col_count
        #     y_inches = 7 * row_count
        # else:
        #     if isinstance(fig_size, tuple) or isinstance(fig_size, list):
        #         x_inches = fig_size[0]
        #         y_inches = fig_size[1]
        #     else:
        #         raise TypeError('Please make sure figsize is a tuple of the '
        #         'form (w,h) in inches.')
        #
        # if ax is None:
        #     fig, axx = plt.subplots(nrows=row_count, ncols=col_count,
        #                             figsize=(x_inches, y_inches),
        #                             gridspec_kw={'wspace':0.3,
        #                                          'hspace':0.3})
        # else:
        #     axx = ax
        #
        # # Loop through each panel.
        # for c, grp in enumerate( groupby_grps ):
        #     if len(groupby_grps)>1:
        #         rasterax = axx[c]
        #     else:
        #         rasterax = axx
        #     print('plotting {0} {1}'.format(grp,'rasters'))
        #     print('Be patient, this can a while!')
        #
        #     # Plot the raster plots.
        #     ## Plot vertical grid lines if desired.
        #     grid_kwargs = dict(linestyle=':', alpha=0.5)
        #     if gridlines_major:
        #         rasterax.xaxis.grid(which='major',linewidth=0.25,**grid_kwargs)
        #     if gridlines_minor:
        #         rasterax.xaxis.grid(which='minor',linewidth=0.15,**grid_kwargs)
        #
        #     ## Grab only the flies we need.
        #     tempfeeds = allfeeds[allfeeds[group_by] == grp].copy()
        #     temp_allflies = tempfeeds.FlyID.unique().tolist()
        #
        #     ## Order the flies properly.
        #     ### First, drop non-valid feeds, then sort by feed time and feed duration,
        #     ### then pull out FlyIDs in that order.
        #     temp_feeding_flies = tempfeeds[~np.isnan(tempfeeds['FeedDuration_s'])].\
        #                             sort_values(['RelativeTime_s','FeedDuration_s']).FlyID.\
        #                             drop_duplicates().tolist()
        #     ### Next, identify which flies did not feed (aka not in list above.)
        #     temp_non_feeding_flies = [fly for fly in temp_allflies
        #     if fly not in temp_feeding_flies]
        #     ### Then, join these two lists.
        #     flies_in_order = temp_feeding_flies + temp_non_feeding_flies
        #
        #     ### Now, plot each fly as a row, and plot each feed as a colored raster for every fly.
        #     flycount = int(len(flies_in_order))
        #     for k, flyid in enumerate(flies_in_order):
        #         tt = tempfeeds[tempfeeds.FlyID == flyid]
        #         for idx in [idx for idx in tt.index if ~np.isnan(tt.loc[idx,'FeedDuration_s'])]:
        #             rasterplot_kwargs = dict(xmin=tt.loc[idx,'RelativeTime_s'],
        #                                    xmax=tt.loc[idx,'RelativeTime_s']+tt.loc[idx,'FeedDuration_s'],
        #
        #                                    ymin=(1/maxflycount)*(maxflycount-k-1),
        #                                    ymax=(1/maxflycount)*(maxflycount-k),
        #
        #                                    color=palette[ tt.loc[idx,color_by] ],
        #                                    label="_"*k + tt.loc[idx,color_by],
        #
        #                                    alpha=0.8)
        #
        #             rasterax.axvspan(**rasterplot_kwargs)
        #
        #         ### Plot the flyid labels if so desired.
        #         if add_flyid_labels:
        #             if flyid in temp_non_feeding_flies:
        #                 label_color = 'grey'
        #             else:
        #                 label_color = 'black'
        #             rasterax.text(-85, (1/maxflycount)*(maxflycount-k-1) + (1/maxflycount)*.5,
        #                         flyid,
        #                         color=label_color,
        #                         verticalalignment='center',
        #                         horizontalalignment='right',
        #                         fontsize=8)
        #     ## Aesthetic tweaks
        #     rasterax.yaxis.set_visible(False)
        #     rasterax.set_title(grp)
        #
        #     ### Format x-axis.
        #     plt_help.format_timecourse_xaxis(rasterax, self.__expt_end_time)
        #
        # ## Despine accordingly (if multiple axes were produced.)
        # ## Note the we remove the left spine (set to True).
        # if len(groupby_grps) > 1:
        #     for a in axx:
        #         sns.despine(ax=a,left=True,trim=True,offset=5)
        # else:
        #     sns.despine(ax=axx,left=True,trim=True,offset=5)
        #
        # # Position the raster color legend.
        # if num_plots>1:
        #     rasterlegend_ax=axx
        # else:
        #     rasterlegend_ax=[ axx ]
        #
        # for a in rasterlegend_ax:
        #     a.legend(loc='upper left',bbox_to_anchor=(0,-0.15),
        #              handles=raster_legend_handles)
        #
        # # End and return the figure.
        # if ax is None:
        #     return axx



    def percent_feeding(self,group_by='Genotype',
                        time_start=0,time_end=360,
                        palette_type='categorical'):
        """
        Produces a lineplot depicting the percent of flies feeding for each condition.
        A 95% confidence interval for each proportion of flies feeding is also given.

        Keywords
        --------
        group_by: string, default 'Genotype'
            The column or label indicating the categorical grouping on the x-axis.

        time_start, time_end: integer, default 0 and 360 respectively
            The time window (in minutes) during which to compute and display the
            percent flies feeding.

        palette_type: string, 'categorical' or 'sequential'.

        Returns
        -------
        A matplotlib Axes instance, and a pandas DataFrame with the statistics.
        """
        import matplotlib.pyplot as plt
        from . import plot_helpers as plt_help
        import seaborn as sns


        # Get plotting variables.
        percent_feeding_summary = plt_help.compute_percent_feeding(self._experiment.flies,
                                                             self._experiment.feeds,
                                                             group_by,
                                                             start=time_start,
                                                             end=time_end)


        cilow = percent_feeding_summary.ci_lower.tolist()
        cihigh = percent_feeding_summary.ci_upper.tolist()
        ydata = percent_feeding_summary.percent_feeding.tolist()

        # Select palette.
        if palette_type == 'categorical':
            color_palette = plt_help._make_categorial_palette(self._experiment.feeds,
                group_by)
        elif palette_type == 'sequential':
            color_palette = plt_help._make_sequential_palette(self._experiment.feeds,
                group_by)

        # Set style.
        sns.set(style='ticks',context='talk',font_scale=1.1)

        # Initialise figure.
        f,ax = plt.subplots(1,figsize=(8,5))
        ax.set_ylim(0,110)
        # Plot 95CI first.
        ax.fill_between(range(0,len(percent_feeding_summary)),
                        cilow,cihigh,
                        alpha=0.25,
                        color='grey' )
        # Then plot the line.
        percent_feeding_summary.percent_feeding.plot.line(ax=ax,
            color='k',lw=1.2)

        for j, s in enumerate(ydata):
            ax.plot(j, s, 'o',
                    color=color_palette[j])

        # Aesthetic tweaks.
        ax.xaxis.set_ticks([i for i in range(0,len(percent_feeding_summary))])
        ax.xaxis.set_ticklabels(percent_feeding_summary.index.tolist())

        xmax = ax.xaxis.get_ticklocs()[-1]
        ax.set_xlim(-0.2, xmax+0.2) # Add x-padding.

        # __rotate_ticks(ax, angle=45, alignment='right')
        for tick in ax.get_xticklabels():
            tick.set_rotation(45)
            tick.set_horizontalalignment('right')

        sns.despine(ax=ax, trim=True, offset={'left':1})
        ax.set_ylabel('Percent Feeding')

        f.tight_layout()
        return f, percent_feeding_summary
