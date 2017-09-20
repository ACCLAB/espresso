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

from _plotter import espresso_plotter as _esp_plotter
from _plotter import plot_helpers as _plot_helpers
import munger as _munger

class espresso(object):
    """
    Creates an `espresso` experiment for analysis.

    Supply either a folder with raw feedlog(s) and corresponding metadata file(s) in CSV format from
    CRITTA, or a pre-processed FeedLog DataFrame and its corresponding MetaData DataFrame.

    Keywords
    --------

    folder: string
        Path to a folder with at least one FeedLog, along with its corresponding MetaData.

    """
    #       #    #       #       #####
    #       ##   #       #         #
    #       # #  #       #         #
    #       #  # #       #         #
    #       #   ##       #         #
    #       #    #       #         #

    def __init__(self,folder):
        allflies=[]
        allfeeds=[]
        allmetadata=[]
        non_feeding_flies=[]

        files=_os.listdir(folder)
        self.feedlogs=[csv for csv in files if csv.endswith('.csv') and csv.startswith('FeedLog')]
        feedlogs_in_folder=_np.array(self.feedlogs)

        # check that each feedlog has a corresponding metadata CSV.
        for feedlog in feedlogs_in_folder:
            expected_metadata=feedlog.replace('FeedLog','MetaData')
            if expected_metadata not in files:
                raise NameError('A MetaData file for '+feedlog+' cannot be found.\n'+\
                                'MetaData files should start with "MetaData_" and '+\
                                'have the same datetime info as the corresponding FeedLog. Please check.')
        # Prepare variables.
        feedlogs_list=list()
        metadata_list=list()
        # fly_counter=0

        for j, feedlog in enumerate(feedlogs_in_folder):
            datetime_exptname='_'.join( feedlog.strip('.csv').split('_')[1:3] )

            ## Read in metadata.
            path_to_metadata=_os.path.join( folder, feedlog.replace('FeedLog','MetaData') )
            metadata_csv=_munge.metadata(path_to_metadata)
            metadata_csv=_munger.metadata(path_to_metadata)
            metadata_csv['FlyID']=datetime_exptname+'_Fly'+metadata_csv.ID.astype(str)

            ## Save the _munged metadata.
            metadata_list.append(metadata_csv)
            ## Save the fly IDs.
            allflies.append( metadata_csv.loc[:,'FlyID'].copy() )

            ## Read in feedlog.
            path_to_feedlog=_os.path.join(folder,feedlog)
            feedlog_csv=_munge.feedlog(path_to_feedlog)
            feedlog_csv.loc[:,'FlyID']=datetime_exptname+'_Fly'+feedlog_csv.FlyID.astype(str)

            ## Detect non-feeding flies, add to the appropriate list.
            non_feeding_flies=non_feeding_flies + _munge.detect_non_feeding_flies(metadata_csv,feedlog_csv)

            ## Define 2 padrows per fly, per food choice (in this case, only one),
            ## that will ensure feedlogs for each FlyID fully capture the entire 6-hour duration.
            feedlog_csv=_munge.add_padrows(metadata_csv, feedlog_csv)

            ## Add columns in nanoliters.
            feedlog_csv=_munge.compute_nanoliter_cols(feedlog_csv)
            ## Add columns for RelativeTime_s and FeedDuration_s.
            feedlog_csv=_munge.compute_time_cols(feedlog_csv)

            ## Save the _munged feedlog.
            feedlogs_list.append(feedlog_csv)


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

        # Reset the indexes.
        for df in [allflies,allfeeds]:
            df.reset_index(drop=True,inplace=True)

        # Sort by FlyID, then by RelativeTime
        allfeeds.sort_values(['FlyID','RelativeTime_s'],inplace=True)
        # Record which flies did not feed.
        allflies['AtLeastOneFeed']=_np.repeat(True,len(allflies))
        non_feeding_flies_idx=allflies[allflies.FlyID.isin(non_feeding_flies)].index
        allflies.loc[non_feeding_flies_idx,'AtLeastOneFeed']=False

        ## Change relevant columns to categorical.
        for catcol in ['Genotype','FoodChoice','Temperature']:
            try:
                allfeeds[catcol]=allfeeds.loc[:,catcol].astype('category',ordered=True)
            except KeyError:
                pass

        # ## Should we set the FlyID as the index for the (combined) metadata?
        # allflies.set_index('FlyID',inplace=True,drop=True)
        allflies.drop('ID',axis=1,inplace=True) # Discard superfluous 'ID' column.

        self.flies=allflies
        self.feeds=allfeeds

        self.flies.original_labels=allflies.columns
        self.feeds.original_labels=allfeeds.columns

        self.feedlog_count=len(feedlogs_in_folder)
        self.genotypes=allflies.Genotype.unique()
        self.temperatures=allflies.Temperature.unique()
        self.foodtypes=_np.unique( allflies.dropna(axis=1).filter(regex='Tube') )

        self.plot=_esp_plotter.espresso_plotter(self) # Passes an instance of `self` to plotter.

 #####  ###### #####  #####
 #    # #      #    # #    #
 #    # #####  #    # #    #
 #####  #      #####  #####
 #   #  #      #      #   #
 #    # ###### #      #    #

    def __repr__(self):

        plural_list=[]
        for value in [self.feedlog_count,len(self.genotypes),
                      len(self.temperatures),len(self.foodtypes)]:
            if value>1:
                plural_list.append('s')
            else:
                plural_list.append('')

        rep_str="{0} feedlog{8} with a total of {1} flies.\n{2} genotype{9} {3}.\n{4} temperature{10} {5}.\n{6} foodtype{11} {7}.".format(
            self.feedlog_count,len(self.flies),
            len(self.genotypes),self.genotypes,
            len(self.temperatures),self.temperatures,
            len(self.foodtypes),self.foodtypes,
            plural_list[0],plural_list[1],plural_list[2],plural_list[3])

        if hasattr(self, "added_labels"):
            if len(self.added_labels)>1:
                plural_label='s have'
            else:
                plural_label=' has'
            rep_str=rep_str+"\n{0} label{1} been added: {2}".format( len(self.added_labels),
                                                                         plural_label,
                                                                         self.added_labels )

        return rep_str

   ##   #####  #####       ##   #    # #####     #####    ##   #####  #####
  #  #  #    # #    #     #  #  ##   # #    #    #    #  #  #  #    # #    #
 #    # #    # #    #    #    # # #  # #    #    #    # #    # #    # #    #
 ###### #    # #    #    ###### #  # # #    #    #####  ###### #    # #    #
 #    # #    # #    #    #    # #   ## #    #    #   #  #    # #    # #    #
 #    # #####  #####     #    # #    # #####     #    # #    # #####  #####

    def __add__(self, other):
        from copy import copy as _deepcopy
        self_copy=_deepcopy(self) # Create a copy of the first espresso object to be summed.
        other_copy=_deepcopy(other) # Create a copy of the other espresso object.

        ##### EXTRACT ADDED LABELS FOR EACH OBJECT IF THEY EXIST.
        ##### IF NOT ASSIGN EMPTY LIST TO DROP.

        # Merge the flies and feeds attributes.
        self_copy.flies=_pd.merge(self_copy.flies, other_copy.flies, how='outer')
        self_copy.feeds=_pd.merge(self_copy.feeds, other_copy.feeds, how='outer')
        # carry over the original_labels attrib.
        self_copy.flies.original_labels=self.flies.original_labels
        self_copy.feeds.original_labels=self.feeds.original_labels

        new_labels=[]
        for o in [self_copy,other_copy]:
            if hasattr(o, "added_labels"):
                if isinstance(o.added_labels, list):
                    new_labels=new_labels+o.added_labels
                elif isinstance(o.added_labels, str):
                    new_labels.append(o.added_labels)
        new_labels=list( set(new_labels) )
        if len(new_labels)>0:
            self_copy.added_labels=new_labels

        self_copy.feedlogs=list( set(self_copy.feedlogs+other_copy.feedlogs) )
        self_copy.feedlog_count=len(self_copy.feedlogs)

        self_copy.genotypes=self_copy.flies.Genotype.unique()
        self_copy.temperatures=self_copy.flies.Temperature.unique()

        self_copy.foodtypes=_np.unique( self_copy.flies.dropna(axis=1).filter(regex='Tube') )
        self_copy.plot=_esp_plotter.espresso_plotter(self_copy)

        return self_copy

    def __radd__(self, other):
        if other==0:
            return self
        else:
            return self.__add__(other)

   ##   #####  #####           #        ##   #####  ###### #       ####
  #  #  #    # #    #          #       #  #  #    # #      #      #
 #    # #    # #    #          #      #    # #####  #####  #       ####
 ###### #    # #    #          #      ###### #    # #      #           #
 #    # #    # #    #          #      #    # #    # #      #      #    #
 #    # #####  #####           ###### #    # #####  ###### ######  ####

    def add_label(self, label_name,
                    label_value=None,
                    label_from_cols=None,
                    sep=','):
        """
        Add a custom label to the metadata and feedlog of an espresso experiment.
        The espresso object is modified in place.

        Keywords
        --------

        label_name: string
            The new category name.

        label_value: default None
            Assigns a custom value to the label for all flies in the espresso experiment.
            You can assign any type of Python object. The label will be converted
            into a pandas Categorical variable.

        label_from_cols: list, default None
            Assigns a value to all flies in this espresso experiment by concatenating
            existing metadata columns of the espresso object. The list order is the
            concatenation order.

        sep: string, default ','
            The seperator used to denote the joined columns if `label_from_cols` is passed.
        """

        # Sanity check for keywords passed.
        label_name=str(label_name)

        if label_value is None and label_from_cols is None:
            raise ValueError("Please specify either `label_value` or `label_from_cols`.")
        if label_value is not None and label_from_cols is not None:
            raise ValueError("You have specified both `label_value` or `label_from_cols`. Please only specify one.")
        if label_from_cols is not None and isinstance(label_from_cols, list) is False:
            raise TypeError("`label_from_cols` is not a list. Please check again.")

        if label_value is not None:
            for obj in [self.flies, self.feeds]:
                obj[label_name]=_np.repeat(str(label_value), len(obj))
                # turn into Categorical.
                obj.loc[:,label_name]=obj[label_name].astype('category',ordered=True)

        else:
            for col in label_from_cols:
                col=str(col)
                if col not in self.flies.columns:
                    raise KeyError( "{0} is not found in the metadata. Please check.".format(col) )
            for obj in [self.flies, self.feeds]:
                # See https://stackoverflow.com/questions/33098383/merge-multiple-column-values-into-one-column-in-python-pandas
                obj[label_name]=obj[label_from_cols].apply(lambda x: sep.join(x.dropna().astype(str)),axis=1)
                # turn into Categorical.
                obj.loc[:,label_name]=obj[label_name].astype('category',ordered=True)

        labels=[label_name] # convert to single-member list.
        if hasattr(self, 'added_labels'):
            self.added_labels.extend(labels)
        else:
            self.added_labels=labels

        if label_value is not None:
            print("{0} has been added as a new label, with '{1}' as the custom value.".format(label_name, label_value))
        else:
            print("{0} has been added as a new label. The values were created by concatenating the columns {1}.".format(label_name, label_from_cols))

 #####  ###### #    #  ####  #    # ######       #        ##   #####  ###### #       ####
 #    # #      ##  ## #    # #    # #            #       #  #  #    # #      #      #
 #    # #####  # ## # #    # #    # #####        #      #    # #####  #####  #       ####
 #####  #      #    # #    # #    # #            #      ###### #    # #      #           #
 #   #  #      #    # #    #  #  #  #            #      #    # #    # #      #      #    #
 #    # ###### #    #  ####    ##   ######       ###### #    # #####  ###### ######  ####

    def remove_labels(self, labels):
        """
        Removes the label(s) from the `flies` and `feeds` DataFrames of an espresso experiment.
        The espresso experiment is modified in place.

        Keywords
        --------

        labels: string or list.
            A single label to remove, or a list of labels to remove.
        """
        # Sanity checks.
        if 'added_labels' not in self.__dict__:
            raise KeyError('This espresso experimenthas no added labels.')

        # Handle labels depending if string or list.
        if isinstance(labels, str):
            labels=[labels] # convert to single-member list.

        if isinstance(labels,list):
            in_added=[str(l) for l in labels if l in self.added_labels]

            if len(in_added)==0:
                raise KeyError("Not all labels in {0} is not an added label. Please check.".format(labels))

        self.flies.drop(labels,axis=1,inplace=True)
        self.feeds.drop(labels,axis=1,inplace=True)

        # check if we need to remove the added_labels attribute.
        if labels==self.added_labels:
            del self.__dict__['added_labels']
        else:
            for l in labels:
                self.added_labels.remove(l)

        return "{0} has been dropped.".format(labels)


    def remove_all_labels(self):
        """
        Removes add added label(s) from the `flies` and `feeds` DataFrames of an espresso experiment.
        The espresso experiment is modified in place.
        """
        # Sanity checks.
        if 'added_labels' not in self.__dict__:
            raise KeyError('This espresso experiment has no added labels.')

        dropped=self.added_labels

        for attr in [self.flies, self.feeds]:
            attr.drop(dropped,axis=1,inplace=True)

        del self.__dict__['added_labels']

        return "All added labels {0} have been dropped.".format(dropped)
