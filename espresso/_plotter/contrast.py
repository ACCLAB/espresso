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
    feed_speed_per_fly

    feed_duration_per_fly
    latency_to_feed_per_fly
    """



    def __init__(self, plotter):
        self.__feeds = plotter._experiment.feeds.copy()
        self.__flies = plotter._experiment.flies
        self.__expt_end_hour = plotter._experiment.expt_duration_minutes / 60
        try:
            self.__added_labels = plotter._experiment.added_labels
        except AttributeError:
            self.__added_labels = [None]



    def feed_count_per_fly(self, group_by, compare_by, start_hour=0,
                           end_hour=None, color_by='Genotype',
                           fig_size=None, ax=None, palette=None,
                           return_plot_data=False,
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
            this column will receive its own 'hub-and-spoke' plot.

        compare_by: string, default None
            Accepts a categorical column in the espresso object. This column
            will be used as the factor for generating and visualizing contrasts.

        start_hour, end_hour: float, defaults 0 and None
            The time window of the experiment to plot. If end_hour is None,
            all feeds until the end of the experiment will be included.

        color_by: string, default 'Genotype'
            Accepts a categorical column in the espresso object. Each group in
            this column will be colored seperately.

        palette: matplotlib palette OR a list of named matplotlib colors.
            Full list of matplotlib palettes
            https://matplotlib.org/examples/color/colormaps_reference.html
            Full list of named matplotlib colors
            https://matplotlib.org/gallery/color/named_colors.html

        return_plot_data: boolean, default False
            If True, the dataframe will be returned after the bootstrap
            statistics.

        contrastplot_kwargs: dict, default None
            All contrastplot keywords will be entered here.

        Returns
        -------

        A matplotlib Figure, and a pandas DataFrame with the statistics.
        """
        from . import plot_helpers as plothelp

        start, end = plothelp.check_time_window(start_hour, end_hour,
                                               self.__expt_end_hour)

        plot_df = plothelp.prep_feeds_for_contrast_plot(self.__feeds,
                                                        self.__flies,
                                                        self.__added_labels,
                                                        group_by, compare_by,
                                                        color_by, start, end,
                                                        type='volume_duration')

        yvar = 'Total\nFeed Count\nPer Fly'
        fig, stats =  plothelp.generic_contrast_plotter(plot_df, yvar, color_by,
                                     fig_size=fig_size, palette=palette,
                                     contrastplot_kwargs=contrastplot_kwargs)

        title = '{} hr to {} hr'.format(start, end)
        fig.suptitle(title, fontsize=36)

        if return_plot_data:
            return fig, stats, plot_df
        else:
            return fig, stats



    def feed_volume_per_fly(self, group_by, compare_by,
                           start_hour=0, end_hour=None,
                           color_by='Genotype', fig_size=None, ax=None,
                           palette=None, volume_unit='nanoliter',
                           return_plot_data=False,
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

        volume_unit: string, default 'nanoliter'
            Accepts 'centiliter' (10^-2 liters), 'milliliter (10^-3 liters)',
            'microliter'(10^-6 liters), 'nanoliter' (10^-9 liters), and
            'picoliter' (10^-12 liters).

        palette: matplotlib palette OR a list of named matplotlib colors.
            Full list of matplotlib palettes
            https://matplotlib.org/examples/color/colormaps_reference.html
            Full list of named matplotlib colors
            https://matplotlib.org/gallery/color/named_colors.html

        return_plot_data: boolean, default False
            If True, the dataframe will be returned after the bootstrap
            statistics.

        contrastplot_kwargs: dict, default None
            All contrastplot keywords will be entered here.

        Returns
        -------

        A matplotlib Figure, and a pandas DataFrame with the statistics.
        """
        from . import plot_helpers as plothelp

        start, end = plothelp.check_time_window(start_hour, end_hour,
                                             self.__expt_end_hour)

        plot_df = plothelp.prep_feeds_for_contrast_plot(self.__feeds,
                                                        self.__flies,
                                                        self.__added_labels,
                                                        group_by, compare_by,
                                                        color_by, start, end,
                                                        type='volume_duration')

        plot_col = 'Total\nFeed Volume\nPer Fly (µl)'

        if volume_unit.strip().split('lit')[0] == 'micro':
            yvar = plot_col
        else:
            multiplier = plothelp.get_unit_multiplier(volume_unit,
                                                      convert_from='micro')
            new_unit = plothelp.get_new_prefix(volume_unit)
            yvar = 'Total\nFeed Volume\nPer Fly ({}l)'.format(new_unit)
            plot_df[yvar] = plot_df[plot_col] * multiplier

        fig, stats =  plothelp.generic_contrast_plotter(plot_df, yvar, color_by,
                                     fig_size=fig_size, palette=palette,
                                     contrastplot_kwargs=contrastplot_kwargs)

        title = '{} hr to {} hr'.format(start, end)
        fig.suptitle(title, fontsize=36)

        if return_plot_data:
            return fig, stats, plot_df
        else:
            return fig, stats


    def feed_speed_per_fly(self, group_by, compare_by,
                           start_hour=0, end_hour=None,
                           color_by='Genotype', fig_size=None,
                           ax=None, volume_unit='nanoliter',
                           palette=None, return_plot_data=False,
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

        volume_unit: string, default 'nanoliter'
            Accepts 'centiliter' (10^-2 liters), 'milliliter (10^-3 liters)',
            'microliter'(10^-6 liters), 'nanoliter' (10^-9 liters), and
            'picoliter' (10^-12 liters).

        palette: matplotlib palette OR a list of named matplotlib colors.
            Full list of matplotlib palettes
            https://matplotlib.org/examples/color/colormaps_reference.html
            Full list of named matplotlib colors
            https://matplotlib.org/gallery/color/named_colors.html

        return_plot_data: boolean, default False
            If True, the dataframe will be returned after the bootstrap
            statistics.

        contrastplot_kwargs: dict, default None
            All contrastplot keywords will be entered here.

        Returns
        -------

        A matplotlib Figure, and a pandas DataFrame with the statistics.
        """
        from . import plot_helpers as plothelp

        start, end = plothelp.check_time_window(start_hour, end_hour,
                                             self.__expt_end_hour)

        plot_df = plothelp.prep_feeds_for_contrast_plot(self.__feeds,
                                                        self.__flies,
                                                        self.__added_labels,
                                                        group_by, compare_by,
                                                        color_by, start, end,
                                                        type='volume_duration')

        plot_col = 'Feed Speed\nPer Fly (nl/s)'

        if volume_unit.strip().split('lit')[0] == 'nano':
            yvar = plot_col
        else:
            multiplier = plothelp.get_unit_multiplier(volume_unit,
                                                      convert_from='nano')
            new_unit = plothelp.get_new_prefix(volume_unit)
            yvar = 'Feed Speed\nPer Fly ({}l/s)'.format(new_unit)
            plot_df[yvar] = plot_df[plot_col] * multiplier


        fig, stats =  plothelp.generic_contrast_plotter(plot_df, yvar, color_by,
                                     fig_size=fig_size, palette=palette,
                                     contrastplot_kwargs=contrastplot_kwargs)

        title = '{} hr to {} hr'.format(start, end)
        fig.suptitle(title, fontsize=36)

        if return_plot_data:
            return fig, stats, plot_df
        else:
            return fig, stats



    def feed_duration_per_fly(self, group_by, compare_by,
                               start_hour=0, end_hour=None,
                               color_by='Genotype', fig_size=None,
                               ax=None, time_unit='minute', palette=None,
                               return_plot_data=False,
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
            this column will be colored seperately.

        time_unit: string, default 'minute'
            Accepts 'second', or 'minute'.

        palette: matplotlib palette OR a list of named matplotlib colors.
            Full list of matplotlib palettes
            https://matplotlib.org/examples/color/colormaps_reference.html
            Full list of named matplotlib colors
            https://matplotlib.org/gallery/color/named_colors.html

        return_plot_data: boolean, default False
            If True, the dataframe will be returned after the bootstrap
            statistics.

        contrastplot_kwargs: dict, default None
            All contrastplot keywords will be entered here.

        Returns
        -------

        A matplotlib Figure, and a pandas DataFrame with the statistics.
        """
        from . import plot_helpers as plothelp

        start, end = plothelp.check_time_window(start_hour, end_hour,
                                             self.__expt_end_hour)
        plot_df = plothelp.prep_feeds_for_contrast_plot(self.__feeds,
                                                        self.__flies,
                                                        self.__added_labels,
                                                        group_by, compare_by,
                                                        color_by, start, end,
                                                        type='volume_duration')

        time_dict = {'second': 'sec', 'minute': 'min'}
        if time_unit not in time_dict.keys():
            raise ValueError("{} is not an accepted unit of time {}"\
                            .format(time_unit, [a for a in time_dict.keys()])
                            )
        yvar = 'Total Time\nFeeding\nPer Fly ({})'.format(time_dict[time_unit])

        fig, stats =  plothelp.generic_contrast_plotter(plot_df, yvar, color_by,
                                     fig_size=fig_size, palette=palette,
                                     contrastplot_kwargs=contrastplot_kwargs)

        title = '{} hr to {} hr'.format(start, end)
        fig.suptitle(title, fontsize=36)

        if return_plot_data:
            return fig, stats, plot_df
        else:
            return fig, stats



    def latency_to_feed_per_fly(self, group_by, compare_by,
                               start_hour=0, end_hour=None,
                               color_by='Genotype', fig_size=None,
                               ax=None, time_unit='minute', palette=None,
                               return_plot_data=False,
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

        time_unit: string, default 'minute'
            Accepts 'second', 'minute', 'hour'.

        palette: matplotlib palette OR a list of named matplotlib colors.
            Full list of matplotlib palettes
            https://matplotlib.org/examples/color/colormaps_reference.html
            Full list of named matplotlib colors
            https://matplotlib.org/gallery/color/named_colors.html

        return_plot_data: boolean, default False
            If True, the dataframe will be returned after the bootstrap
            statistics.

        contrastplot_kwargs: dict, default None
            All contrastplot keywords will be entered here.

        Returns
        -------

        A matplotlib Figure, and a pandas DataFrame with the statistics.
        """
        from . import plot_helpers as plothelp
        from .._munger import munger as munge

        start, end = plothelp.check_time_window(start_hour, end_hour,
                                             self.__expt_end_hour)

        plot_df = plothelp.prep_feeds_for_contrast_plot(self.__feeds,
                                                        self.__flies,
                                                        self.__added_labels,
                                                        group_by, compare_by,
                                                        color_by, start, end,
                                                        type='latency')

        time_dict = {'second': 'sec', 'minute': 'min', 'hour': 'hr'}
        if time_unit not in time_dict.keys():
            raise ValueError("{} is not an accepted unit of time {}"\
                            .format(time_unit, [a for a in time_dict.keys()])
                            )
        yvar = 'Latency to\nFirst Feed ({})'.format(time_dict[time_unit])

        fig, stats =  plothelp.generic_contrast_plotter(plot_df, yvar, color_by,
                                     fig_size=fig_size, palette=palette,
                                     contrastplot_kwargs=contrastplot_kwargs)

        title = '{} hr to {} hr'.format(start, end)
        fig.suptitle(title, fontsize=36)

        if return_plot_data:
            return fig, stats, plot_df
        else:
            return fig, stats
