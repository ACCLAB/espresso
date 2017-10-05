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
    """

    #    #    #    #    #####
    #    ##   #    #      #
    #    # #  #    #      #
    #    #  # #    #      #
    #    #   ##    #      #
    #    #    #    #      #

    def __init__(self,plotter):
        self.__feeds=plotter._experiment.feeds.copy()

    def __generic_contrast_plotter(self,
                                   df,
                                   yvar,
                                   color_by=None,
                                   fig_size=None,
                                   ax=None,
                                   contrastplot_kwargs=None):

        import numpy as __np
        import pandas as __pd

        import bootstrap_contrast as __bsc

        from . import plot_helpers as __pth
        from _munger import munger as __munger

        # Handle the yvar and color_by keywords.
        __munger.check_column(yvar,df)
        if color_by is not None:
            __munger.check_column(color_by,df)

        # Handle contrastplot keyword arguments.
        default_kwargs=dict(fig_size=(12,9),
                            float_contrast=False,
                            font_scale=1.4,
                            swarmplot_kwargs={'size':6,
                                              'hue':color_by})
        if contrastplot_kwargs is None:
            contrastplot_kwargs=default_kwargs
        else:
            contrastplot_kwargs=__bsc.merge_two_dicts(default_kwargs,contrastplot_kwargs)

        # Select palette.
        if palette_type=='categorical':
            color_palette=__pth._make_categorial_palette(df,group_by)
        elif palette_type=='sequential':
            color_palette=__pth._make_sequential_palette(df,group_by)

        f,b=__bsc.contrastplot(data=df,
                              x=group_by,y=yvar,
                              idx=__np.sort(total_feeds.loc[:,group_by].unique()),
                              **contrastplot_kwargs)
        return f,b

    def feed_count_per_fly(self,
                           color_by=None,
                           fig_size=None,
                           ax=None,
                           palette_type='categorical',
                           contrastplot_kwargs=None):

        """
        Produces a contrast plot depicting the mean differences in the feed counts between groups.
        Place any contrast plot keywords in a dictionary and pass in through `contrastplot_kwargs`.

        Keywords
        --------
        group_by: string, default None
            Accepts a categorical column in the espresso object. Each group in this column
            will be plotted on its own axes.

        color_by: string, default None
            Accepts a categorical column in the espresso object. Each group in this column
            will be colored seperately, and stacked as an area plot.

        palette_type: string, 'categorical' or 'sequential'.

        contrastplot_kwargs: dict, default None
            All contrastplot keywords will be entered here.

        Returns
        -------

        A matplotlib Figure, and a pandas DataFrame with the statistics.
        """
        import numpy as __np
        import pandas as __pd

        total_feeds=__pd.DataFrame(self.__feeds[['FlyID',group_by,'FeedVol_nl']].\
                                    groupby([group_by,'FlyID']).count().\
                                    to_records())
        total_feeds.columns=[group_by,'FlyID','Total feed count\nper fly']
        max_feeds=__np.round(total_feeds.max()['Total feed count\nper fly'],decimals=-2)

        f, b=__generic_contrast_plotter(yvar='Total feed count\nper fly',
                                        color_by=color_by,
                                        fig_size=fig_size,
                                        ax=ax,
                                        palette_type='categorical',
                                        contrastplot_kwargs=contrastplot_kwargs)
        f.suptitle('Contrast Plot Total Feed Count Per Fly')

        return f, b
