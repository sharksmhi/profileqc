#!/usr/bin/env python
# Copyright (c) 2022 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2022-01-04 15:20

@author: johannes
"""
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
