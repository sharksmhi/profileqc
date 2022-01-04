#!/usr/bin/env python
# Copyright (c) 2022 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-02-20 11:45

@author: a002028
"""
import numpy as np
import pandas as pd
from profileqc.boolean_handler import BooleanBaseSerie
from profileqc.config import qc_fail_message


class Range(BooleanBaseSerie):
    """QC-routine.

    We check how values for x number of parameters differ from one another.
    """

    def __init__(self, df_or_serie, parameter=None, q_flag=None,
                 min_range_value=None, max_range_value=None):
        """Initiate."""
        super().__init__()
        self.qc_passed = False
        self.q_flag = q_flag or 'B'
        if type(df_or_serie) == pd.DataFrame:
            self.serie = df_or_serie[parameter].astype(float)
        else:
            self.serie = df_or_serie.astype(float)
        self.min = min_range_value
        self.max = max_range_value

    def __call__(self):
        """Run routine."""
        self.add_boolean_less_or_equal(self.max)
        self.add_boolean_greater_or_equal(self.min)

        if all(self.boolean):
            # Data passed with distinction!
            self.qc_passed = True
            # qc_pass_message(self, self.serie.name)
        else:
            qc_fail_message(self, self.serie.name)

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


if __name__ == "__main__":
    import time
    df = pd.DataFrame({'TEMP': ['AAAA'] * 100000})

    start_timeit = time.time()
    df['TEMP'].apply(tuple)
    print("Timed: --apply(tuple) in %.9f sec" % (time.time() - start_timeit))

    start_timeit = time.time()
    li = df['TEMP'].apply(list)
    # tup.apply(''.join)
    print("Timed: --apply(list) in %.9f sec" % (time.time() - start_timeit))

    def set_flag(value, i, flag):
        """Doc."""
        value[i] = flag
        return value

    start_timeit = time.time()
    li = li.apply(lambda x: set_flag(x, 1, 'Bb'))
    print("Timed: --set_flag in %.9f sec" % (time.time() - start_timeit))

    start_timeit = time.time()
    li.apply(''.join)
    print("Timed: --join in %.9f sec" % (time.time() - start_timeit))

    a = [[1, 2, 3]] * 1000000
    a = pd.Series(a)
    b = [6] * 100

    start_timeit = time.time()
    index = 1
    # def ff(i, j):
    #     i[index] = j
    #     return i
    # generator = (ff(i, j) for i, j in zip(a, b))
    # a = list(generator)

    for i, j in zip(a, b):
        i[index] = j
    print("Timed: --generator in %.9f sec" % (time.time() - start_timeit))
