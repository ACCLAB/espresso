#!/usr/bin/python
# -*-coding: utf-8 -*-
# Author: Joses Ho
# Email : joseshowh@gmail.com

"""
Package for analysis of ESPRESSO experiments run on CRITTA.
"""

import sys as _sys
import os as _os

import numpy as _np
import scipy as _sp
import pandas as _pd

import seaborn as _sns
import bootstrap_contrast as _bsc

import munge

class espresso(object):
    """
    Creates an `espresso` object for analysis.

    Supply either a folder with raw feedlog(s) and corresponding metadata file(s) in CSV format from CRITTA,
    or a pre-processed feedlog DataFrame and its corresponding metadata DataFrame.
    """
    import plot

    def __init__(self,folder=None,flies_df=None,feeds_df=None):
        if folder is None:
            if flies_df is not None and feeds_df is not None:
                self.flies=flies_df
                self.feeds=feeds_df
                self.feedlog_count=1
                self.genotypes=flies_df.Genotype.unique()
                self.temperatures=flies_df.Temperature.unique()
                self.foodtypes=_np.unique( flies_df.dropna(axis=1).filter(regex='Tube') )

            else:
                raise ValueError('Please check the arguments you passed.')

        else:
            allflies=[]
            allfeeds=[]
            allmetadata=[]
            non_feeding_flies=[]

            files=_os.listdir(folder)
            feedlogs=_np.sort( [csv for csv in files if csv.endswith('.csv') and csv.startswith('FeedLog')] )

            # check that each feedlog has a corresponding metadata CSV.
            for feedlog in feedlogs:
                expected_metadata=feedlog.replace('FeedLog','MetaData')
                if expected_metadata not in files:
                    raise NameError('A MetaData file for '+feedlog+' cannot be found.\n'+\
                                    'MetaData files should start with "MetaData_" and '+\
                                    'have the same datetime info as the corresponding FeedLog. Please check.')
            # Prepare variables.
            feedlogs_list=list()
            metadata_list=list()
            fly_counter=0

            for j, feedlog in enumerate(feedlogs):

                ## Read in metadata.
                path_to_metadata=_os.path.join( folder, feedlog.replace('FeedLog','MetaData') )
                metadata_csv=munge.metadata(path_to_metadata)
                ## Track the flycount.
                if j>0:
                    metadata_csv.ID=metadata_csv.ID+fly_counter
                metadata_csv['FlyID']='Fly'+metadata_csv.ID.astype(str)
                ## Add current fly count to fly_counter.
                fly_counter+=len(metadata_csv)

                ## Save the munged metadata.
                metadata_list.append(metadata_csv)
                ## Save the fly IDs.
                allflies.append( metadata_csv.loc[:,'FlyID'].copy() )

                ## Read in feedlog.
                path_to_feedlog=_os.path.join(folder,feedlog)
                feedlog_csv=munge.feedlog(path_to_feedlog)

                ## Increment each FlyID by the total number of flies in previous feedlogs.
                if j>0:
                    feedlog_csv.FlyID=feedlog_csv.FlyID+fly_counter
                feedlog_csv.loc[:,'FlyID']='Fly'+feedlog_csv.FlyID.astype(str)

                ## Define 2 padrows per fly, per food choice (in this case, only one),
                ## that will ensure feedlogs for each FlyID fully capture the entire 6-hour duration.
                feedlog_csv=munge.add_padrows(metadata_csv, feedlog_csv)

                ## Add columns in nanoliters.
                feedlog_csv=munge.compute_nanoliter_cols(feedlog_csv)
                ## Add columns for RelativeTime_s and FeedDuration_s.
                feedlog_csv=munge.compute_nanoliter_cols(feedlog_csv)

                ## Save the munged feedlog.
                feedlogs_list.append(feedlog_csv)

                ## Detect non-feeding flies, add to the appropriate list.
                non_feeding_flies.extend( munge.detect_non_feeding_flies(metadata_csv,feedlog_csv) )


            # Join all processed feedlogs and metadata into respective DataFrames.
            allflies=_pd.concat(metadata_list).reset_index(drop=True)
            allfeeds=_pd.concat(feedlogs_list).reset_index(drop=True)
            # merge metadata with feedlogs.
            allfeeds=_pd.merge(allfeeds,allflies,left_on='FlyID',right_on='FlyID')

            # rename columns and food types as is appropriate.
            for df in [allflies,allfeeds]:
                df.loc[:,'Genotype']=df.Genotype.str.replace('W','w')

            # Discard superfluous columns.
            allfeeds.drop('ID',axis=1,inplace=True)

            # Assign feed choice to the allfeeds DataFrame.
            choice1=allfeeds['Tube1'].unique()
            choice2=allfeeds['Tube2'].unique()

            if len(choice1)>1 or len(choice2)>1:
                raise ValueError('More than one food choice detected per food column. Please check the file '+metadata)
            else:
                choice1=choice1[0]
                choice2=choice2[0]
                try:
                    there_is_no_second_tube=_np.isnan(choice2)
                    if there_is_no_second_tube:
                        ## Drop anomalous feed events from Tube2 (aka ChoiceIdx=1),
                        ## where there was no feed tube in the first place.
                        allfeeds.drop(allfeeds[allfeeds.ChoiceIdx==1].index,inplace=True)
                except TypeError:
                    allfeeds['FoodChoice']=_np.repeat('xx',len(allfeeds))
                    allfeeds.loc[_np.where(allfeeds.ChoiceIdx==0)[0],'FoodChoice']=choice1
                    allfeeds.loc[_np.where(allfeeds.ChoiceIdx==1)[0],'FoodChoice']=choice2
                    ## Add column to identify which FeedLog file the feed data came from.
                    allfeeds['FeedLog_rawfile']=_np.repeat(feedlog, len(allfeeds))
                    ## Turn the 'Valid' column into integers.
                    ## 1 -- True; 0 -- False
                    allfeeds['Valid']=allfeeds.Valid.astype('int')

            allfeeds.reset_index(drop=True,inplace=True)

            # Sort by FlyID, then by RelativeTime
            allfeeds.sort_values(['FlyID','RelativeTime_s'],inplace=True)

            # Reset the indexes.
            for df in [allflies,allfeeds]:
                df.reset_index(drop=True,inplace=True)

            # Record which flies did not feed.
            allflies['fed_during_assay']=_np.repeat(True,len(allflies))
            allflies.set_index('FlyID',inplace=True,drop=True)
            allflies.loc[non_feeding_flies,'fed_during_assay']=False

            self.flies=allflies
            self.feeds=allfeeds
            self.feedlog_count=len(feedlogs)
            self.genotypes=allflies.Genotype.unique()
            self.temperatures=allflies.Temperature.unique()
            self.foodtypes=_np.unique( allflies.dropna(axis=1).filter(regex='Tube') )

    def __repr__(self):
        return '{0} feedlog(s) with a total of {1} flies.\n{2} genotype(s) detected {3}.\n{4} temperature(s) detected {5}.\n{6} foodtype(s) detected {7}.'.format( self.feedlog_count,len(self.flies),
                                                    len(self.genotypes),self.genotypes,
                                                    len(self.temperatures),self.temperatures,
                                                    len(self.foodtypes),self.foodtypes )

    def __add__(self, other):
        newflies=_pd.concat([self.flies,other.flies])
        newfeeds=_pd.concat([self.feeds,other.feeds])

        return espresso(flies_df=newflies,feeds_df=newfeeds)

    def __radd__(self, other):
        if other==0:
            return self
        else:
            return self.__add__(other)
