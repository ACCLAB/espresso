#!/usr/bin/python
# -*-coding: utf-8 -*-
# Author: Joses Ho
# Email : joseshowh@gmail.com

"""
cumulative plotting functions for espresso objects.
"""

# import sys as _sys
# _sys.path.append("..") # so we can import espresso from the directory above.



class cumulative_plotter:
    """
    cumulative plotting class for espresso object.
    """

    #    #    #    #    #####
    #    ##   #    #      #
    #    # #  #    #      #
    #    #  # #    #      #
    #    #   ##    #      #
    #    #    #    #      #

    def __init__(self, plotter): # pass along an espresso_plotter instance.
        self.__feeds = plotter._experiment.feeds.copy()
        self.__expt_end_time = plotter._experiment.expt_duration_seconds

    def __generic_cumulative_plotter(self,
                                     yvar,
                                     group_by=None,
                                     color_by=None,
                                     resample_by='10min',
                                     fig_size=None,
                                     gridlines_major=True,
                                     gridlines_minor=True,
                                     ax=None):
        import numpy as np
        import matplotlib.pyplot as plt
        import seaborn as sns
        from . import plot_helpers as plt_helper
        from .._munger import munger as munge

        # Handle the group_by and color_by keywords.
        group_by, color_by = munge.check_group_by_color_by(group_by,
                                    color_by, self.__feeds)

        print( "Coloring feed volume time course by {0}".format(color_by) )
        print( "Grouping feed volume time course by {0}".format(group_by) )

        if color_by ==group_by: # catch as exception:
            raise ValueError('color_by and group_by both have the same value.'
            'They should be 2 different column names in the feedlog.')

        resampdf = munge.groupby_resamp_sum(self.__feeds, resample_by)
        plotdf = munge.cumsum_for_cumulative(resampdf, group_by, color_by)

        groupby_grps = np.sort( plotdf[group_by].unique() )
        num_plots = int( len(groupby_grps) )

        # Initialise figure.
        sns.set(style='ticks',context='poster')
        if fig_size is None:
            x_inches = 10*num_plots
            y_inches = 7
        else:
            if isinstance(fig_size, tuple) or isinstance(fig_size, list):
                x_inches = fig_size[0]
                y_inches = fig_size[1]
            else:
                raise TypeError('Please make sure figsize is a tuple of the form (w,h) in inches.')

        if ax is None:
            fig,axx = plt.subplots(nrows = 1,
                                    ncols=num_plots,
                                    figsize=(x_inches,y_inches),
                                    gridspec_kw={'wspace':0.2})
        else:
            axx = ax

        # Loop through each panel.
        for c, grp in enumerate( groupby_grps ):
            if len(groupby_grps)>1:
                plotax = axx[c]
            else:
                plotax = axx

            ### Plot vertical grid lines if desired.
            if gridlines_major:
                plotax.xaxis.grid(True,linestyle='dotted',
                    which='major',lw = 0.5,alpha = 1)
            if gridlines_minor:
                plotax.xaxis.grid(True,linestyle='dotted',
                    which='minor',lw = 0.25,alpha = 0.5)

            ## Filter plotdf according to group_by.
            temp_plotdf = plotdf[plotdf[group_by] == grp]

            ### and make timeseries plot.
            temp_plotdf_groupby = temp_plotdf.groupby([color_by,'time_s'])
            temp_plotdf_mean = temp_plotdf_groupby.mean().unstack()[yvar].T
            temp_plotdf_mean.plot(ax=plotax,lw=1)

            temp_plotdf_halfci = temp_plotdf_groupby.sem().unstack()[yvar].T * 1.96
            lower_ci = temp_plotdf_mean-temp_plotdf_halfci
            upper_ci = temp_plotdf_mean+temp_plotdf_halfci

            lower_ci[lower_ci<0] = 0 # Make sure no CI drops below zero.

            for c in temp_plotdf_mean.columns:
                plotax.fill_between(temp_plotdf_mean.index,
                                   lower_ci[c],upper_ci[c],
                                   alpha = 0.25)

            ## Add the group name as title.
            plotax.set_title(grp)
            ## Format x-axis.
            plt_helper.format_timecourse_xaxis(plotax, self.__expt_end_time)

        # Normalize all the y-axis limits.
        if num_plots > 1:
            plt_helper.normalize_ylims(axx,include_zero = True)
            ## Despine and offset each axis.
            for a in axx:
                sns.despine(ax=a, trim=True, offset=5)
        else:
            axx.set_ylim(-2, axx.get_ylim()[1]) # Ensure zero is displayed!
            sns.despine(ax=axx, trim=True, offset=5)

        # Position the raster color legend,
        # and label the y-axis appropriately.
        if num_plots>1:
            rasterlegend_ax = axx
        else:
            rasterlegend_ax = [axx]
        for a in rasterlegend_ax:
            a.legend(loc='upper left' ,bbox_to_anchor=(0,-0.15))
            ## Set label for y-axis..
            a.set_ylabel(yvar)

        # End and return the figure.
        if ax is None:
            return axx

    def consumption(self,
                    group_by = None,
                    color_by = None,
                    resample_by='10min',
                    fig_size = None,
                    gridlines_major = True,
                    gridlines_minor = True,
                    ax = None):
        """
        Produces a cumulative line plot depicting the average total volume consumed per fly
        for the entire assay. The plot will be tiled horizontally according to the
        category "group_by", and will be colored according to the category
        "color_by". Feed volumes will be binned by the duration in `resample_by`.

        keywords
        --------
        group_by: string, default None
            Accepts a categorical column in the espresso object. Each group in this column
            will be plotted on its own axes.

        color_by: string, default None
            Accepts a categorical column in the espresso object. Each group in this column
            will be colored seperately, and stacked as an area plot.

        resample_by: string, default '10min'
            The time frequency used to bin the timecourse data. For the format, please see
            http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases

        fig_size: tuple (width, height), default None
            The size of the final figure, in inches.

        gridlines_major, gridlines_minor: boolean, default True
            Whether or not major and minor vertical gridlines are displayed.

        ax: array of matplotlib Axes objects, default None
            Given an array of Axes, each category (as dictacted by group_by) will be plotted
            respectively.

        Returns
        -------
        matplotlib AxesSubplot(s)
        """
        out = self.__generic_cumulative_plotter(yvar='Cumulative Volume (nl)',
                                              group_by = group_by,
                                              color_by = color_by,
                                              resample_by = resample_by,
                                              fig_size = fig_size,
                                              gridlines_major = gridlines_major,
                                              gridlines_minor = gridlines_minor,
                                              ax = ax)
        return out

    def feed_count(self,
                   group_by = None,
                   color_by = None,
                   resample_by='10min',
                   fig_size = None,
                   gridlines_major = True,
                   gridlines_minor = True,
                   ax = None):
        """
        Produces a cumulative line plot depicting the average total feed count consumed per fly
        for the entire assay. The plot will be tiled horizontally according to the
        category "group_by", and will be colored according to the category
        "color_by". Feed volumes will be binned by the duration in `resample_by`.

        keywords
        --------
        group_by: string, default None
            Accepts a categorical column in the espresso object. Each group in this column
            will be plotted on its own axes.

        color_by: string, default None
            Accepts a categorical column in the espresso object. Each group in this column
            will be colored seperately, and stacked as an area plot.

        resample_by: string, default '10min'
            The time frequency used to bin the timecourse data. For the format, please see
            http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases

        fig_size: tuple (width, height), default None
            The size of the final figure, in inches.

        gridlines_major, gridlines_minor: boolean, default True
            Whether or not major and minor vertical gridlines are displayed.

        ax: array of matplotlib Axes objects, default None
            Given an array of Axes, each category (as dictacted by group_by) will be plotted
            respectively.

        Returns
        -------
        matplotlib AxesSubplot(s)
        """
        out = self.__generic_cumulative_plotter(yvar='Cumulative Feed Count',
                                              group_by = group_by,
                                              color_by = color_by,
                                              resample_by = resample_by,
                                              fig_size = fig_size,
                                              gridlines_major = gridlines_major,
                                              gridlines_minor = gridlines_minor,
                                              ax = ax)
        return out
