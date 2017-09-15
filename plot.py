#!/usr/bin/python
# -*-coding: utf-8 -*-
# Author: Joses Ho
# Email : joseshowh@gmail.com

"""
Plot functions for espresso objects.
"""

import sys as _sys
import os as _os

import numpy as _np
import scipy as _sp
import pandas as _pd

import matplotlib as _mpl
import matplotlib.pyplot as _plt

import seaborn as _sns
import bootstrap_contrast as _bsc


def swarm():
    x=_np.random.random(10)
    y=_np.random.random(10)
    df=_pd.DataFrame([x,y]).T
    ax=_sns.swarmplot(data=df)

    return ax
