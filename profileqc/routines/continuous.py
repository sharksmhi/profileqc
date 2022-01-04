#!/usr/bin/env python
# Copyright (c) 2022 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-02-20 13:34

@author: a002028
"""
import numpy as np
import pandas as pd
from profileqc.boolean_handler import BooleanBaseSerie
from profileqc.config import qc_fail_message

# FIXME if we need a boolean return (in order to say which values are causing
#  the QC-routine to fail) we use BooleanBaseSerie.
#  However, if we don´t need this, we can exclude the base inheritance..


class ContinuousBase(BooleanBaseSerie):
    """Base class of any continuous routine."""

    def __init__(self, df_or_serie, parameter=None, q_flag=None,
                 acceptable_error=None):
        """Initiate."""
        super().__init__()
        if type(df_or_serie) == pd.DataFrame:
            self.serie = df_or_serie[parameter].astype(float)
        else:
            self.serie = df_or_serie.astype(float)
        self.qc_passed = False
        self.q_flag = q_flag or 'B'
        self.acceptable_error = acceptable_error

    @property
    def boolean_return(self):
        """Return boolean.

        We insert one "True" on the first index because these types
        of QC-routines check value 2 against value 1. Therefore the first
        value cannot be False.
        However! it can in fact be value 1 that is BAD..


        True means that the corresponding value has passed the test.
        False means that the value has NOT passed and should be
        flagged accordingly.
        """
        return pd.Series([True] + list(self.boolean_generator))
        # boolean = [True] + list(self.generator)
        # return pd.Series(boolean)

    @property
    def flag_return(self):
        """Return serie of flags."""
        flag_serie = np.array(['A'] * self.serie.__len__())
        flag_serie[~self.boolean_return] = self.q_flag
        return flag_serie

    @property
    def boolean_generator(self):
        """Doc."""
        raise NotImplementedError

    @property
    def error_magnitude_accepted(self):
        """Return True / False."""
        return all(self.boolean_generator)


class Decreasing(ContinuousBase):
    """QC-routine.

    Check if value 1 >= value 2 and so on..
    - If not passed: position 1 is flagged as False.
    """

    def __call__(self):
        """Run routine."""
        # TODO handle QC failure.. boolean? report?
        if self.serie.is_monotonic_decreasing:
            # Data passed with distinction!
            self.qc_passed = True
            # qc_pass_message(self, self.serie.name)
        else:
            if self.error_magnitude_accepted:
                # Data passed with acceptable error!
                self.qc_passed = True
                # qc_pass_message(self, self.serie.name)
            else:
                qc_fail_message(self, self.serie.name)

    @property
    def boolean_generator(self):
        """Return generator."""
        return (i >= j for i, j in zip(self.serie, self.control_serie[1:]))

    @property
    def control_serie(self):
        """Return the given data serie minus the acceptable error."""
        return self.serie - self.acceptable_error


class Increasing(ContinuousBase):
    """QC-routine.

    Check if value 1 <= value 2 and so on..
    - If not passed: position 1 is flagged as False.
    """
    def __call__(self):
        """Run routine."""
        # TODO handle QC failure.. boolean? report?
        if self.serie.is_monotonic_increasing:
            # Data passed with distinction!
            self.qc_passed = True
            # qc_pass_message(self, self.serie.name)
        else:
            if self.error_magnitude_accepted:
                # Data passed with acceptable error!
                self.qc_passed = True
                # qc_pass_message(self, self.serie.name)
            else:
                qc_fail_message(self, self.serie.name)

    @property
    def boolean_generator(self):
        """Return generator."""
        return (i <= j for i, j in zip(self.serie, self.control_serie[1:]))

    @property
    def control_serie(self):
        """Return the given data serie minus the acceptable error."""
        return self.serie + self.acceptable_error


if __name__ == "__main__":
    test_4 = [0, 1, 0.9, 2, 3]

    df_tst = pd.DataFrame({
        'test_1': [3, 4, 6, 87, 3],
        'test_2': list(range(5)),
        'test_3': list(range(5))[::-1],
        'test_4': test_4})
    increasing = Increasing(df_tst, parameter='test_4', acceptable_error=0.01)
    increasing()
    decreasing = Decreasing(df_tst, parameter='test_3', acceptable_error=0.01)
    decreasing()
