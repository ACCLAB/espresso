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

    #    #    #    #    #####
    #    ##   #    #      #
    #    # #  #    #      #
    #    #  # #    #      #
    #    #   ##    #      #
    #    #    #    #      #

    def __init__(self,plotter):
        self.__feeds=plotter._experiment.feeds.copy()


    def __volume_duration_munger(self,
                                 df,
                                 group_by,
                                 compare_by,
                                 color_by):

        import pandas as pd
        from .._munger import munger as munge

        df = self.__feeds.copy()

        for c in [compare_by,color_by]:
            munge.check_column(c,df)

        if len( df[compare_by].unique() )<2:
            raise ValueError('{} has less than 2 categories and cannot be used for `compare_by`.'.format(compare_by))

        for col in ['AverageFeedVolumePerFly_µl','FeedDuration_ms']:
            df[col].fillna(value=0,inplace=True)

        plot_df=pd.DataFrame(df[['Temperature','Genotype','FoodChoice','FlyID',
                                   'AverageFeedCountPerFly',
                                   'AverageFeedVolumePerFly_µl',
                                   'FeedDuration_ms']]\
                            .groupby(['Temperature','Genotype','FoodChoice','FlyID'])\
                            .sum()\
                            .to_records() )\
                    .dropna() # for some reason, groupby produces NaN rows...

        plot_df.reset_index(drop=True, inplace=True)
        plot_df['FeedDuration_min']=plot_df['FeedDuration_ms']/60000
        plot_df['Feed Speed\nPer Fly (nl/s)']=(plot_df['AverageFeedVolumePerFly_µl'] / plot_df['FeedDuration_ms'])*1000000
        plot_df.rename(columns={'AverageFeedCountPerFly':'Total Feed Count\nPer Fly',
                               'AverageFeedVolumePerFly_µl':'Total Feed Volume\nPer Fly (µl)',
                               'FeedDuration_min':'Total Time\nFeeding Per Fly (min)'},
                       inplace=True)
        plot_df = munge.cat_categorical_columns(plot_df,group_by,compare_by)

        return plot_df

    def __latency_munger(self,
                         df,
                         group_by,
                         compare_by,
                         color_by):
        import pandas as pd
        from .._munger import munger as munge

        df = self.__feeds.copy()

        for c in [compare_by,color_by]:
            munge.check_column(c,df)

        if len( df[compare_by].unique() )<2:
            raise ValueError('{} has less than 2 categories and cannot be used for `compare_by`.'.format(compare_by))

        plot_df = pd.DataFrame(df.dropna()[['Temperature','Genotype',
                                            'FoodChoice','FlyID',
                                            'RelativeTime_s']]\
                                 .groupby(['Temperature','Genotype',
                                           'FoodChoice','FlyID'])\
                                 .min()\
                                 .to_records() )\
                     .dropna() # for some reason, groupby produces NaN rows...

        plot_df.reset_index(drop=True, inplace=True)
        plot_df['RelativeTime_min']=plot_df['RelativeTime_s']/60
        plot_df.rename(columns={'RelativeTime_min':'Latency to\nFirst Feed (min)'},
                       inplace=True)
        plot_df = munge.cat_categorical_columns(plot_df, group_by, compare_by)

        return plot_df

    def __merge_two_dicts(x, y):
        """
        Given two dicts, merge them into a new dict as a shallow copy.
        Any overlapping keys in `y` will override the values in `x`.

        Taken from https://stackoverflow.com/questions/38987/
        how-to-merge-two-python-dictionaries-in-a-single-expression

        Keywords:
            x, y: dicts

        Returns:
            A dictionary containing a union of all keys in both original dicts.
        """
        z = x.copy()
        z.update(y)
        return z

    def __generic_contrast_plotter(self,
                                   plot_df, yvar,
                                   color_by,
                                   fig_size=None,
                                   palette_type='categorical',
                                   contrastplot_kwargs=None):

        from . import plot_helpers as pth
        import numpy as np
        import dabest

        # Handle contrastplot keyword arguments.
        default_kwargs = dict(fig_size=(12,9),
                              float_contrast=False,
                              font_scale=1.4,
                              swarmplot_kwargs={'size':6})
        if contrastplot_kwargs is None:
            contrastplot_kwargs = default_kwargs
        else:
            contrastplot_kwargs = __merge_two_dicts(default_kwargs,
                contrastplot_kwargs)

        # Select palette.
        if palette_type == 'categorical':
            color_palette = pth._make_categorial_palette(plot_df, color_by)
        elif palette_type == 'sequential':
            color_palette = pth._make_sequential_palette(plot_df, color_by)

        custom_pal = dict(zip(plot_df[color_by].unique(),
                              color_palette))

        # Properly arrange idx for grouping.
        unique_ids = np.sort(plot_df.plot_groups_with_contrast.unique())
        split_idxs = np.array_split(unique_ids,
            len(plot_df.plot_groups.unique()))
        idx = [tuple(i) for i in split_idxs]

        # Make sure the ylims don't stretch below zero but still capture all
        # the datapoints.
        ymax = np.max(plot_df[yvar])*1.1

        f,b = dabest.plot(plot_df,
                          x='plot_groups_with_contrast',
                          y=yvar,
                          idx=idx,
                          color_col=color_by,
                          custom_palette=custom_pal,
                          swarm_ylim=(-ymax/70, ymax),
                          **contrastplot_kwargs)
        return f, b


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
        plot_df = self.__volume_duration_munger(self.__feeds,
                                              group_by, compare_by, color_by)

        yvar = 'Total Feed Count\nPer Fly'

        return self.__generic_contrast_plotter(plot_df, yvar, color_by,
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
        plot_df = self.__volume_duration_munger(self.__feeds,
                                              group_by, compare_by, color_by)

        yvar = 'Total Feed Volume\nPer Fly (µl)'

        return self.__generic_contrast_plotter(plot_df, yvar, color_by,
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
        plot_df = self.__volume_duration_munger(self.__feeds,
                                              group_by, compare_by, color_by)

        yvar = 'Total Time\nFeeding Per Fly (min)'

        return self.__generic_contrast_plotter(plot_df, yvar, color_by,
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
        plot_df = self.__volume_duration_munger(self.__feeds,
                                              group_by, compare_by, color_by)

        yvar = 'Feed Speed\nPer Fly (nl/s)'

        return self.__generic_contrast_plotter(plot_df, yvar, color_by,
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
        plot_df = self.__latency_munger(self.__feeds,
                                      group_by, compare_by, color_by)

        yvar = 'Latency to\nFirst Feed (min)'

        return self.__generic_contrast_plotter(plot_df, yvar, color_by,
                                     fig_size=fig_size,
                                     palette_type=palette_type,
                                     contrastplot_kwargs=contrastplot_kwargs)
