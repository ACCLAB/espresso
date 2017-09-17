#!/usr/bin/python
# -*-coding: utf-8 -*-
# Author: Joses Ho
# Email : joseshowh@gmail.com

import sys
import os

import numpy as _np
import scipy as _sp
import pandas as _pd

 #    # ###### #####   ##   #####    ##   #####   ##
 ##  ## #        #    #  #  #    #  #  #    #    #  #
 # ## # #####    #   #    # #    # #    #   #   #    #
 #    # #        #   ###### #    # ######   #   ######
 #    # #        #   #    # #    # #    #   #   #    #
 #    # ######   #   #    # #####  #    #   #   #    #

def metadata(path_to_csv):
    """
    Munges a metadata CSV from an ESPRESSO experiment.
    Returns a pandas DataFrame.
    """
    ## Read in metadata.
    metadata_csv=_pd.read_csv( path_to_csv )
    ## Check that the metadata has a nonzero number of rows.
    if len(metadata_csv)==0:
        raise ValueError(metadata+' has 0 rows. Please check!!!')

    ## Rename columns.
    metadata_csv.rename(columns={"Food 1":"Tube1",
                                "Food 2":"Tube2",
                                "#Flies":"FlyCountInChamber"},
                        inplace=True)

    ## Try to deal with inconsistencies in how metadata is recorded.
    ## Do keep this section updated whenever new inconsistencies are spotted.
    for c in ['Tube1','Tube2']:
        try:
            metadata_csv.loc[:,c]=metadata_csv[c]\
            .str.replace('5%S','5% sucrose ')\
            .str.replace('5%YE',' 5% yeast extract')
        except AttributeError:
            pass

    # Turn N/A in #Flies to 0.
    metadata_csv.loc[:,'FlyCountInChamber']=metadata_csv.FlyCountInChamber.fillna(value=1).astype(int)

    return metadata_csv

 ###### ###### ###### #####  #       ####   ####
 #      #      #      #    # #      #    # #    #
 #####  #####  #####  #    # #      #    # #
 #      #      #      #    # #      #    # #  ###
 #      #      #      #    # #      #    # #    #
 #      ###### ###### #####  ######  ####   ####

def feedlog(path_to_csv):
    """
    Munges a feedlog CSV from an ESPRESSO experiment.
    Returns a pandas DataFrame.
    """
    ## Read in the CSV.
    feedlog_csv=_pd.read_csv( path_to_csv )

    ## Rename columns.
    feedlog_csv.rename(columns={"Food 1":"Tube1",
                                "Food 2":"Tube2",
                                'Volume-mm3':'FeedVol_µl',
                                'Duration-ms':'FeedDuration_ms',
                                'RelativeTime-s':'RelativeTime_s'},
                        inplace=True)

    ## Check that the feedlog has a nonzero number of rows.
    if len(feedlog_csv)==0:
        raise ValueError(feedlog+' has 0 rows. Please check!!!')

    ## Drop the feed events where `AviFile` is "Null", as well as events that have a negative `RelativeTime-s`.
    feedlog_csv.drop(feedlog_csv[feedlog_csv.AviFile=='Null'].index, inplace=True)
    feedlog_csv.drop(feedlog_csv[feedlog_csv['RelativeTime_s']<0].index, inplace=True)

    ## You have to ADD 1 to match the feedlog FlyID with the corresponding FlyID in `metadata_csv`.
    feedlog_csv.FlyID=feedlog_csv.FlyID+1

    return feedlog_csv

   ##   #####  #####          #####    ##   #####  #####   ####  #    #  ####
  #  #  #    # #    #         #    #  #  #  #    # #    # #    # #    # #
 #    # #    # #    #         #    # #    # #    # #    # #    # #    #  ####
 ###### #    # #    #         #####  ###### #    # #####  #    # # ## #      #
 #    # #    # #    #         #      #    # #    # #   #  #    # ##  ## #    #
 #    # #####  #####          #      #    # #####  #    #  ####  #    #  ####
                      #######

def add_padrows(metadata_df, feedlog_df):
    """
    Define 2 padrows per fly, per food choice. This will ensure that feedlogs
    for each FlyID fully capture the entire 6-hour duration.

    Pass along a munged metadata and corresponding munged feedlog. Returns the modified feedlog.
    """
    f=feedlog_df.copy()
    for flyid in metadata_df.FlyID.unique():
        for choice in f.ChoiceIdx.unique():
            padrows=_pd.DataFrame( [ [_np.nan,_np.nan,choice,
                                     flyid,choice,'NIL',
                                     _np.nan,_np.nan,_np.nan,
                                     False,0.5,'PAD', # 0.5 seconds
                                    ],
                                   [_np.nan,_np.nan,choice,
                                    flyid,choice,'NIL',
                                    _np.nan,_np.nan,_np.nan,
                                    False,21891,'PAD', # 6 hrs, 5 min, 1 sec in seconds.
                                   ] ]
                                )
            padrows.columns=f.columns
        # Add the padrows to feedlog. There is no `inplace` argument for append.
        f=f.append(padrows,ignore_index=True)

    return f

  ####   ####  #    # #####  #    # ##### ######         #    #   ##   #    #  ####  #      # ##### ###### #####           ####   ####  #       ####
 #    # #    # ##  ## #    # #    #   #   #              ##   #  #  #  ##   # #    # #      #   #   #      #    #         #    # #    # #      #
 #      #    # # ## # #    # #    #   #   #####          # #  # #    # # #  # #    # #      #   #   #####  #    #         #      #    # #       ####
 #      #    # #    # #####  #    #   #   #              #  # # ###### #  # # #    # #      #   #   #      #####          #      #    # #           #
 #    # #    # #    # #      #    #   #   #              #   ## #    # #   ## #    # #      #   #   #      #   #          #    # #    # #      #    #
  ####   ####  #    # #       ####    #   ######         #    # #    # #    #  ####  ###### #   #   ###### #    #          ####   ####  ######  ####
                                                 #######                                                          #######

def compute_nanoliter_cols(feedlog_df):
    """
    Computes feed volume and feed speed in nanoliters. Adds these two values as new columns.

    Pass along a munged feedlog. Returns the modified feedlog.
    """
    f=feedlog_df.copy()
    # Compute feed volume in nanoliters for convenience.
    f['FeedVol_nl']=f['FeedVol_µl']*1000
    # Compute feeding speed.
    f['FeedSpeed_nl/s']=f['FeedVol_nl']/(f['FeedDuration_ms']/1000)

    return f

  ####   ####  #    # #####  #    # ##### ######         ##### # #    # ######          ####   ####  #       ####
 #    # #    # ##  ## #    # #    #   #   #                #   # ##  ## #              #    # #    # #      #
 #      #    # # ## # #    # #    #   #   #####            #   # # ## # #####          #      #    # #       ####
 #      #    # #    # #####  #    #   #   #                #   # #    # #              #      #    # #           #
 #    # #    # #    # #      #    #   #   #                #   # #    # #              #    # #    # #      #    #
  ####   ####  #    # #       ####    #   ######           #   # #    # ######          ####   ####  ######  ####
                                                 #######                       #######

def compute_time_cols(feedlog_df):
    """
    Computes RelativeTime_s and FeedDuration_s. Adds these two values as new columns.

    Pass along a munged feedlog. Returns the modified feedlog.
    """
    f=feedlog_df.copy()
    # Duplicate `RelativeTime_s` as non-DateTime object.
    f['FeedTime_s']=f['RelativeTime_s']
    # Convert `RelativeTime_s` to DateTime object.
    f['RelativeTime_s']=_pd.to_datetime(f['RelativeTime_s'],unit='s')
    f['FeedDuration_s']=f.FeedDuration_ms/1000

    return f

 #####  ###### ##### ######  ####  #####         #    #  ####  #    #         ###### ###### ###### #####  # #    #  ####          ###### #      # ######  ####
 #    # #        #   #      #    #   #           ##   # #    # ##   #         #      #      #      #    # # ##   # #    #         #      #      # #      #
 #    # #####    #   #####  #        #           # #  # #    # # #  #         #####  #####  #####  #    # # # #  # #              #####  #      # #####   ####
 #    # #        #   #      #        #           #  # # #    # #  # #         #      #      #      #    # # #  # # #  ###         #      #      # #           #
 #    # #        #   #      #    #   #           #   ## #    # #   ##         #      #      #      #    # # #   ## #    #         #      #      # #      #    #
 #####  ######   #   ######  ####    #           #    #  ####  #    #         #      ###### ###### #####  # #    #  ####          #      ###### # ######  ####
                                         #######                      #######                                             #######

def detect_non_feeding_flies(metadata_df,feedlog_df):
    """
    Detects non-feeding flies.

    Pass along a munged metadata and corresponding munged feedlog. Returns the non-feeding flies as a list.
    """
    non_feeding_flies=[]
    for flyid in metadata_df.FlyID.unique():
        if flyid not in feedlog_df.FlyID.unique():
            non_feeding_flies.append(flyid)
    return non_feeding_flies
