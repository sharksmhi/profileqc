#!/usr/bin/env python
# Copyright (c) 2022 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-02-25 14:16

@author: a002028
"""
import numpy as np
import pandas as pd
from profileqc.boolean_handler import BooleanBaseDataFrame
from profileqc.config import qc_fail_message


class DiffBase(BooleanBaseDataFrame):
    """Base class of any diff routine."""

    def __init__(self, df, parameters=None, q_flag=None,
                 acceptable_error=None, **kwargs):
        """Initiate."""
        super().__init__()
        self.qc_passed = False
        self.q_flag = q_flag or 'B'
        self.parameters = parameters
        self.data = df[self.parameters].astype(float)
        self.acceptable_error = acceptable_error

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
        flag_serie = np.array(['A'] * self.data.__len__())
        flag_serie[~self.boolean_return] = self.q_flag
        return flag_serie


class DataDiff(DiffBase):
    """QC-routine.

    We check how values for x number of parameters differ from one another.
    """

    def __call__(self):
        """Run routine."""
        self.add_boolean_diff(self.parameters, self.acceptable_error)
        # TODO handle QC failure.. boolean? report?
        if all(self.boolean):
            # Data passed with distinction!
            self.qc_passed = True
            # qc_pass_message(self, self.parameters)
        else:
            qc_fail_message(self, self.parameters)


if __name__ == "__main__":
    df_tst = pd.DataFrame({'a': [1, 2, 3, 7.2, 5, 6],
                           'b': [2, 3, 4, 5, 6, 7],
                           'c': [4., 5., 6., 7., 8., 9.]})

    diff = DataDiff(df_tst, parameters=['a', 'b'], acceptable_error=2.2)
    diff()
