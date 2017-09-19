#!/usr/bin/python
# -*-coding: utf-8 -*-
# Author: Joses Ho
# Email : joseshowh@gmail.com

"""
Plot functions for espresso objects.
"""


 #      # #####  #####    ##   #####  #   #    # #    # #####   ####  #####  #####
 #      # #    # #    #  #  #  #    #  # #     # ##  ## #    # #    # #    #   #
 #      # #####  #    # #    # #    #   #      # # ## # #    # #    # #    #   #
 #      # #    # #####  ###### #####    #      # #    # #####  #    # #####    #
 #      # #    # #   #  #    # #   #    #      # #    # #      #    # #   #    #
 ###### # #####  #    # #    # #    #   #      # #    # #       ####  #    #   #


import sys as _sys
import os as _os

import numpy as _np
import scipy as _sp
import pandas as _pd

import matplotlib as _mpl
import matplotlib.pyplot as _plt
import matplotlib.ticker as _tk

import seaborn as _sns
import bootstrap_contrast as _bsc

from . import plot_helpers as _pth
from . import contrast as _con

class espresso_plotter:
    """
    Plotting class for espresso object.
    """


 #    #    #    #    #####
 #    ##   #    #      #
 #    # #  #    #      #
 #    #  # #    #      #
 #    #   ##    #      #
 #    #    #    #      #

    def __init__(self,espresso): # pass along an espresso instance.
        self._experiment=espresso # so contrast method can access it.
        self.contrast=_con.contrast_plotter(self)


 #####    ##    ####  ##### ###### #####     #####  #       ####  #####  ####
 #    #  #  #  #        #   #      #    #    #    # #      #    #   #   #
 #    # #    #  ####    #   #####  #    #    #    # #      #    #   #    ####
 #####  ######      #   #   #      #####     #####  #      #    #   #        #
 #   #  #    # #    #   #   #      #   #     #      #      #    #   #   #    #
 #    # #    #  ####    #   ###### #    #    #      ######  ####    #    ####


    def rasters(self,group_by,resample='10min',add_flyid_labels=True,palette_type='categorical'):
        # make a copy of the metadata and the feedlog.
        allfeeds=self._experiment.feeds.copy()
        allflies=self._experiment.flies.copy()

        # Select palette.
        if palette_type=='categorical':
            color_palette=_pth._make_categorial_palette(allfeeds,group_by)
        elif palette_type=='sequential':
            color_palette=_pth._make_sequential_palette(allfeeds,group_by)

        grps=allfeeds[group_by].unique()
        pal=dict( zip(grps, color_palette) )

        # Duplicate `RelativeTime_s` as non-DateTime object.
        allfeeds['feed_time_s']=allfeeds.loc[:,'RelativeTime_s']

        # Convert `RelativeTime_s` to DateTime object.
        allfeeds.loc[:,'RelativeTime_s']=_pd.to_datetime(allfeeds['RelativeTime_s'], unit='s')

        # munging for bygroup data.
        allfeeds_bygroup=_pd.DataFrame( allfeeds.groupby(group_by).\
                                          resample('10min',on='RelativeTime_s').\
                                          sum().to_records() )
        allfeeds_bygroup_fv=allfeeds_bygroup.loc[:,[group_by,'RelativeTime_s','FeedVol_µl']]
        allfeeds_bygroup_fv.fillna(0,inplace=True)
        allfeeds_bygroup_fv['feed_time_s']=allfeeds_bygroup_fv.RelativeTime_s.dt.hour*3600+\
                                              allfeeds_bygroup_fv.RelativeTime_s.dt.minute*60+\
                                              allfeeds_bygroup_fv.RelativeTime_s.dt.second

        maxflycount=allflies.groupby(group_by).count().FlyID.max()

        _sns.set(style='ticks',context='poster')
        if add_flyid_labels:
            ws=0.4
        else:
            ws=0.2

        fig,axx=_plt.subplots(nrows=2,
                             ncols=int( len(grps) ),
                             figsize=(32,15),
                             gridspec_kw={'wspace':ws,
                                          'hspace':0.2,
                                          'height_ratios':(3,2)} )

        for c, grp in enumerate( grps ):

            print('plotting {0} {1}'.format(grp,'rasters'))
            # Plot the raster plots.
            rasterax=axx[0,c]
            rasterax.xaxis.grid(True,linestyle='dotted',which='major',alpha=1)
            rasterax.xaxis.grid(True,linestyle='dotted',which='minor',alpha=0.5)

            # Grab only the flies we need.
            tempfeeds=allfeeds[allfeeds[group_by]==grp]
            temp_allflies=tempfeeds.FlyID.unique().tolist()

            # Grab the columns we need.
            tempfeeds=tempfeeds[['FlyID',group_by,'feed_time_s','FeedDuration_s']]

            # Order the flies properly.
            ## First, drop non-valid feeds, then sort by feed time and feed duration,
            ## then pull out FlyIDs in that order.
            temp_feeding_flies=tempfeeds[~_np.isnan(tempfeeds['FeedDuration_s'])].\
                                    sort_values(['feed_time_s','FeedDuration_s']).FlyID.\
                                    drop_duplicates().tolist()
            ## Next, identify which flies did not feed (aka not in list above.)
            temp_non_feeding_flies=[fly for fly in temp_allflies if fly not in temp_feeding_flies]
            ## Now, join these two lists.
            flies_in_order=temp_feeding_flies+temp_non_feeding_flies

            flycount=int(len(flies_in_order))
            for k, flyid in enumerate(flies_in_order):
                tt=tempfeeds[tempfeeds.FlyID==flyid]
                for idx in [idx for idx in tt.index if ~_np.isnan(tt.loc[idx,'FeedDuration_s'])]:
                    rasterax.axvspan(xmin=tt.loc[idx,'feed_time_s'],
                                     xmax=tt.loc[idx,'feed_time_s']+tt.loc[idx,'FeedDuration_s'],
                                     ymin=(1/maxflycount)*(maxflycount-k-1),
                                     ymax=(1/maxflycount)*(maxflycount-k),
                                     color='k',
                                     alpha=1)
                if add_flyid_labels:
                    if flyid in temp_non_feeding_flies:
                        label_color='grey'
                    else:
                        label_color='black'
                    rasterax.text(-85, (1/maxflycount)*(maxflycount-k-1) + (1/maxflycount)*.5,
                                flyid,
                                color=label_color,
                                verticalalignment='center',
                                horizontalalignment='right',
                                fontsize=8)
            rasterax.yaxis.set_visible(False)
            rasterax.set_title(grp)

            # Plot the feed volume plots.
            print('plotting {0}'.format(grp))
            bygroupax=axx[1,c]
            temp_df=allfeeds_bygroup_fv[allfeeds_bygroup_fv[group_by]==grp]
            bygroupax.fill_between(x=temp_df['feed_time_s'],
                                   y1=temp_df['FeedVol_µl'],
                                   y2=_np.repeat(0,len(temp_df)),
                                   color=pal[grp],
                                   lw=1)
            bygroupax.set_ylim(0,allfeeds_bygroup_fv['FeedVol_µl'].max())
            if c==0:
                bygroupax.set_ylabel('Total Consumption (µl)\n10 min bins')

            # Format x-axis for both axes.
            for a in [rasterax, bygroupax]:
                a.set_xlim(0,21600)
                a.xaxis.set_ticks(range(0,25200,3600))
                a.xaxis.set_minor_locator( _tk.MultipleLocator(base=1800) )
                a.set_xlabel('Time (h)',fontsize=17)
                newlabels=[str(int(t/3600)) for t in a.xaxis.get_ticklocs(minor=False)]
                a.set_xticklabels(newlabels)
                a.tick_params(axis='x', which='major',length=10)
                a.tick_params(axis='x', which='minor',length=6)

            _sns.despine(ax=rasterax,left=True,trim=True)
            _sns.despine(ax=bygroupax,trim=True,offset={'left':7,'bottom':5})

        return fig


 #####  ###### #####   ####  ###### #    # #####    ###### ###### ###### #####  # #    #  ####
 #    # #      #    # #    # #      ##   #   #      #      #      #      #    # # ##   # #    #
 #    # #####  #    # #      #####  # #  #   #      #####  #####  #####  #    # # # #  # #
 #####  #      #####  #      #      #  # #   #      #      #      #      #    # # #  # # #  ###
 #      #      #   #  #    # #      #   ##   #      #      #      #      #    # # #   ## #    #
 #      ###### #    #  ####  ###### #    #   #      #      ###### ###### #####  # #    #  ####

    def percent_feeding(self,group_by,
                        time_start=0,time_end=360,
                        palette_type='categorical'):
        """
        Produces a lineplot depicting the percent of flies feeding for each condition.
        A 95% confidence interval for each proportion of flies feeding is also given.

        Keywords
        --------
        group_by: string, categorical
            The column or label indicating the categorical grouping on the x-axis.

        time_start, time_end: integer, default 0 and 360 respectively
            The time window (in minutes) during which to compute and display the
            percent flies feeding.

        palette_type: string, 'categorical' or 'sequential'.

        Returns
        -------

        A matplotlib Axes instance, and a pandas DataFrame with the statistics.
        """
        # Get plotting variables.
        percent_feeding_summary=_pth.compute_percent_feeding(self._experiment.flies,
                                                             self._experiment.feeds,
                                                             group_by,
                                                             start=time_start,
                                                             end=time_end)


        cilow=percent_feeding_summary.ci_lower.tolist()
        cihigh=percent_feeding_summary.ci_upper.tolist()
        ydata=percent_feeding_summary.percent_feeding.tolist()

        # Select palette.
        if palette_type=='categorical':
            color_palette=_pth._make_categorial_palette(self._experiment.feeds,group_by)
        elif palette_type=='sequential':
            color_palette=_pth._make_sequential_palette(self._experiment.feeds,group_by)

        # Set style.
        _sns.set(style='ticks',context='talk',font_scale=1.1)

        # Initialise figure.
        f,ax=_plt.subplots(1,figsize=(8,5))
        ax.set_ylim(0,110)
        # Plot 95CI first.
        ax.fill_between(range(0,len(percent_feeding_summary)),
                        cilow,cihigh,
                        alpha=0.25,
                        color='grey' )
        # Then plot the line.
        percent_feeding_summary.percent_feeding.plot.line(ax=ax,color='k',lw=1.2)

        for j,s in enumerate(ydata):
            ax.plot(j, s, 'o',
                    color=color_palette[j])

        # Aesthetic tweaks.
        ax.xaxis.set_ticks( [i for i in range( 0,len(percent_feeding_summary) )] )
        ax.xaxis.set_ticklabels( percent_feeding_summary.index.tolist() )

        xmax=ax.xaxis.get_ticklocs()[-1]
        ax.set_xlim(-0.2, xmax+0.2) # Add x-padding.
        _bsc.rotate_ticks(ax, angle=45, alignment='right')
        _sns.despine(ax=ax,trim=True,offset={'left':1})
        ax.set_ylabel('Percent Feeding')

        f.tight_layout()
        return f, percent_feeding_summary
