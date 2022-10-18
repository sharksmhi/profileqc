#!/usr/bin/env python
# Copyright (c) 2022 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2022-01-04 15:20

@author: johannes
"""
import yaml
import datetime
from pathlib import Path


def get_base_folder():
    """Return the base folder of ProfileQC."""
    return Path(__file__).parent


def git_version():
    """Return current version of this github-repository."""
    wd = get_base_folder()
    version_file = wd.parent.joinpath('.git', 'FETCH_HEAD')
    if version_file.exists():
        f = open(version_file, 'r')
        version_line = f.readline().split()

        # Is much longer, but only the first 7 letters are presented on Github
        version = version_line[0][:7]
        repo = version_line[-1]
        return 'github version "{}" of repository {}'.format(version, repo)
    else:
        return ''


def get_time_as_format(now=False, fmt=None, timestamp=None):
    """Return datetime in string format."""
    d = None
    if now:
        d = datetime.datetime.now()
    elif timestamp:
        d = timestamp.to_pydatetime()

    if not d:
        raise ValueError

    if fmt:
        return d.strftime(fmt)
    else:
        raise NotImplementedError


def get_pressure_str(pressure_serie):
    """Doc."""
    return ','.join(pressure_serie)


def get_parameter_str(_item):
    """Doc."""
    para_string = _item.get('parameter')
    if para_string:
        para_string = para_string.split('[')[0].strip()
    else:
        plist = [p.split('[')[0].strip()
                 for p in _item.get('parameters')]
        para_string = ' - '.join(plist)
    return para_string


class QcLog:
    """Logger for QC."""

    log = {}

    def __init__(self, *args, reset_log=None, serie=None, routine_name=None,
                 parameter=None, pressure=None, info=None, **kwargs):
        """Log for QC routine failure / comments.

        Args:
            *args (iterable): Other information is stored under "etc".
            reset_log (bool): if True reset cls.log to {}
            serie (str): serie according to format MYEAR_SHIPC_SERNO
                         or profile filename.
            routine_name (str): Name of QC routine.
            parameter (str): Name of parameter.
            pressure (str): Pressure(s).
            info (str): Validation information.
            **kwargs:
        """
        if reset_log:
            self._reset_log()

        if any(args):
            for a in args:
                self.log.setdefault('etc', []).append(a)

        if serie and routine_name and parameter:
            info = info or ''
            pressure = pressure or 'pressure not specified'
            self.log.setdefault(serie, {})
            self.log[serie].setdefault(routine_name, {})
            self.log[serie][routine_name].setdefault(
                'parameter', []).append(parameter)
            self.log[serie][routine_name].setdefault(
                'pressure', []).append(pressure)
            self.log[serie][routine_name].setdefault('info', []).append(info)

    @classmethod
    def update_info(cls, *args, **kwargs):
        """Update information to log."""
        return cls(*args, **kwargs)

    @classmethod
    def _reset_log(cls):
        """Reset cls.log."""
        cls.log = {}

    @classmethod
    def write(cls, file_path):
        """Write to yaml file."""
        with open(file_path, 'w') as file:
            yaml.safe_dump(
                cls.log,
                file,
                indent=4,
                width=120,
                default_flow_style=False,
            )
