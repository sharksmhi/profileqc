#!/usr/bin/env python
# Copyright (c) 2022 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-04-14 12:20

@author: a002028
"""
import numpy as np
import pandas as pd
from profileqc.boolean_handler import BooleanBaseSerie
from profileqc.config import qc_fail_message


class Spike(BooleanBaseSerie):
    """QC-routine.

    We check how values for x number of parameters differ from one another.
    """

    def __init__(self, df_or_serie, parameter=None, q_flag=None,
                 acceptable_stddev_factor=None, min_stddev_value=None,
                 **kwargs):
        """Initiate."""
        super().__init__()
        self.qc_passed = False
        self.q_flag = q_flag or 'B'

        if type(df_or_serie) == pd.DataFrame:
            self.serie = df_or_serie[parameter].astype(float)
        else:
            self.serie = df_or_serie.astype(float)

        self.acceptable_stddev_factor = acceptable_stddev_factor
        self.min_stddev_value = min_stddev_value

        # self.index_window = 7  # ok window?
        # user can control the outcome with acceptable_stddev_factor
        # self.min_periods = 3  # or np.floor(self.index_window / 2)
        self.rolling = self.serie.rolling(7, min_periods=3, center=True)

    def __call__(self):
        """Run routine."""
        self.add_boolean_less_than_other(self.max)
        self.add_boolean_greater_than_other(self.min)

        if all(self.boolean):
            # Data passed with distinction!
            self.qc_passed = True
            # qc_pass_message(self, self.serie.name)
        else:
            qc_fail_message(self, self.serie.name)

    @property
    def min(self):
        """Return acceptable minimum values."""
        return self._mean - self._std

    @property
    def max(self):
        """Return acceptable maximum values."""
        return self._mean + self._std

    @property
    def _mean(self):
        """Return mean values from the rolling object."""
        return self.rolling.mean()

    @property
    def _std(self):
        """Return standard deviation values from the rolling object.

        Based on the settings for this routine, we use a minimum value for the
        standard deviation and a factor to multiply with depending on the
        parameter and sensor sensitivity.
        """
        std_serie = self.rolling.std()
        boolean = std_serie < self.min_stddev_value
        std_serie[boolean] = self.min_stddev_value
        return std_serie * self.acceptable_stddev_factor

    @property
    def boolean_return(self):
        """Return boolean.

        True means that the corresponding value has passed the test.
        False means that the value has NOT passed and should be flagged.
        """
        return self.boolean

    @property
    def flag_return(self):
        """Return serie of flags."""
        flag_serie = np.array(['A'] * self.serie.__len__())
        flag_serie[~self.boolean_return] = self.q_flag
        return flag_serie
