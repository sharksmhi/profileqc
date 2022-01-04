#!/usr/bin/env python
# Copyright (c) 2022 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2022-01-04 16:36

@author: johannes
"""
import numpy as np


class BooleanBaseDataFrame:
    """Base of pd.DataFrame boolean handling."""

    def __init__(self):
        """Initiate."""
        super().__init__()
        self.data = None
        self._boolean = True
        self._boolean_combo = {}

    def add_boolean_from_list(self, parameter, value_list):
        """Add boolean to self.boolean. See property: self.boolean."""
        self.boolean = self.data[parameter].isin(value_list)

    def add_boolean_month(self, month):
        """Add boolean to self.boolean. See property: self.boolean."""
        self.boolean = self.data['timestamp'].dt.month == month

    def add_boolean_diff(self, parameters, accepted_diff):
        """Add boolean to self.boolean. See property: self.boolean.

        Args:
            parameters: list of two parameters
            accepted_diff: int or float

        True where diff <= accepted_diff.
        False indicates discrepancies between the two parameters.
        """
        # We need 2, and only 2 parameters
        assert len(parameters) == 2

        # Get the absolute difference between parameter_1 and parameter_2
        diff = self.data[parameters].astype(float).diff(axis=1).abs()

        # Check how parameter_2 compares to parameter_1
        # and add this to self.boolean
        # (True indicates difference acceptance)
        self.boolean = diff[parameters[-1]] <= accepted_diff

    def add_boolean_equal(self, param, value):
        """Add boolean to self.boolean. See property: self.boolean."""
        self.boolean = self.data[param] == value

    def add_boolean_less_or_equal(self, param, value):
        """Add boolean to self.boolean. See property: self.boolean."""
        self.boolean = self.data[param] <= value

    def add_boolean_greater_or_equal(self, param, value):
        """Add boolean to self.boolean. See property: self.boolean."""
        self.boolean = self.data[param] >= value

    def add_boolean_not_equal(self, param, value):
        """Add boolean to self.boolean. See property: self.boolean."""
        self.boolean = self.data[param] != value

    def add_boolean_not_nan(self, param):
        """Add boolean to self.boolean. See property: self.boolean."""
        self.boolean = self.data[param].notna()

    def reset_boolean(self):
        """Reset boolean to True."""
        self._boolean = True

    def reset_boolean_combo(self):
        """Reset combo boolean."""
        self._boolean_combo = {}

    def add_combo_boolean(self, key, boolean, only_true_values=False):
        """Add boolean to the dictionary self._boolean_combo."""
        self._boolean_combo[key] = boolean
        if only_true_values:
            boolean_true = self.boolean_not_nan(key)
            self._boolean_combo[key] = self._boolean_combo[key] & boolean_true

    def remove_combo_boolean(self, key):
        """Delete boolean from dictionary."""
        self._boolean_combo.pop(key, None)

    def boolean_not_nan(self, param):
        """Return boolean."""
        return self.data[param].notna()

    @property
    def _boolean_stack(self):
        """Return a stacked numpy array of booleans.

        Based on the dictionary self._boolean_combo.
        """
        return np.column_stack(
            [self._boolean_combo[key] for key in self._boolean_combo.keys()]
        )

    @property
    def combo_boolean_all(self):
        """Return boolean."""
        try:
            return self._boolean_stack.all(axis=1)
        except ValueError:
            return self._boolean

    @property
    def combo_boolean_any(self):
        """Return boolean."""
        return self._boolean_stack.any(axis=1)

    @property
    def index(self):
        """Return index array."""
        return np.where(self.boolean)[0]

    @property
    def boolean(self):
        """Return boolean."""
        return self._boolean

    @boolean.setter
    def boolean(self, add_bool):
        """Add boolean."""
        self._boolean = self._boolean & add_bool


class BooleanBaseSerie:
    """Base of pd.Series boolean handling."""

    def __init__(self):
        """Initiate."""
        super().__init__()
        self.serie = None
        self._boolean = True
        self._boolean_combo = {}

    def add_boolean_from_list(self, value_list):
        """Add boolean to self.boolean. See property: self.boolean."""
        self.boolean = self.serie.isin(value_list)

    def add_boolean_equal(self, value):
        """Add boolean to self.boolean. See property: self.boolean."""
        self.boolean = self.serie == value

    def add_boolean_less_or_equal(self, value):
        """Add boolean to self.boolean. See property: self.boolean."""
        self.boolean = self.serie <= value

    def add_boolean_greater_or_equal(self, value):
        """Add boolean to self.boolean. See property: self.boolean."""
        self.boolean = self.serie >= value

    def add_boolean_not_equal(self, value):
        """Add boolean to self.boolean. See property: self.boolean."""
        self.boolean = self.serie != value

    def add_boolean_less_than_other(self, other):
        """Add boolean to self.boolean. See property: self.boolean.

        Compare self.serie to other index-wise.
        If self.serie[index] < other[index] : True else False

        Args:
            other: pd.Series of the same length as self.serie
        """
        self.boolean = self.serie.lt(other)

    def add_boolean_greater_than_other(self, other):
        """Add boolean to self.boolean. See property: self.boolean.

        Compare self.serie to other index-wise.
        If self.serie[index] > other[index] : True else False

        Args:
            other: pd.Series of the same length as self.serie
        """
        self.boolean = self.serie.gt(other)

    def add_boolean_not_nan(self):
        """Add boolean to self.boolean. See property: self.boolean."""
        self.boolean = self.serie.notna()

    def reset_boolean(self):
        """Reset boolean to True."""
        self._boolean = True

    def reset_boolean_combo(self):
        """Reset combo boolean."""
        self._boolean_combo = {}

    def add_combo_boolean(self, key, boolean, only_true_values=False):
        """Add boolean to the dictionary self._boolean_combo."""
        self._boolean_combo[key] = boolean
        if only_true_values:
            boolean_true = self._boolean_not_nan()
            self._boolean_combo[key] = self._boolean_combo[key] & boolean_true

    def remove_combo_boolean(self, key):
        """Delete boolean from dictionary."""
        self._boolean_combo.pop(key, None)

    def _boolean_not_nan(self):
        """Return boolean."""
        return self.serie.notna()

    @property
    def _boolean_stack(self):
        """Return a stacked numpy array of booleans.

        Based on the dictionary self._boolean_combo.
        """
        return np.column_stack(
            [self._boolean_combo[key] for key in self._boolean_combo.keys()]
        )

    @property
    def combo_boolean_all(self):
        """Return boolean."""
        try:
            return self._boolean_stack.all(axis=1)
        except ValueError:
            return self._boolean

    @property
    def combo_boolean_any(self):
        """Return boolean."""
        return self._boolean_stack.any(axis=1)

    @property
    def index(self):
        """Return index array."""
        return np.where(self.boolean)[0]

    @property
    def boolean(self):
        """Return boolean."""
        return self._boolean

    @boolean.setter
    def boolean(self, add_bool):
        """Add boolean."""
        self._boolean = self._boolean & add_bool
