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
    import numpy as np
    import pandas as pd

    ## Read in metadata.
    metadata_csv = pd.read_csv(path_to_csv)
    ## Check that the metadata has a nonzero number of rows.
    if len(metadata_csv) == 0:
        raise ValueError(metadata+' has 0 rows. Please check!!!')

    ## Add ``#Flies` column if it is not in the metadata.
    ## Assume that there is 1 fly per chamber if the metadata did not
    ## have a `#Flies` column.
    if '#Flies' not in metadata_csv.columns:
        metadata_csv['#Flies'] = np.repeat(1, len(metadata_csv))

    ## Rename columns.
    food_cols = metadata_csv.filter(regex='Food').columns
    rename_dict = {c: c.replace("Food ", "Tube") for c in food_cols}

    rename_dict['Volume-mm3'] = 'FeedVol_µl'
    rename_dict['Duration-ms'] = 'FeedDuration_ms'
    rename_dict['RelativeTime-s'] = 'RelativeTime_s'
    rename_dict['#Flies'] = 'FlyCountInChamber'
    metadata_csv.rename(columns=rename_dict, inplace=True)


    ## Try to deal with inconsistencies in how metadata is recorded.
    ## Do keep this section updated whenever new inconsistencies are spotted.
    tube_cols = [c.replace("Food ", "Tube") for c in food_cols]
    for c in tube_cols:
        try:
            metadata_csv.loc[:,c] = metadata_csv[c]\
                                    .str.replace('5%S','5% sucrose ')\
                                    .str.replace('5%YE',' 5% yeast extract')
        except AttributeError:
            pass

    # Turn N/A in #Flies to 1.
    metadata_csv.loc[:,'FlyCountInChamber'] = metadata_csv.FlyCountInChamber.fillna(value=1).astype(int)

    return metadata_csv




def feedlog(path_to_csv):
    """
    Munges a feedlog CSV from an ESPRESSO experiment.
    Returns a pandas DataFrame.
    """
    import pandas as pd

    # Read in the CSV.
    feedlog_csv = pd.read_csv( path_to_csv )

    # Rename columns.
    feedlog_csv.rename(columns={"Food 1":"Tube1",
                                "Food 2":"Tube2",
                                'Volume-mm3':'FeedVol_µl',
                                'Duration-ms':'FeedDuration_ms',
                                'RelativeTime-s':'RelativeTime_s'},
                        inplace = True)

    # Check that the feedlog has a nonzero number of rows.
    if len(feedlog_csv) == 0:
        raise ValueError(feedlog+' has 0 rows. Please check!!!')

    # Drop the feed events where `AviFile` is "Null",
    # as well as events that have a negative `RelativeTime-s`.
    feedlog_csv.drop(feedlog_csv[feedlog_csv.AviFile == 'Null'].index,
                     inplace = True)
    feedlog_csv.drop(feedlog_csv[feedlog_csv['RelativeTime_s']<0].index,
                     inplace = True)

    # You have to ADD 1 to match the feedlog FlyID with the corresponding FlyID
    #  in `metadata_csv`.
    feedlog_csv.FlyID = feedlog_csv.FlyID + 1

    return feedlog_csv



def add_padrows(metadata_df, feedlog_df, expt_duration):
    """
    Define 2 padrows per fly, per food choice. This will ensure that feedlogs
    for each FlyID fully capture the entire 6-hour duration.

    Keywords
    --------
    metadata_df: pandas DataFrame
        A (munged) Espresso metadata.

    feedlog_df: pandas DataFrame
        The corresponding (munged) Espresso feedlog.

    expt_duration: int, default 21600
        The total length of the experiment, in seconds. The default is six
        hours.

    Returns
    -------
    The modified feedlog. By default, two padrows will be added: a padrow at 0.5
    seconds, and a padrow at `expt_duration` with 4 min and 49 seconds added.
    """

    import numpy as np
    import pandas as pd

    f = feedlog_df.copy()
    end_time = expt_duration + 289 # 289 seconds = # 4 min, 49 sec.
    for flyid in metadata_df.FlyID.unique():
        for choice in f.ChoiceIdx.unique():
            padrows = pd.DataFrame( [
                                    [np.nan,np.nan,choice,
                                     flyid,choice,'NIL',
                                     np.nan,np.nan,np.nan,
                                     False,0.5,'PAD'], # 0.5 seconds

                                   [np.nan,np.nan,choice,
                                    flyid,choice,'NIL',
                                    np.nan,np.nan,np.nan,
                                    False, end_time,'PAD']
                                   ] )
            padrows.columns = f.columns
            # Add the padrows to feedlog.
            # There is no `inplace` argument for append.
            f = f.append(padrows, ignore_index = True)
    return f




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
    f['FeedDuration_s'] = f.FeedDuration_ms/1000
    return f


def __add_time_column(df):
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
    f['AverageFeedVolumePerFly_µl'] = f['FeedVol_µl'] / f['FlyCountInChamber']
    return f

def average_feed_count_per_fly(df):
    """
    Computes AverageFeedCountPerChamber for each feed. This seems redundant,
    but serves a crucial munging purpose when we are producing timecourse plots.
    Adds this value as new columns.

    Pass along a merged feedlog-metadata DataFrame. Returns the modified DataFrame.
    """
    f = df.copy()
    f['AverageFeedCountPerFly'] = f['Valid'] / f['FlyCountInChamber']
    return f

def average_feed_speed_per_fly(df):
    """
    Computes AverageFeedSpeedPerFly_µl/s for each feed.

    Pass along a merged feedlog-metadata DataFrame. Returns the modified DataFrame.
    """
    f = df.copy()
    f['AverageFeedSpeedPerFly_µl/s'] = (f['FeedVol_µl'] / (f['FeedDuration_ms']/1000)) / f['FlyCountInChamber']
    return f




def detect_non_feeding_flies(metadata_df,feedlog_df):
    """
    Detects non-feeding flies.

    Pass along a munged metadata and corresponding munged feedlog.
    Returns the non-feeding flies as a list.
    """
    non_feeding_flies=[ flyid for flyid in metadata_df.FlyID.unique() if flyid not in feedlog_df.dropna().FlyID.unique() ]
    return non_feeding_flies





def check_column(col, df):
    """
    Convenience function to check if a dataframe has a column of interest.
    """
    if not isinstance(col, str): # if col is not a string.
        raise TypeError("{} is not a string. Please enter a column name from `feeds` with quotation marks.".format(col))
    if col not in df.columns: # make sure col is a column in df.
        raise KeyError("{} is not a column in the feedlog. Please check.".format(col))
    pass




def check_group_by_color_by(col, row, color_by, df):
    """
    Check to see if `row`, `col` and `color_by` (if supplied) are columns in `df`.
    If not, assign them default values of "Genotype" and "FoodChoice" respectively.
    """
    not_none = [c for c in [col, row, color_by] if c is not None]
    for contrast in not_none:
        check_column(contrast, df)

    if col == color_by or row == color_by:
        raise ValueError('{} is the same as {} or {}.'.format(color_by, row, col))
    if col == row:
        raise ValueError('Row variable {} is the same as column variable {}.'.format(row, col))

def groupby_resamp_sum(df, resample_by='10min'):
    """
    Convenience function to groupby and then resample a feedlog DataFrame.
    """

    import pandas as pd
    # Convert RelativeTime_s to datetime if not done so already.
    if df.RelativeTime_s.dtype == 'float64':
        df.loc[:,'RelativeTime_s'] = pd.to_datetime(df['RelativeTime_s'],
                                                    unit='s')

    df_groupby_resamp_sum = df.groupby(['Temperature','Status',
                                        'Genotype','Sex',
                                        'FlyID','FoodChoice'])\
                              .resample(resample_by,
                                        on='RelativeTime_s')\
                              .sum()

    return df_groupby_resamp_sum




def sum_for_timecourse(df):
    """
    Convenience function to sum a resampled feedlog for timecourse plotting.
    """
    import pandas as pd

    temp = df.copy()
    temp_sum = pd.DataFrame(temp.to_records())

    temp_sum = temp_sum[['Temperature','Status','Genotype',
                        'Sex','FlyID','FoodChoice',
                        'RelativeTime_s',
                        'FlyCountInChamber',
                        ### Below, add all the columns that are
                         ### potentially used for plotting.
                         'AverageFeedVolumePerFly_µl',
                         'AverageFeedCountPerFly',
                         'AverageFeedSpeedPerFly_µl/s']]

    temp_sum.fillna(0,inplace = True)
    temp_sum = __add_time_column(temp_sum)

    return temp_sum




def cumsum_for_cumulative(df):
    """
    Convenience function to sum a resampled feedlog for timecourse plotting.
    """
    import pandas as pd

    temp = df.copy()

    # # Drop duplicate columns:
    # duplicated_cols = [col for col in [group_by, color_by]
    #                    if col in temp.columns]
    # for col in [duplicated_cols]:
    #     temp.drop(col, axis=1, inplace=True)

    # Rename for facility in plotting.
    temp.rename(columns={'AverageFeedVolumePerFly_µl':'Cumulative Volume (µl)',
                          'AverageFeedCountPerFly':'Cumulative Feed Count'},
                inplace=True)

    temp['Cumulative Volume (nl)'] = temp['Cumulative Volume (µl)'] * 1000

    # Select only relevant columns.
    temp = pd.DataFrame(temp.to_records())[['RelativeTime_s','FlyID',
                                            'Temperature','Status',
                                            'Genotype','Sex','FoodChoice',
                                            'Cumulative Feed Count',
                                            'Cumulative Volume (nl)']]

    # Compute the cumulative sum, by Fly.
    grs_cumsum_a = temp.groupby(['Temperature','Status',
                                'Genotype','Sex',
                                'FlyID','FoodChoice']).cumsum()

    # Combine metadata with cumsum.
    grs_cumsum = pd.merge(temp[['RelativeTime_s','Temperature',
                                'Status','Genotype','Sex',
                                'FlyID','FoodChoice']],
                          grs_cumsum_a,
                          left_index=True,
                          right_index=True)

    # Add time column to facilitate plotting.
    grs_cumsum = __add_time_column(grs_cumsum)

    # temp_cumsum = temp.groupby(['Temperature','Genotype','FlyID','FoodChoice'])\
    #                 .cumsum()\
    #                 .groupby(['Temperature','Genotype','FlyID','FoodChoice'])\
    #                 .fillna(method='ffill')\
    #                 .fillna(0)
    #
    # temp_cumsum = pd.DataFrame( temp_cumsum.to_records() )
    #
    # # Select only relavant columns.
    # temp_cumsum = temp_cumsum[[group_by,color_by,
    #                          'FlyID',
    #                          'RelativeTime_s',
    #                          'FlyCountInChamber',
    #                          ### Below, add all the columns that are
    #                          ### potentially used for timecourse plotting.
    #                          'AverageFeedVolumePerFly_µl',
    #                          'AverageFeedCountPerFly']]
    #
    # temp_cumsum.loc[:,'AverageFeedVolumePerFly_nl'] = temp_cumsum.loc[:,'AverageFeedVolumePerFly_µl']*1000
    #
    # temp_cumsum.rename( columns={'AverageFeedVolumePerFly_nl':'Cumulative Volume (nl)',
    #                              'AverageFeedCountPerFly':'Cumulative Feed Count',
    #                                      },
    #                          inplace = True)
    #
    # # # Add time column to facilitate plotting.
    # temp_cumsum = __add_time_column(temp_cumsum)

    return grs_cumsum



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

    df_out = df.copy()

    if isinstance(group_by, str):
        df_out['plot_groups'] = df_out[group_by]
        gby = [group_by, ]
    elif isinstance(group_by, list):
        # create new categorical column.
        df_out['plot_groups'] = join_cols(df_out, group_by)
        gby = ['plot_groups',]

    gby.append(compare_by)
    # Create another categorical column.
    df_out['plot_groups_with_contrast'] = join_cols(df_out, gby)

    return df_out


def assign_food_choice(flyid, choiceid, mapper):
    """
    Convenience function used to assign the food choice.
    """

    return mapper.loc[flyid, 'Tube{}'.format(choiceid)]


def get_expt_duration(path_to_feedstats):
    """
    Convenience function that reads in CRITTA's `FeedStats` csv, extracts out
    the last timestamp, and assigns that as the experiment duration.
    """
    import numpy as np
    import pandas as pd

    feedstats = pd.read_csv(path_to_feedstats)
    return np.int(np.round(feedstats.Minutes.values[-1]))


def assign_status_from_genotype(genotype):
    """
    Convenience function to map genotype to status.
    """
    if genotype.lower().includes('w1118'):
        status = 'Sibling'
    else:
        status = 'Offspring'

    return status
