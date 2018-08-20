def __cumulative_plotter(self, yvar, row, col, min_time, max_time,
                           color_by, resample_by='5min',
                           gridlines=True):

      # import numpy as np
      # import pandas as pd

      import matplotlib.pyplot as plt
      import seaborn as sns
      from . import plot_helpers as plothelp
      from .._munger import munger as munge

      # Handle the group_by and color_by keywords.
      munge.check_group_by_color_by(col, row, color_by, self.__feeds)

      # Resample (aka bin by time).
      resamp_feeds = munge.groupby_resamp_sum(self.__feeds, resample_by)

      # Perform cumulative summation.
      plotdf = munge.cumsum_for_cumulative(resamp_feeds)

      # Initialise figure.
      sns.set(style='ticks')

      g = sns.FacetGrid(b, row="Status", col="Temperature",
                        hue="FoodChoice", legend_out=True,
                        palette='tab10',
                        sharex=False, sharey=True,
                        height=5, aspect=1.5,
                        gridspec_kws={'hspace':0.5, 'wspace':0.1})

      g.map(sns.lineplot, "time_s", "Cumulative Feed Count")

      for ax in g.axes.flat:
          ax.tick_params(labelsize=15)
          plothelp.format_timecourse_xaxis(ax, min_time, max_time)
          if gridlines:
              ax.xaxis.grid(True, which='major',
                            linestyle='dotted', #linewidth=1,
                            alpha=0.5)

      sns.despine(fig=g.fig, trim=True)

      # Change relevant columns to categorical.
      try:
          plotdf.loc[:, 'Status'] = pd.Categorical(plotdf.loc[:, 'Status'],
                                              categories=['Sibling', 'Offspring'],
                                              ordered=True)
      except KeyError:
          pass

      # Change relevant columns to categorical.
      for column in ['Genotype','Temperature',
                     'Sex','FoodChoice']:
          try:
              cats = np.sort(plotdf[column].unique())
              plotdf.loc[:, column] = pd.Categorical(plotdf[column],
                                                     categories=cats,
                                                     ordered=True)
          except KeyError:
              pass

      if row is not None:
          row_count = int(len(plotdf[row].cat.categories))
      else:
          row_count = 1
      if col is not None:
          col_count = int(len(plotdf[col].cat.categories))
      else:
          col_count = 1

      # Compute means
      group_by_cols = [a for a in [col, row, color_by,'time_s']
                      if a is not None]
      plotdf_groupby = plotdf.groupby(group_by_cols)
      plotdf_mean = plotdf_groupby.mean().unstack()[yvar].T

      # Compute CIs
      plotdf_halfci = plotdf_groupby.sem().unstack()[yvar].T * 1.96
      lower_ci = plotdf_mean - plotdf_halfci
      upper_ci = plotdf_mean + plotdf_halfci
      # Make sure no CI drops below zero.
      lower_ci[lower_ci < 0] = 0

      groupby_grps = plotdf[group_by].cat.categories.tolist()
      num_plots = int(len(groupby_grps))

      # Initialise figure.
      sns.set(style='ticks', context='poster', font_scale=1.25)
      if fig_size is None:
          x_inches = 10 * col_count
          y_inches = 7 * row_count
      else:
          if isinstance(fig_size, tuple) or isinstance(fig_size, list):
              x_inches = fig_size[0]
              y_inches = fig_size[1]
          else:
              raise TypeError('Please make sure figsize is a tuple of the '
              'form (w,h) in inches.')

      if ax is None:
          fig, axx = plt.subplots(nrows=row_count, ncols=col_count,
                                  figsize=(x_inches, y_inches),
                                  gridspec_kw={'wspace':0.3,
                                               'hspace':0.3})
      else:
          axx = ax

      if row is not None and col is not None:
           for r, row_ in enumerate(plotdf[row].cat.categories):
              for c, col_ in enumerate(plotdf[col].cat.categories):
                  plot_ax = axx[r, c] # the axes to plot on.
                  # Plot the means as cumulative lines.
                  plotdf_mean[(col_, row_)].plot(ax=plot_ax, lw=1)
                  # Now, plot the CIs individually.
                  for yvar_type in lower_ci[(col_, row_)].columns:
                      plot_ax.fill_between(plotdf_mean.index,
                                           lower_ci[(col_, row_, yvar_type)],
                                           upper_ci[(col_, row_, yvar_type)],
                                           alpha=0.25)
                  plot_ax.set_title("{}; {}".format(row_, col_))
      else:
          # We only have one dimension here.
          plot_dim = [d for d in [row, col] if d is not None][0]
          # check how many panels in the single row/column.
          panels = plotdf[plot_dim].unique().tolist()
          more_than_one_panel = len(panels) > 1
          for j, dim_ in enumerate(panels):
              # Get the axes to plot on.
              if more_than_one_panel:
                  plot_ax = axx[j]
              else:
                  plot_ax = axx
              # Plot the means as cumulative lines.
              plotdf_mean[(dim_)].plot(ax=plot_ax, lw=1)
              # Now, plot the CIs individually.
              for yvar_type in lower_ci[(dim_)].columns:
                  plot_ax.fill_between(plotdf_mean.index,
                                       lower_ci[(dim_, yvar_type)],
                                       upper_ci[(dim_, yvar_type)],
                                       alpha=0.25)
              plot_ax.set_title(dim_)

      # Normalize all the y-axis limits.
      if row_count + col_count > 2:
          ax_arr = axx.flatten()
          plt_helper.normalize_ylims(ax_arr,
                                     include_zero=True)
      else:
          ax_arr = [axx]

      for plot_ax in ax_arr:
          # Format x-axis.
          plt_helper.format_timecourse_xaxis(plot_ax,
                                             self.__expt_end_time)
          # Set label for y-axis.
          plot_ax.set_ylabel(yvar)
          # Plot vertical grid lines if desired.
          if gridlines:
              plot_ax.xaxis.grid(True, which='major',
                                 linestyle='dotted', #linewidth=1,
                                 alpha=0.5)

          # Despine and offset each axis.
          sns.despine(ax=plot_ax, trim=True, offset=3)
      if color_by is not None:
          legend_title = ' '
      else:
          legend_title = color_by

      if row_count + col_count > 2:
          for ax in ax_arr[:-1]:
              ax.legend().set_visible(False)

          ax_arr[-1].legend(loc='upper left',
                              title=legend_title,
                              bbox_to_anchor=(-0.05, -0.15))
      else:
          ax_arr[0].legend(loc='upper left',
                           title=legend_title,
                           bbox_to_anchor=(1, 1))

      # End and return the figure.
      if ax is None:
          return axx



def __timecourse_plotter(self,
                         yvar,
                         col,
                         row,
                         color_by,
                         resample_by='5min',
                         fig_size=None,
                         gridlines=True,
                         ax=None):

    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    from . import plot_helpers as plt_helper
    from .._munger import munger as munge

    feeds = self.__feeds.copy()

    # Handle the group_by and color_by keywords.
    munge.check_group_by_color_by(col, row, color_by, feeds)

    ## DICTIONARY FOR MATCHING YVAR TO APPROPRIATE YLABEL.
    yvar_ylabel_dict = {'AverageFeedVolumePerFly_µl':'Average Feed Volume Per Fly (µl)',
                       'AverageFeedCountPerFly':'Average Feed Count Per Fly',
                       'AverageFeedSpeedPerFly_µl/s':'Average Feed Speed Per Fly (µl/s)'}

    ylab = yvar_ylabel_dict[yvar]

    resamp_feeds = munge.groupby_resamp_sum(feeds, '5min')
    resamp_feeds_sum = munge.sum_for_timecourse(resamp_feeds)
    plotdf = self.__pivot_for_plot(resamp_feeds_sum, row, col, color_by)

    # print("Coloring time course by {0}".format(color_by))
    if row is not None:
        # print("Plotting rows by {0}".format(row))
        row_count = int(len(feeds[row].cat.categories))
    else:
        row_count = 1
    if col is not None:
        # print("Plotting columns by {0}".format(col))
        col_count = int(len(feeds[col].cat.categories))
    else:
        col_count = 1


    # DICTIONARY FOR MATCHING YVAR TO APPROPRIATE YLABEL.
    yvar_ylabel_dict = {'AverageFeedVolumePerFly_µl':'Average Feed Volume Per Fly (µl)',
                       'AverageFeedCountPerFly':'Average Feed Count Per Fly',
                       'AverageFeedSpeedPerFly_µl/s':'Average Feed Speed Per Fly (µl/s)'}


    # Initialise figure.
    sns.set(style='ticks',context='poster')
    if fig_size is None:
        x_inches = 10 * col_count
        y_inches = 7 * row_count
    else:
        if isinstance(fig_size, tuple) or isinstance(fig_size, list):
            x_inches = fig_size[0]
            y_inches = fig_size[1]
        else:
            raise TypeError('Please make sure figsize is a tuple of the '
            'form (w,h) in inches.')

    if ax is None:
        fig,axx = plt.subplots(nrows=row_count, ncols=col_count,
                               figsize=(x_inches,y_inches),
                               gridspec_kw={'wspace':0.3,
                                           'hspace':0.3})
    else:
        axx = ax

    if row is not None and col is not None:
        for r, row_ in enumerate(feeds[row].cat.categories):
            for c, col_ in enumerate(feeds[col].cat.categories):
                plot_ax = axx[r, c] # the axes to plot on.

                # Reshape the current data to be plotted.
                current_plot_df = plotdf.loc[(row_, col_), yvar]

                # We unstack and transpose to create a 'long' dataset,
                # where each column is a timecourse dataset to be plotted.
                current_plot_df = current_plot_df.unstack().T

                # Create the plot.
                current_plot_df.plot.area(ax=plot_ax, stacked=True)
                plot_ax.set_title("{}; {}".format(row_, col_))

    else:
        # We only have one dimension here.
        plot_dim = [d for d in [row, col] if d is not None][0]
        for j, dim_ in enumerate(feeds[plot_dim].cat.categories):

            plot_ax = axx[j]

            current_plot_df = plotdf.loc[dim_, yvar]
            current_plot_df = current_plot_df.unstack().T

            current_plot_df.plot.area(ax=plot_ax, stacked=True)
            plot_ax.set_title(dim_)

    # Normalize all the y-axis limits.
    if row_count + col_count > 1:
        plt_helper.normalize_ylims(axx.flatten(),
                                 include_zero=True)
        for plot_ax in axx.flatten():
            # Format x-axis.
            plt_helper.format_timecourse_xaxis(plot_ax, 21600)
            # Set label for y-axis.
            plot_ax.set_ylabel(ylab)
            # Plot vertical grid lines if desired.
            if gridlines:
                plot_ax.xaxis.grid(True, which='major',
                                   linestyle='dotted', #linewidth=1,
                                   alpha=0.5)
            # Despine and offset each axis.
            sns.despine(ax=plot_ax, trim=True, offset=3)

    for ax in axx.flatten()[:-1]:
        ax.legend().set_visible(False)

    if color_by is not None:
        legend_title = ' '
    else:
        legend_title = color_by
    axx.flatten()[-1].legend(loc='upper left',
                             title=legend_title,
                             bbox_to_anchor=(-0.05, -0.15))

    # End and return the figure.
    if ax is None:
        return axx
