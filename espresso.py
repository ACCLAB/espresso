#!/usr/bin/python
# -*-coding: utf-8 -*-
# Author: Joses Ho
# Email : joseshowh@gmail.com

import sys as _sys
import os as _os

import numpy as _np
import scipy as _sp
import pandas as _pd

import munge

######  ####  #####  #####  ######  ####   ####   ####      ####  #####       # ######  ####  #####
#      #      #    # #    # #      #      #      #    #    #    # #    #      # #      #    #   #
#####   ####  #    # #    # #####   ####   ####  #    #    #    # #####       # #####  #        #
#           # #####  #####  #           #      # #    #    #    # #    #      # #      #        #
#      #    # #      #   #  #      #    # #    # #    #    #    # #    # #    # #      #    #   #
######  ####  #      #    # ######  ####   ####   ####      ####  #####   ####  ######  ####    #

class espresso(object):
    """
    Creates an `espresso` object for analysis.

    Supply either a folder with raw feedlog(s) and corresponding metadata file(s) in CSV format from CRITTA,
    or a pre-processed feedlog DataFrame and its corresponding metadata DataFrame.
    """
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
                        feeds_to_drop_count=len(allfeeds[allfeeds.ChoiceIdx==1])
                except TypeError:
                    allfeeds['FoodChoice']=_np.repeat('xx',len(allfeeds))
                    allfeeds.loc[_np.where(allfeeds.ChoiceIdx==0)[0],'FoodChoice']=choice1
                    allfeeds.loc[_np.where(allfeeds.ChoiceIdx==1)[0],'FoodChoice']=choice2
                    ## Add column to identify which FeedLog file the feed data came from.
                    allfeeds['FeedLog_rawfile']=_np.repeat(feedlog, len(allfeeds))
                    ## Turn the 'Valid' column into integers.
                    ## 1 -- True; 0 -- False
                    allfeeds['Valid']=allfeeds.Valid.astype('int')

            allfeeds.drop(allfeeds[allfeeds.ChoiceIdx==1].index,inplace=True)
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



#####  #       ####  #####    ###### #    # #    #  ####  ##### #  ####  #    #  ####
#    # #      #    #   #      #      #    # ##   # #    #   #   # #    # ##   # #
#    # #      #    #   #      #####  #    # # #  # #        #   # #    # # #  #  ####
#####  #      #    #   #      #      #    # #  # # #        #   # #    # #  # #      #
#      #      #    #   #      #      #    # #   ## #    #   #   # #    # #   ## #    #
#      ######  ####    #      #       ####  #    #  ####    #   #  ####  #    #  ####




#####  #       ####  #####    #    # ###### #      #####  ###### #####   ####
#    # #      #    #   #      #    # #      #      #    # #      #    # #
#    # #      #    #   #      ###### #####  #      #    # #####  #    #  ####
#####  #      #    #   #      #    # #      #      #####  #      #####       #
#      #      #    #   #      #    # #      #      #      #      #   #  #    #
#      ######  ####    #      #    # ###### ###### #      ###### #    #  ####

def normalize_ylims(ax_arr,include_zero=False,draw_zero_line=False):
    """Custom function to normalize ylims for an array of axes."""
    ymins=list()
    ymaxs=list()
    for ax in ax_arr:
        ymin=ax.get_ylim()[0]
        ymax=ax.get_ylim()[1]
        ymins.append(ymin)
        ymaxs.append(ymax)
    new_min=_np.min(ymins)
    new_max=_np.max(ymaxs)
    if include_zero:
        if new_max<0:
            new_max=0
        if new_min>0:
            new_min=0
    for ax in ax_arr:
        ax.set_ylim(new_min,new_max)
    if draw_zero_line:
        for ax in ax_arr:
            ax.axhline(y=0,linestyle='solid',linewidth=0.5,color='k')

def meanci(mean, cilow, cihigh, idx, ax, alpha=0.8, marker= 'o',color='black', size=8, ls='solid',lw=1.2):
    """Custom function to normalize plot the mean and CI as a dot and a vertical line, respectively."""
    # Plot the summary measure.
    ax.plot(idx, mean,
             marker=marker,
             markerfacecolor=color,
             markersize=size,
             alpha=alpha
            )
    # Plot the CI.
    ax.plot([idx, idx],
             [cilow, cihigh],
             color=color,
             alpha=alpha,
             linestyle=ls,
            linewidth=lw
            )

# Define function for string formatting of scientific notation.
def sci_nota(num, decimal_digits=2, precision=None, exponent=None):
    """
    Returns a string representation of the scientific
    notation of the given number formatted for use with
    LaTeX or Mathtext, with specified number of significant
    decimal digits and precision (number of decimal digits
    to show). The exponent to be used can also be specified
    explicitly.

    Found on https://stackoverflow.com/questions/21226868/superscript-in-python-plots
    """
    if not exponent:
        exponent = int(_np.floor(_np.log10(abs(num))))
    coeff = round(num / float(10**exponent), decimal_digits)
    if not precision:
        precision = decimal_digits

    return r"${0:.{2}f}\times10^{{{1:d}}}$".format(coeff, exponent, precision)

def compute_percent_feeding(metadata,feeds,group_by,start=0,end=30):
    """
    Used to compute the percent of flies feeding from
    a processed dataset of feedlogs.
    """
    fly_counts=metadata.groupby(group_by).count().FlyID
    data_timewin=feeds[(feeds.RelativeTime_s>_pd.to_datetime(start*60, unit='s')) &
                            (feeds.RelativeTime_s<_pd.to_datetime(end*60, unit='s'))
                            ]
    # To count total flies that fed, I adapted the methods here:
    # https://stackoverflow.com/questions/8364674/python-numpy-how-to-count-the-number-of-true-elements-in-a-bool-array
    feed_boolean_by_fly=~_np.isnan( data_timewin.groupby([group_by,'FlyID']).sum()['FeedVol_µl'] )
    fly_feed_counts=feed_boolean_by_fly.apply(_np.count_nonzero).groupby(group_by).sum()
    # Proportion code taken from here:
    # https://onlinecourses.science.psu.edu/stat100/node/56
    percent_feeding=(fly_feed_counts/fly_counts)*100
    half95ci=_np.sqrt( (percent_feeding*(100-percent_feeding))/fly_counts )
    percent_feeding_summary=_pd.DataFrame([percent_feeding,
                                          percent_feeding-half95ci,
                                          percent_feeding+half95ci]).T
    percent_feeding_summary.columns=['percent_feeding','ci_lower','ci_upper']
    return( percent_feeding_summary )

def latency_ingestion_plots(feeds,first_x_min=180):
    """
    Convenience function to enable ipython interact to modify contrast plots
    for the latency to feed, and total volume ingested, in the `first_x_min`.
    """
    allfeeds_timewin=feeds[feeds.feed_time_s<first_x_min*60]

    latency=_pd.DataFrame(allfeeds_timewin[['FlyID','starved_time',
                                           'feed_time_s','feed_duration_s']].\
                         dropna().\
                         groupby(['starved_time','FlyID']).\
                         apply(_np.min).drop(['starved_time','FlyID','feed_duration_s'],axis=1).\
                         to_records())
    latency['feed_time_min']=latency['feed_time_s']/60
    latency.rename(columns={"feed_time_min": "Latency to\nfirst feed (min)"}, inplace=True)
    max_latency=_np.round(latency.max()["Latency to\nfirst feed (min)"],decimals=-2)

    total_ingestion=_pd.DataFrame(allfeeds_timewin[['FlyID','starved_time','FeedVol_nl']].\
                                 dropna().\
                                 groupby(['starved_time','FlyID']).\
                                 sum().to_records())
    total_ingestion.rename(columns={"FeedVol_nl": "Total Ingestion (nl)"}, inplace=True)
    max_ingestion=_np.round(total_ingestion.max()["Total Ingestion (nl)"],decimals=-2)

    f1,b1=bs.contrastplot(data=latency,x='starved_time',y="Latency to\nfirst feed (min)",
                          swarm_ylim=(-20,max_latency),
                          **bs_kwargs)
    f1.suptitle('Latency to feed in first {0} min'.format(first_x_min),fontsize=20)
    plt.show()
    print(b1)

    f2,b2=bs.contrastplot(data=total_ingestion,
                          x='starved_time',y='Total Ingestion (nl)',
                          swarm_ylim=(-20,max_ingestion),
                          **bs_kwargs)
    f2.suptitle('Total Volume (nl) ingested in first {0} min'.format(first_x_min),fontsize=20)
    plt.show()
    print(b2)
