#!/usr/bin/python
# -*-coding: utf-8 -*-
# Author: Joses Ho
# Email : joseshowh@gmail.com

"""
contrast plot functions for espresso objects.
"""

class contrast_plotter:
    """
    contrast plotting class for espresso object.

    Available methods
    -----------------
    feed_count_per_fly
    feed_volume_per_fly
    feed_duration_per_fly
    feed_speed_per_fly
    latency_to_feed_per_fly
    """



    def __init__(self,plotter):
        self.__feeds=plotter._experiment.feeds.copy()



    def feed_count_per_fly(self,
                           group_by,
                           compare_by,
                           color_by='Genotype',
                           fig_size=None,
                           ax=None,
                           palette_type='categorical',
                           contrastplot_kwargs=None):

        """
        Produces a contrast plot depicting the mean differences in the feed
        counts between groups.

        Place any contrast plot keywords in a dictionary and pass in through
        `contrastplot_kwargs`.

        Keywords
        --------
        group_by: string, default None
            Accepts a categorical column in the espresso object. Each group in
            this column
            will receive its own 'hub-and-spoke' plot.

        compare_by: string, default None
            Accepts a categorical column in the espresso object. This column
            will be used
            as the factor for generating and visualizing contrasts.

        color_by: string, default 'Genotype'
            Accepts a categorical column in the espresso object. Each group in
            this column
            will be colored seperately.

        palette_type: string, 'categorical' or 'sequential'.

        contrastplot_kwargs: dict, default None
            All contrastplot keywords will be entered here.

        Returns
        -------

        A matplotlib Figure, and a pandas DataFrame with the statistics.
        """
        from .._munger import munger as munge
        from . import plot_helpers as pth
        plot_df = munge.volume_duration_munger(self.__feeds,
                                              group_by, compare_by, color_by)

        yvar = 'Total Feed Count\nPer Fly'

        return pth.generic_contrast_plotter(plot_df, yvar, color_by,
                                     fig_size=fig_size,
                                     palette_type=palette_type,
                                     contrastplot_kwargs=contrastplot_kwargs)



    def feed_volume_per_fly(self,
                           group_by,
                           compare_by,
                           color_by='Genotype',
                           fig_size=None,
                           ax=None,
                           palette_type='categorical',
                           contrastplot_kwargs=None):

        """
        Produces a contrast plot depicting the mean differences in the feed
        volumes between groups.

        Place any contrast plot keywords in a dictionary and pass in through
        `contrastplot_kwargs`.

        Keywords
        --------
        group_by: string, default None
            Accepts a categorical column in the espresso object. Each group in
            this column will receive its own 'hub-and-spoke' plot.

        compare_by: string, default None
            Accepts a categorical column in the espresso object. This column
            will be used as the factor for generating and visualizing contrasts.

        color_by: string, default 'Genotype'
            Accepts a categorical column in the espresso object. Each group in
            this column will be colored seperately.

        palette_type: string, 'categorical' or 'sequential'.

        contrastplot_kwargs: dict, default None
            All contrastplot keywords will be entered here.

        Returns
        -------

        A matplotlib Figure, and a pandas DataFrame with the statistics.
        """
        from .._munger import munger as munge
        from . import plot_helpers as pth
        plot_df = munge.volume_duration_munger(self.__feeds,
                                              group_by, compare_by, color_by)

        yvar = 'Total Feed Volume\nPer Fly (µl)'

        return pth.generic_contrast_plotter(plot_df, yvar, color_by,
                                     fig_size=fig_size,
                                     palette_type=palette_type,
                                     contrastplot_kwargs=contrastplot_kwargs)



    def feed_duration_per_fly(self,
                           group_by,
                           compare_by,
                           color_by='Genotype',
                           fig_size=None,
                           ax=None,
                           palette_type='categorical',
                           contrastplot_kwargs=None):

        """
        Produces a contrast plot depicting the mean differences in the feed
        durations between groups.

        Place any contrast plot keywords in a dictionary and pass in through
        `contrastplot_kwargs`.

        Keywords
        --------
        group_by: string, default None
            Accepts a categorical column in the espresso object. Each group in
            this column
            will receive its own 'hub-and-spoke' plot.

        compare_by: string, default None
            Accepts a categorical column in the espresso object. This column
            will be used
            as the factor for generating and visualizing contrasts.

        color_by: string, default 'Genotype'
            Accepts a categorical column in the espresso object. Each group in
            this column
            will be colored seperately.

        palette_type: string, 'categorical' or 'sequential'.

        contrastplot_kwargs: dict, default None
            All contrastplot keywords will be entered here.

        Returns
        -------

        A matplotlib Figure, and a pandas DataFrame with the statistics.
        """
        from .._munger import munger as munge
        from . import plot_helpers as pth
        plot_df = munge.volume_duration_munger(self.__feeds,
                                              group_by, compare_by, color_by)

        yvar = 'Total Time\nFeeding Per Fly (min)'

        return pth.generic_contrast_plotter(plot_df, yvar, color_by,
                                     fig_size=fig_size,
                                     palette_type=palette_type,
                                     contrastplot_kwargs=contrastplot_kwargs)



    def feed_speed_per_fly(self,
                           group_by,
                           compare_by,
                           color_by='Genotype',
                           fig_size=None,
                           ax=None,
                           palette_type='categorical',
                           contrastplot_kwargs=None):

        """
        Produces a contrast plot depicting the mean differences in the feed
        speeds (across the entire assay duration) between groups.

        Place any contrast plot keywords in a dictionary and pass in through
        `contrastplot_kwargs`.

        Keywords
        --------
        group_by: string, default None
            Accepts a categorical column in the espresso object. Each group in
            this column will receive its own 'hub-and-spoke' plot.

        compare_by: string, default None
            Accepts a categorical column in the espresso object. This column
            will be used as the factor for generating and visualizing contrasts.

        color_by: string, default 'Genotype'
            Accepts a categorical column in the espresso object. Each group in
            this column will be colored seperately.

        palette_type: string, 'categorical' or 'sequential'.

        contrastplot_kwargs: dict, default None
            All contrastplot keywords will be entered here.

        Returns
        -------

        A matplotlib Figure, and a pandas DataFrame with the statistics.
        """
        from .._munger import munger as munge
        from . import plot_helpers as pth
        plot_df = munge.volume_duration_munger(self.__feeds,
                                              group_by, compare_by, color_by)

        yvar = 'Feed Speed\nPer Fly (nl/s)'

        return pth.generic_contrast_plotter(plot_df, yvar, color_by,
                                     fig_size=fig_size,
                                     palette_type=palette_type,
                                     contrastplot_kwargs=contrastplot_kwargs)



    def latency_to_feed_per_fly(self,
                                group_by,
                                compare_by,
                                color_by='Genotype',
                                fig_size=None,
                                ax=None,
                                palette_type='categorical',
                                contrastplot_kwargs=None):

        """
        Produces a contrast plot depicting the mean differences in the latency
        to first feed between groups.

        Place any contrast plot keywords in a dictionary and pass in through
        `contrastplot_kwargs`.

        Keywords
        --------
        group_by: string, default None
            Accepts a categorical column in the espresso object. Each group in
            this column will receive its own 'hub-and-spoke' plot.

        compare_by: string, default None
            Accepts a categorical column in the espresso object. This column
            will be used as the factor for generating and visualizing contrasts.

        color_by: string, default 'Genotype'
            Accepts a categorical column in the espresso object. Each group in
            this column will be colored seperately.

        palette_type: string, 'categorical' or 'sequential'.

        contrastplot_kwargs: dict, default None
            All contrastplot keywords will be entered here.

        Returns
        -------

        A matplotlib Figure, and a pandas DataFrame with the statistics.
        """
        from .._munger import munger as munge
        from . import plot_helpers as pth
        plot_df = munge.latency_munger(self.__feeds,
                                      group_by, compare_by, color_by)

        yvar = 'Latency to\nFirst Feed (min)'

        return pth.generic_contrast_plotter(plot_df, yvar, color_by,
                                     fig_size=fig_size,
                                     palette_type=palette_type,
                                     contrastplot_kwargs=contrastplot_kwargs)
