#!/usr/bin/python
# -*-coding: utf-8 -*-
# Author: Joses Ho
# Email : joseshowh@gmail.com

"""
Convenience functions for munging of metadata and feedlogs.
"""



def metadata(path_to_csv):
    """
    Munges a metadata CSV from an ESPRESSO experiment.
    Returns a pandas DataFrame.
    """
    import os
    from numpy import repeat as nprepeat
    from pandas import read_csv

    # Read in metadata.
    metadata_csv = read_csv(path_to_csv)
    # Remove all columns that have all values missing.
    metadata_csv.dropna(axis=1, how='all', inplace=True)
    # Check that the metadata has a nonzero number of rows.
    if len(metadata_csv) == 0:
        raise ValueError(metadata+' has 0 rows. Please check!!!')

    # Add ``#Flies` column if it is not in the metadata.
    # Assume that there is 1 fly per chamber if the metadata did not
    # have a `#Flies` column.
    if '#Flies' not in metadata_csv.columns:
        metadata_csv['#Flies'] = nprepeat(1, len(metadata_csv))

    # Rename columns.
    food_cols = metadata_csv.filter(regex='Food').columns
    rename_dict = {c: c.replace("Food ", "Tube") for c in food_cols}

    rename_dict['Volume-mm3'] = 'FeedVol_µl'
    rename_dict['Duration-ms'] = 'FeedDuration_ms'
    rename_dict['RelativeTime-s'] = 'RelativeTime_s'
    rename_dict['#Flies'] = 'FlyCountInChamber'
    metadata_csv.rename(columns=rename_dict, inplace=True)


    # Try to deal with inconsistencies in how metadata is recorded.
    # Do keep this section updated whenever new inconsistencies are spotted.
    tube_cols = [c.replace("Food ", "Tube") for c in food_cols]
    for c in tube_cols:
        try:
            metadata_csv.loc[:,c] = metadata_csv[c]\
                                    .str.replace('5%S','5% sucrose ')\
                                    .str.replace('5%YE',' 5% yeast extract')
        except AttributeError:
            pass

    # Turn N/A in FlyCountInChamber to 1.
    fc = metadata_csv.FlyCountInChamber
    metadata_csv.loc[:,'FlyCountInChamber'] = fc.fillna(value=1).astype(int)

    return metadata_csv




def feedlog(path_to_csv):
    """
    Munges a feedlog CSV from an ESPRESSO experiment.
    Returns a pandas DataFrame.
    """
    from pandas import read_csv

    # Read in the CSV.
    feedlog_csv = read_csv(path_to_csv)

    # Rename columns.
    feedlog_csv.rename(columns={"FlyID"             :    "ChamberID",
                                "Food 1"            :    "Tube1",
                                "Food 2"            :    "Tube2",
                                'Volume-mm3'        :   'FeedVol_µl',
                                'Duration-ms'       :   'FeedDuration_ms',
                                'RelativeTime-s'    :   'RelativeTime_s'},
                        inplace=True)

    # Check that the feedlog has a nonzero number of rows.
    if len(feedlog_csv) == 0:
        raise ValueError(feedlog+' has 0 rows. Please check!!!')

    # Drop the feed events where `AviFile` is "Null",
    # as well as events that have a negative `RelativeTime-s`.
    feedlog_csv.drop(feedlog_csv[feedlog_csv.AviFile == 'Null'].index,
                     inplace = True)
    feedlog_csv.drop(feedlog_csv[feedlog_csv['RelativeTime_s'] < 0].index,
                     inplace = True)

    # You have to ADD 1 to match the feedlog ChamberID with the corresponding ChamberID
    #  in `metadata_csv`.
    feedlog_csv.ChamberID = feedlog_csv.ChamberID + 1

    return feedlog_csv



def add_padrows(metadata, feedlog, time_end, time_start=0):
    """
    Define 2 padrows per fly, per food choice. This will ensure that feedlogs
    for each ChamberID fully capture the entire experiment duration.

    Keywords
    --------
    metadata_df: pandas DataFrame
        A (munged) Espresso metadata.

    feedlog_df: pandas DataFrame
        The corresponding (munged) Espresso feedlog.

    time_end, time_start: int
        In seconds. The timepoints at which to add padrows.

    Returns
    -------
    The modified feedlog. By default, two padrows will be added: a padrow at 0.5
    seconds after the start of the experiment, and a padrow 4 min, 49 sec seconds
    after the experiment was concluded.
    """

    from numpy import nan as npnan
    from numpy import repeat
    from pandas import Series, DataFrame

    f = feedlog.copy()

    feed_cols = f.columns
    ncols = len(feed_cols)
    end_time = time_end + 289 # 289 seconds = 4 min, 49 sec.

    all_padrows = []

    for chamberid in metadata.ChamberID.unique():
        for choice in feedlog.FoodChoice.unique().tolist():

            padrow1 = Series(repeat(npnan, ncols), index=feed_cols)
            padrow2 = Series(repeat(npnan, ncols), index=feed_cols)

            padrow1.loc['RelativeTime_s'] = time_start + 0.5
            padrow2.loc['RelativeTime_s'] = end_time

            padrows = [padrow1, padrow2]

            for padrow in padrows:
                padrow.loc['FoodChoice'] = choice
                padrow.loc['ChamberID'] = chamberid
                padrow.loc['Valid'] = False
                padrow.loc['ExperimentState'] = 'PAD'

                # padrow.loc['AverageFeedVolumePerFly_µl'] = 0
                # padrow.loc['AverageFeedCountPerFly'] = 0

            all_padrows = all_padrows + padrows
    return f.append(all_padrows, ignore_index=True, sort=False)



def compute_nanoliter_cols(feedlog_df):
    """
    Computes feed volume and feed speed in nanoliters. Adds these two values as new columns.

    Pass along a munged feedlog. Returns the modified feedlog.
    """
    f = feedlog_df.copy()
    # Compute feed volume in nanoliters for convenience.
    f['FeedVol_nl'] = f['FeedVol_µl'] * 1000
    # Compute feeding speed.
    f['FeedSpeed_nl/s'] = f['FeedVol_nl'] / (f['FeedDuration_ms']/1000)
    return f




def compute_time_cols(feedlog_df):
    """
    ©Computes RelativeTime_s and FeedDuration_s. Adds these two values as new columns.

    Pass along a munged feedlog. Returns the modified feedlog.
    """
    f = feedlog_df.copy()
    f['FeedDuration_s'] = f.FeedDuration_ms / 1000
    return f


def add_time_column(df):
    """
    Convenience function to add a non DateTime column representing the time.
    """
    temp = df.copy()
    rt = temp.loc[:,'RelativeTime_s']
    temp['time_s'] = rt.dt.hour*3600 + rt.dt.minute*60 + rt.dt.second

    return temp




def average_feed_vol_per_fly(df):
    """
    Computes AverageFeedVolumePerFly in µl for each feed.
    Adds this value as new columns.

    Pass along a merged feedlog-metadata DataFrame. Returns the modified DataFrame.
    """
    f = df.copy()
    fly_count_in_chamber = f['FlyCountInChamber'].astype(float)
    f['AverageFeedVolumePerFly_µl'] = f['FeedVol_µl'] / fly_count_in_chamber
    return f



def average_feed_count_per_fly(df):
    """
    Computes AverageFeedCountPerChamber for each feed. This seems redundant,
    but serves a crucial munging purpose when we are producing timecourse plots.
    Adds this value as new columns.

    Pass along a merged feedlog-metadata DataFrame. Returns the modified DataFrame.
    """
    f = df.copy()
    fly_count_in_chamber = f['FlyCountInChamber'].astype(float)
    f['AverageFeedCountPerFly'] = f['Valid'] / fly_count_in_chamber
    return f



def average_feed_speed_per_fly(df):
    """
    Computes AverageFeedSpeedPerFly_µl/s for each feed.

    Pass along a merged feedlog-metadata DataFrame. Returns the modified DataFrame.
    """
    f = df.copy()
    fly_count_in_chamber = f['FlyCountInChamber'].astype(float)
    f['AverageFeedSpeedPerFly_µl/s'] = (f['FeedVol_µl'] / (f['FeedDuration_ms']/1000)) / fly_count_in_chamber
    return f



def detect_non_feeding_flies(metadata_df,feedlog_df):
    """
    Detects non-feeding flies.

    Pass along a munged metadata and corresponding munged feedlog.
    Returns the non-feeding flies as a list.
    """
    non_feeding_flies = [chamberid for chamberid in metadata_df.ChamberID.unique()
                        if chamberid not in feedlog_df.dropna().ChamberID.unique()]
    return non_feeding_flies



def make_categorical_columns(df, added_labels=None):
    """
    Turns Genotype, Status, Temperature, Sex, FlyCountInChamber columns
    into Categorical columns, inplace.

    If there are added labels, this is also done.
    """

    import numpy as np
    import pandas as pd

    # Assign Status based on genotype.
    assigned_status = df.Genotype.astype(str).apply(assign_status_from_genotype)

    # Turn Status into an Ordered Categorical.
    df['Status'] = pd.Categorical(assigned_status,
                                  categories=['Sibling', 'Offspring'],
                                  ordered=True)

    # Turn Genotype into an Ordered Categorical
    genotypes_ordered = [a for a in df.sort_values(['Status', 'Genotype'])\
                                      .Genotype.unique()
                         if a is not None]
    df.loc[:, 'Genotype'] = pd.Categorical(df.Genotype,
                                           categories=genotypes_ordered,
                                           ordered=True)

    # Change relevant columns to Categorical.
    if added_labels is None:
        cols = ['Temperature', 'Sex', 'FlyCountInChamber']
    else:
        cols = ['Temperature', 'Sex', 'FlyCountInChamber', *added_labels]

    for col in cols:
        try:
            c = df[col]
            df.loc[:, col] = pd.Categorical(c, categories=np.sort(c.unique()),
                                            ordered=True)
        except KeyError:
            pass

    # Remove unused categories.
    for c in ['Status', 'Genotype', *cols]:
        df.loc[:, c].cat.remove_unused_categories(inplace=True)



def check_column(col, df):
    """
    Convenience function to check if a dataframe has a column of interest.
    """
    if not isinstance(col, str): # if col is not a string.
        err = "{} is not a string.".format(col) + \
              " Please enter a column name from `feeds` with quotation marks."
        raise TypeError(errstr)
    if col not in df.columns: # make sure col is a column in df.
        err = "{} is not a column in the feedlog. Please check.".format(col)
        raise KeyError(err)
    pass




def check_group_by_color_by(col, row, color_by, df):
    """
    Check to see if `row`, `col` and `color_by` (if supplied) are columns in `df`.
    """
    not_none = [c for c in [col, row, color_by] if c is not None]

    if len(not_none) > 0:
        for contrast in not_none:
            check_column(contrast, df)

    # if col == color_by or row == color_by:
    #     if color_by is not None:
    #         err = '{} is the same as {} or {}.'.format(color_by, row, col)
    #         raise ValueError(err)

    if col == row:
        if col is not None:
            err1 = 'Row variable {} is the same '.format(row)
            err2 = 'as column variable {}.'.format(col)

            raise ValueError(err1 + err2)

        # else:
        #     err = 'Both {} and {} are None.'.format(row, col)
        #     raise ValueError(err)



def groupby_resamp_sum(feeds, group_by_cols, resample_by='10min'):
    """
    Convenience function to groupby and then resample a feedlog DataFrame.
    """
    from pandas import to_datetime
    # from . import __static as static

    # gbp_cols = [*static.grpby_cols,
    #             *[a for a in added_labels if a in feeds.columns],
    #             ]


    # Convert RelativeTime_s to datetime if not done so already.
    if feeds.RelativeTime_s.dtype == 'float64':
        feeds.loc[:,'RelativeTime_s'] = to_datetime(feeds['RelativeTime_s'],
                                                    unit='s')

    gbp_cols  = group_by_cols + ["ChamberID"]
    df_groupby_resamp_sum = feeds.groupby(gbp_cols)\
                                 .resample(resample_by, on='RelativeTime_s')\
                                 .sum()
    df_groupby_resamp_sum.reset_index(inplace=True)

    return df_groupby_resamp_sum




def sum_for_timecourse(resamp_feeds):
    """
    Convenience function to sum a resampled feedlog for timecourse plotting.
    """
    from pandas import DataFrame
    # from . import __static as static

    temp = resamp_feeds.copy()
    temp_sum = DataFrame(temp.to_records())

    # gbp_cols = [*static.grpby_cols,
    #             *[a for a in added_labels if a in temp_sum.columns]
    #             ]

    cols_of_interest = ['ChamberID', 'RelativeTime_s',
                        'AverageFeedVolumePerFly_µl',
                        'AverageFeedCountPerFly',
                        'AverageFeedSpeedPerFly_µl/s'
                        ]

    temp_sum = temp_sum[cols_of_interest]

    temp_sum.fillna(0, inplace=True)
    # temp_sum = add_time_column(temp_sum)

    return temp_sum



def groupby_sum_for_timecourse(resampdf, row, col, color_by):
    from pandas import DataFrame
    from numpy import unique

    group_by_cols = unique([a for a in [row, col, color_by, 'time_s']
                           if a is not None]
                           ).tolist()
    out = resampdf.groupby(group_by_cols).sum()

    # if row == col:
    #     reorder = [a for a in [row, color_by, 'time_s']
    #                   if a is not None]
    # else:
    #     reorder = [a for a in [row, col, color_by, 'time_s']
    #                   if a is not None]
    #
    # out.index = out.index.reorder_levels(reorder)

    return out



def cumsum_for_cumulative(df, group_by_cols):
    """
    Convenience function to sum a resampled feedlog for timecourse plotting.
    """
    from pandas import merge

    """
    Convenience function to sum a resampled feedlog for timecourse plotting.
    """
    from pandas import merge

    temp = df.copy()

    # Rename for facility in plotting.
    temp.rename(columns={'AverageFeedVolumePerFly_µl':'Cumulative Volume (µl)',
                          'AverageFeedCountPerFly':'Cumulative Feed Count'},
                inplace=True)


    # Select only relevant columns.
    for_cumsum = ['RelativeTime_s', 'ChamberID',
                  'Cumulative Feed Count',
                  'Cumulative Volume (µl)']

    # Compute the cumulative sum, by Chamber.
    grs_cumsum = temp[for_cumsum].groupby('ChamberID').cumsum()

    # Combine metadata with cumsum.
    out = merge(grs_cumsum,
                temp[group_by_cols + ['RelativeTime_s', 'ChamberID']],
                left_index=True, right_index=True)

    # Add time column to facilitate plotting.
    out = add_time_column(out)

    return out



def assign_food_choice(chamberid, choiceid, mapper):
    """ Convenience function used to assign the food choice. """
    from numpy import nan
    try:
        return mapper.loc[chamberid, 'Tube{}'.format(choiceid)]

    except KeyError:
        return nan



def assign_status_from_genotype(genotype):
    """ Convenience function to map genotype to status."""
    if 'w1118' in genotype.lower():
        status = 'Sibling'
    else:
        status = 'Offspring'

    return status



def join_cols(df, cols, sep='; '):
    """
    Convenience function to concatenate all the columns found in
    the list `cols`, with `sep` as the delimiter.

    Keywords
    --------

    df: a pandas DataFrame

    cols: a list of column names in `df`.

    sep: str, default '; '
        The delimiter used to seperate the concatenated columns.
    """

    try:
        base_col = df[ cols[0] ].astype(str).copy()

        if len(cols)>1: # if more than one column...
            col_list = cols[1:].copy()
            try:
                for j,col in enumerate(col_list):
                    out_col = base_col + sep + df[ col ].astype(str)
                    base_col = out_col
                return out_col
            except KeyError:
                    print('`{}` is not found in the feeds. Please check.'.format(col))
        else:
            # only one column in list; so do nothing.
            return base_col

    except KeyError:
        print('`{}` is not found in the feeds. Please check.'.format(cols[0]))



def cat_categorical_columns(df, group_by, compare_by):
    """
    Convenience function to concatenate categorical columns for
    contrast plotting purposes.
    """
    from pandas import Categorical
    df_out = df.copy()

    if isinstance(group_by, str):
        df_out['plot_groups'] = df_out[group_by]
        gby = [group_by, ]
    elif isinstance(group_by, (list, tuple)):
        # create new categorical column.
        df_out['plot_groups'] = join_cols(df_out, group_by)
        gby = ['plot_groups',]

    gby.append(compare_by)
    # Create another categorical column.
    df_out['plot_groups_with_contrast'] = join_cols(df_out, gby)
    sorted_plot_groups = df_out.plot_groups_with_contrast.unique()
    df_out.loc[:, 'plot_groups_with_contrast'] = Categorical(
                                                df_out.plot_groups_with_contrast,
                                                categories=sorted_plot_groups,
                                                ordered=True)

    return df_out



def contrast_plot_munger(feeds, flies, added_labels, group_by, compare_by,
                         color_by, start_hour, end_hour):
    """Convenience Function for munging before contrast plotting."""

    from numpy import unique, repeat
    from numpy import nan as npnan
    from pandas import Series, DataFrame, concat, merge
    # from . import __static as static


    df = feeds.copy()
    flies_ = flies.copy()
    flies_indexed = flies_.set_index('ChamberID')

    if isinstance(group_by, str):
        if group_by == compare_by:
            raise ValueError("`group_by` and `compare_by` cannot be identical.")
        gby = ["ChamberID", compare_by, color_by, group_by]
        cat_cols = [compare_by, color_by, group_by]

    elif isinstance(group_by, (tuple, list)):
        if compare_by in group_by:
            raise ValueError("`compare_by` cannot be one of the factors" +
                             " in `group_by.`")
        gby = ["ChamberID", compare_by, color_by, *group_by]
        cat_cols = [compare_by, color_by, *group_by]

    for c in cat_cols:
        check_column(c, df)

    if len(df[compare_by].unique()) < 2:
        err = '{} has less than 2 categories'.format(compare_by) + \
              ' and cannot be used for `compare_by`.'
        raise ValueError(err)


    # Select feeds in time window
    after_start = df.RelativeTime_s > start_hour * 3600
    before_end = df.RelativeTime_s < end_hour * 3600
    df_in_window = df[after_start & before_end].copy()

    # Add padrows for food choices that did not get fed upon within
    # the time window.
    inactive_chambers_in_time_window = [c for c in flies_.ChamberID.unique()
                                        if c not in df_in_window.ChamberID.unique()]
    # spacer_timepont = ((end_hour + start_hour) / 2) * 3600

    padrows = []
    for chamberid in inactive_chambers_in_time_window:
        for choice in df.FoodChoice.unique().tolist():
            padrow = Series(repeat(npnan, len(df.columns)),
                            index=df.columns)
            padrow.loc['FoodChoice'] = choice
            padrow.loc['ChamberID'] = chamberid
            padrow.loc['ExperimentState'] = "PAD"
            for g in [c for c in gby
                      if c in flies_indexed.columns]:
                padrow.loc[g] = flies_indexed.loc[chamberid, g]
            padrows.append(padrow)

    padded = DataFrame(padrows)

    for c in ['AverageFeedVolumePerFly_µl', 'AverageFeedCountPerFly']:
        padded.loc[:, c] = repeat(0, len(padded))
    df_in_window_padded = df_in_window.append(padded, ignore_index=True, sort=False)

    # Groupby and sum.
    grouped_sum = df_in_window_padded.groupby(gby).sum()
    # Groupby and min for latency to first feed.
    grouped_min = df_in_window_padded.dropna().groupby(gby).min()
    for g in [grouped_sum, grouped_min]:
        g.reset_index(inplace=True)
        g.sort_values(gby, inplace=True)


    grp_sum = grouped_sum[[*gby, "FeedDuration_ms",
                           'AverageFeedVolumePerFly_µl',
                           'AverageFeedCountPerFly',
                           'AverageFeedSpeedPerFly_µl/s']].copy()

    grp_min = grouped_min[[*gby, "RelativeTime_s"]].copy()

    grp_sum.set_index(gby, inplace=True)
    grp_min.set_index(gby, inplace=True)

    plotdf = merge(left=grp_sum, right=grp_min, how='outer',
                   left_index=True, right_index=True).reset_index()

    if "FoodChoice" in gby:
        plotdf.set_index(["ChamberID", "FoodChoice"], inplace=True)

        # Figure out which chamber-food choice combi does not exist.
        all_combis = df.groupby(['ChamberID', 'FoodChoice']).count().index

        missing_combis = all_combis.difference(plotdf.index)

        # Add pads.
        # Because we've accounted for chambers that did not feed at all,
        # the chambers in `missing_combis` should have at least one feed.
        # We can pull these chambers out.
        missing_rows = []

        for t in missing_combis:
            chamberid = t[0]
            foodchoice = t[1]

            temp_row = plotdf.loc[(chamberid,)].reset_index().drop("FoodChoice", axis=1)
            temp_row["ChamberID"] = chamberid
            temp_row["FoodChoice"] = foodchoice

            for c in ['AverageFeedVolumePerFly_µl', 'AverageFeedCountPerFly', 'FeedDuration_ms']:
                temp_row.loc[:, c] = 0
            for c in ['RelativeTime_s', 'AverageFeedSpeedPerFly_µl/s']:
                temp_row.loc[:, c] = npnan
            missing_rows.append(temp_row)

        if len(missing_rows) > 0:
            missing = concat(missing_rows)
            plotdf = plotdf.reset_index().append(missing, ignore_index=True, sort=False)
            plotdf.sort_values(gby, inplace=True)

        else:
            plotdf.reset_index(inplace=True)

    # # Add padrows for food choices that did not get fed upon within
    # # the time window.
    # spacer_timepont = ((end_hour + start_hour) / 2) * 3600
    # padrows = []
    # for chamberid in flies_.ChamberID.unique():
    #     for choice in df.FoodChoice.unique().tolist():
    #         padrow = Series(repeat(npnan, len(df.columns)),
    #                         index=df.columns)
    #         padrow.loc['FoodChoice'] = choice
    #         padrow.loc['ChamberID'] = chamberid
    #         for g in [c for c in gby
    #                   if c in flies_indexed.columns]:
    #             padrow.loc[g] = flies_indexed.loc[chamberid, g]
    #         padrows.append(padrow)
    # df_in_window = df_in_window.append(padrows, ignore_index=True,
    #                                     sort=False)
    #
    #
    # # Groupby and sum.
    # grouped_sum = df_in_window.groupby(gby).sum()
    # # Groupby and min for latency to first feed.
    # grouped_min = df_in_window.dropna().groupby(gby).min()
    # for g in [grouped_sum, grouped_min]:
    #     g.reset_index(inplace=True)
    #     g.sort_values(gby, inplace=True)
    # # Merge.
    # grouped = merge(left=grouped_sum.drop("RelativeTime_s", axis=1),
    #                 right=grouped_min[['ChamberID', 'RelativeTime_s']],
    #                 left_on='ChamberID', right_on='ChamberID'
    #                   )
    #
    # # Handle numerical columns properly.
    # for col in ['AverageFeedSpeedPerFly_µl/s']:
    #     grouped[col].replace(to_replace=0, value=npnan, inplace=True)
    #
    # # Handle categorical columns.
    # # Have to do this because something like Temperature will become
    # # non-categorical
    # to_drop = [c for c in cat_cols if c in flies_.columns]
    # grouped.drop(to_drop, inplace=True, axis=1)
    # # Add the categories columns
    # to_add = [c for c in gby if c in flies_.columns]
    # metadata_for_merge = flies_[to_add]
    #
    # # merge the data for plotting.
    # plot_df = merge(left=grouped, right=metadata_for_merge,
    #                    left_on="ChamberID", right_on="ChamberID")
    # # Drop superfluous columns.
    # plot_df.drop(["Valid"], axis=1, inplace=True)

    # Rename columns for easy plotting.
    plotdf['RelativeTime_min'] = plotdf['RelativeTime_s'] / 60
    plotdf['RelativeTime_hour'] = plotdf['RelativeTime_min'] / 60

    plotdf['FeedDuration_min'] = plotdf['FeedDuration_ms'] / 60000

    av = plotdf['AverageFeedVolumePerFly_µl']
    t = plotdf['FeedDuration_ms']
    plotdf['Feed Speed\nPer Fly (nl/s)'] = (av / t) * 1000000

    rename_cols = {
        'AverageFeedCountPerFly'     :  'Total\nFeed Count\nPer Fly',
        'AverageFeedVolumePerFly_µl' :  'Total\nFeed Volume\nPer Fly (µl)',

        'FeedDuration_min'           :  'Total Time\nFeeding\nPer Fly (min)',
        'FeedDuration_s'             :  'Total Time\nFeeding\nPer Fly (sec)',

        'RelativeTime_min'           :    'Latency to\nFirst Feed (min)',
        'RelativeTime_sec'           :    'Latency to\nFirst Feed (sec)',
        'RelativeTime_hour'          :    'Latency to\nFirst Feed (hr)'}
    plotdf.rename(columns=rename_cols, inplace=True)

    plotdf = cat_categorical_columns(plotdf, group_by, compare_by)

    return plotdf



def merge_two_dicts(x, y):
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



# def latency_munger(feeds, group_by, compare_by, color_by, start_hour, end_hour):
#     """Convenience Function to get latency of first feeds."""
#     from numpy import unique
#     from pandas import DataFrame
#     from . import __static as static
#
#     grpby_cols = static.grpby_cols.copy()
#     # grpby_cols_all = unique(grpby_cols + [group_by, compare_by, color_by])\
#     #                  .tolist()
#     df = feeds.copy()
#
#     if isinstance(group_by, str):
#         to_check = [compare_by, color_by, group_by]
#     elif isinstance(group_by, (tuple, list)):
#         to_check = [compare_by, color_by, *group_by]
#     for c in to_check:
#         check_column(c, df)
#
#     gby = [*to_check, *grpby_cols]
#     grpby_cols_all = unique(gby).tolist()
#
#     for c in [compare_by, color_by]:
#         check_column(c, df)
#
#     if len(df[compare_by].unique())<2:
#         err = '{} has less than 2 categories'.format(compare_by) + \
#               'and cannot be used for `compare_by`.'
#         raise ValueError(err)
#
#     to_drop_na_cols = grpby_cols_all + ['RelativeTime_s']
#
#     # Select feeds in time window
#     after_start = df.RelativeTime_s > start_hour * 3600
#     before_end = df.RelativeTime_s < end_hour * 3600
#     df_in_time_window = df[after_start & before_end]
#
#     plot_df = DataFrame(df_in_time_window.dropna()[to_drop_na_cols]\
#                                          .groupby(grpby_cols_all)\
#                                          .min().to_records())\
#                         .dropna() # for some reason, groupby produces NaN rows..
#
#     plot_df.reset_index(drop=True, inplace=True)
#     plot_df['RelativeTime_min'] = plot_df['RelativeTime_s'] / 60
#     plot_df.rename(columns={'RelativeTime_min':'Latency to\nFirst Feed (min)',
#                             'RelativeTime_s':'Latency to\nFirst Feed (sec)'},
#                    inplace=True)
#     plot_df = cat_categorical_columns(plot_df, group_by, compare_by)
#
#     return plot_df
