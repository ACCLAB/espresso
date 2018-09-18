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
    latency_to_feed
    """



    def __init__(self, plotter):
        self.__feeds = plotter._experiment.feeds.copy()
        self.__flies = plotter._experiment.flies
        self.__expt_end_hour = plotter._experiment.expt_duration_minutes / 60
        try:
            self.__added_labels = plotter._experiment.added_labels
        except AttributeError:
            self.__added_labels = [None]



    def feed_count_per_fly(self, group_by, compare_by, color_by='Genotype',
                           start_hour=0, end_hour=None, return_plot_data=False,
                           **kwargs):

        """
        Produces a contrast plot depicting the mean differences in the average
        feed count per fly between groups.

        Chambers that did not have a single feed in the time window will have
        a value of 0.

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

        start_hour, end_hour: float, defaults 0 and None
            The time window of the experiment to plot. If end_hour is None,
            all feeds until the end of the experiment will be included.

        return_plot_data: boolean, default False
            If True, the dataframe will be returned after the bootstrap
            statistics.

        kwargs: "keyword=value" pairings
            Any keywords that `dabest.plot()` accepts can be used.
            See https://acclab.github.io/DABEST-python-docs/api.html

        Returns
        -------
        A matplotlib Figure, and a pandas DataFrame with the statistics.
        If `return_plot_data` is True, a second DataFrame will be returned as
        well, consisting of the data used to produce the plot.
        """

        from . import plot_helpers as plothelp

        start, end = plothelp.check_time_window(start_hour, end_hour,
                                                self.__expt_end_hour)

        plot_df = plothelp.prep_feeds_for_contrast_plot(self.__feeds,
                                                        self.__flies,
                                                        self.__added_labels,
                                                        group_by, compare_by,
                                                        color_by, start, end)

        yvar = 'Total\nFeed Count\nPer Fly'
        kwargs['float_contrast'] = False # Fix this as False!
        fig, stats =  plothelp.dabest_plotter(plot_df, yvar, color_by, **kwargs)

        title = '{} hr to {} hr'.format(start, end)
        fig.suptitle(title, fontsize=36)

        if return_plot_data:
            return fig, stats, plot_df
        else:
            return fig, stats



    def feed_volume_per_fly(self, group_by, compare_by, color_by='Genotype',
                            start_hour=0, end_hour=None, return_plot_data=False,
                            volume_unit='nanoliter', **kwargs):

        """
        Produces a contrast plot depicting the mean differences in the average
        feed volume per fly, between groups.

        Chambers that did not have a single feed in the time window will have
        a value of 0.

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

        start_hour, end_hour: float, defaults 0 and None
            The time window of the experiment to plot. If end_hour is None,
            all feeds until the end of the experiment will be included.

        return_plot_data: boolean, default False
            If True, the dataframe will be returned after the bootstrap
            statistics.

        volume_unit: string, default 'nanoliter'
            Accepts 'centiliter' (10^-2 liters), 'milliliter (10^-3 liters)',
            'microliter'(10^-6 liters), 'nanoliter' (10^-9 liters), and
            'picoliter' (10^-12 liters).

        kwargs: "keyword=value" pairings
            Any keywords that `dabest.plot()` accepts can be used.
            See https://acclab.github.io/DABEST-python-docs/api.html

        Returns
        -------
        A matplotlib Figure, and a pandas DataFrame with the statistics.
        If `return_plot_data` is True, a second DataFrame will be returned as
        well, consisting of the data used to produce the plot.
        """

        from . import plot_helpers as plothelp

        start, end = plothelp.check_time_window(start_hour, end_hour,
                                             self.__expt_end_hour)

        plot_df = plothelp.prep_feeds_for_contrast_plot(self.__feeds,
                                                        self.__flies,
                                                        self.__added_labels,
                                                        group_by, compare_by,
                                                        color_by, start, end)

        plot_col = 'Total\nFeed Volume\nPer Fly (µl)'

        if volume_unit.strip().split('lit')[0] == 'micro':
            yvar = plot_col
        else:
            multiplier = plothelp.get_unit_multiplier(volume_unit,
                                                      convert_from='micro')
            new_unit = plothelp.get_new_prefix(volume_unit)
            yvar = 'Total\nFeed Volume\nPer Fly ({}l)'.format(new_unit)
            plot_df[yvar] = plot_df[plot_col] * multiplier

        kwargs['float_contrast'] = False # Fix this as False!
        fig, stats =  plothelp.dabest_plotter(plot_df, yvar, color_by, **kwargs)

        title = '{} hr to {} hr'.format(start, end)
        fig.suptitle(title, fontsize=36)

        if return_plot_data:
            return fig, stats, plot_df
        else:
            return fig, stats


    def feed_speed_per_fly(self, group_by, compare_by, color_by='Genotype',
                           start_hour=0, end_hour=None, return_plot_data=False,
                           volume_unit='nanoliter', **kwargs):

        """
        Produces a contrast plot depicting the mean differences in the average
        feed speeds per fly between groups.

        Flies that did not have a single feed within the time window will not
        be included in the plot.

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

        start_hour, end_hour: float, defaults 0 and None
            The time window of the experiment to plot. If end_hour is None,
            all feeds until the end of the experiment will be included.

        return_plot_data: boolean, default False
            If True, the dataframe will be returned after the bootstrap
            statistics.

        volume_unit: string, default 'nanoliter'
            Accepts 'centiliter' (10^-2 liters), 'milliliter (10^-3 liters)',
            'microliter'(10^-6 liters), 'nanoliter' (10^-9 liters), and
            'picoliter' (10^-12 liters).

        kwargs: "keyword=value" pairings
            Any keywords that `dabest.plot()` accepts can be used.
            See https://acclab.github.io/DABEST-python-docs/api.html

        Returns
        -------
        A matplotlib Figure, and a pandas DataFrame with the statistics.
        If `return_plot_data` is True, a second DataFrame will be returned as
        well, consisting of the data used to produce the plot.
        """

        from . import plot_helpers as plothelp

        start, end = plothelp.check_time_window(start_hour, end_hour,
                                             self.__expt_end_hour)

        plot_df = plothelp.prep_feeds_for_contrast_plot(self.__feeds,
                                                        self.__flies,
                                                        self.__added_labels,
                                                        group_by, compare_by,
                                                        color_by, start, end)

        plot_col = 'Feed Speed\nPer Fly (nl/s)'

        if volume_unit.strip().split('lit')[0] == 'nano':
            yvar = plot_col
        else:
            multiplier = plothelp.get_unit_multiplier(volume_unit,
                                                      convert_from='nano')
            new_unit = plothelp.get_new_prefix(volume_unit)
            yvar = 'Feed Speed\nPer Fly ({}l/s)'.format(new_unit)
            plot_df[yvar] = plot_df[plot_col] * multiplier

        kwargs['float_contrast'] = False # Fix this as False!
        fig, stats =  plothelp.dabest_plotter(plot_df, yvar, color_by, **kwargs)

        title = '{} hr to {} hr'.format(start, end)
        fig.suptitle(title, fontsize=36)

        if return_plot_data:
            return fig, stats, plot_df
        else:
            return fig, stats



    def feed_duration_per_fly(self, group_by, compare_by, start_hour=0,
                           end_hour=None, time_unit='minute',
                           color_by='Genotype', return_plot_data=False,
                           **kwargs):

        """
        Produces a contrast plot depicting the mean differences in the average
        feed duration per fly between groups.

        Chambers that did not record a single feed during the time window will
        have a feed duration of zero.

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

        start_hour, end_hour: float, defaults 0 and None
            The time window of the experiment to plot. If end_hour is None,
            all feeds until the end of the experiment will be included.

        return_plot_data: boolean, default False
            If True, the dataframe will be returned after the bootstrap
            statistics.

        time_unit: string, default 'minute'
            Accepts 'second', or 'minute'.

        kwargs: "keyword=value" pairings
            Any keywords that `dabest.plot()` accepts can be used.
            See https://acclab.github.io/DABEST-python-docs/api.html

        Returns
        -------
        A matplotlib Figure, and a pandas DataFrame with the statistics.
        If `return_plot_data` is True, a second DataFrame will be returned as
        well, consisting of the data used to produce the plot.
        """

        from . import plot_helpers as plothelp

        start, end = plothelp.check_time_window(start_hour, end_hour,
                                             self.__expt_end_hour)
        plot_df = plothelp.prep_feeds_for_contrast_plot(self.__feeds,
                                                        self.__flies,
                                                        self.__added_labels,
                                                        group_by, compare_by,
                                                        color_by, start, end)

        time_dict = {'second': 'sec', 'minute': 'min'}
        if time_unit not in time_dict.keys():
            raise ValueError("{} is not an accepted unit of time {}"\
                            .format(time_unit, [a for a in time_dict.keys()])
                            )
        yvar = 'Total Time\nFeeding\nPer Fly ({})'.format(time_dict[time_unit])
        kwargs['float_contrast'] = False # Fix this as False!
        fig, stats =  plothelp.dabest_plotter(plot_df, yvar, color_by, **kwargs)

        title = '{} hr to {} hr'.format(start, end)
        fig.suptitle(title, fontsize=36)

        if return_plot_data:
            return fig, stats, plot_df
        else:
            return fig, stats



    def latency_to_feed_per_fly(self, group_by, compare_by, time_unit='minute',
                                color_by='Genotype', return_plot_data=False,
                                **kwargs):

        """
        Produces a contrast plot depicting the mean differences in the latency
        to first feed between groups.

        This plot displays the first feed recorded for each chamber, and performs
        estimation statistics on these latencies.

        If a given food choice was not fed from during the entire assay duration,
        that chamber will not be included in this plot.

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

        return_plot_data: boolean, default False
            If True, the dataframe will be returned after the bootstrap
            statistics.

        time_unit: string, default 'minute'
            Accepts 'second', 'minute', 'hour'.

        kwargs: "keyword=value" pairings
            Any keywords that `dabest.plot()` accepts can be used.
            See https://acclab.github.io/DABEST-python-docs/api.html

        Returns
        -------
        A matplotlib Figure, and a pandas DataFrame with the statistics.
        If `return_plot_data` is True, a second DataFrame will be returned as
        well, consisting of the data used to produce the plot.
        """
        from . import plot_helpers as plothelp
        from .._munger import munger as munge

        end_hr = self.__expt_end_hour
        plot_df = plothelp.prep_feeds_for_contrast_plot(self.__feeds,
                                                        self.__flies,
                                                        self.__added_labels,
                                                        group_by, compare_by,
                                                        color_by, start_hour=0,
                                                        end_hour=end_hr
                                                        )

        time_dict = {'second':  'sec',
                     'minute':  'min',
                     'hour'  :  'hr'}
        if time_unit not in time_dict.keys():
            raise ValueError("{} is not an accepted unit of time {}"\
                            .format(time_unit, [a for a in time_dict.keys()])
                            )
        yvar = 'Latency to\nFirst Feed ({})'.format(time_dict[time_unit])
        kwargs['float_contrast'] = False # Fix this as False!
        fig, stats =  plothelp.dabest_plotter(plot_df, yvar, color_by, **kwargs)

        title = '{} hr to {} hr'.format(0, end_hr)
        fig.suptitle(title, fontsize=36)

        if return_plot_data:
            return fig, stats, plot_df
        else:
            return fig, stats
