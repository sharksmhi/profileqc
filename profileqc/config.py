#!/usr/bin/env python
# Copyright (c) 2022 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2022-01-04 15:49

@author: johannes
"""
import json
import yaml
from pathlib import Path
from profileqc import utils


def qc_fail_message(obj, spec):
    """Print message of QC failure."""
    print('QC-{} failed for {}'.format(obj.__class__.__name__, spec))


def qc_pass_message(obj, spec):
    """Print message of QC approval."""
    print('QC-{} passed for {}'.format(obj.__class__.__name__, spec))


class Settings:
    """Config class.

    Keep track of available QC routines and parameter settings.
    """

    def __init__(self, routines=None, routine_path=None):
        """Initiate settings object."""
        # TODO: enable possibility for local settings

        self.qc_routines = {}
        self.base_directory = utils.get_base_folder()
        self._load_settings(self.base_directory.joinpath('etc'),
                            routines=routines,
                            routine_path=routine_path)
        self.user = Path.home().name
        self.repo_version = utils.git_version()

    def update_routines(self, value):
        """Update class routines."""
        for func in value['routines'].values():
            self.qc_routines.setdefault(func.get('name'), func.get('qc_index'))

    def _load_settings(self, etc_path, routines=None, routine_path=None):
        """Load settings."""
        settings = {}
        for fid in etc_path.glob('**/*.json'):
            with open(fid, 'r') as fd:
                content = json.load(fd)
                settings[fid.stem] = content

        routine_path = Path(routine_path) if routine_path else etc_path
        if routines:
            for fid in routines:
                with open(fid, encoding='utf8') as fd:
                    content = yaml.load(fd, Loader=yaml.FullLoader)
                    settings[Path(fid).stem] = content
        else:
            for fid in routine_path.glob('**/*.yaml'):
                with open(fid, encoding='utf8') as fd:
                    content = yaml.load(fd, Loader=yaml.FullLoader)
                    settings[fid.stem] = content

        self.set_attributes(self, **settings)

    def set_attributes(self, obj, **kwargs):
        """Set attribute to object."""
        for key, value in kwargs.items():
            if 'routines' in value and 'datasets' in value:
                for item in value['routines'].values():
                    item['name'] = key
                value['routines'][key] = item

                for item in value['datasets'].values():
                    item['routine'] = key
                self.update_routines(value)
            setattr(obj, key, value)

    @property
    def number_of_routines(self):
        """Return number of routines.

        Used when setting up the Auto-QC flag fields.

        Example: Q0_TEMP_CTD: ['AAAAA', 'AAAAA'...]
        where the length of 'AAAAA' equals self.number_of_routines.
        """
        return len(self.qc_routines)


if __name__ == "__main__":
    # s = Settings()
    routine_path = Path(r'C:\Utveckling\TESTING\ctd_qc_advanced\advanced_qc_routine')
    for fid in routine_path.glob('**/*.yaml'):
        with open(fid, encoding='utf8') as fd:
            content = yaml.load(fd, Loader=yaml.FullLoader)
            content['routines']['_'.join(fid.stem.split('_')[:2])]['name'] = fid.stem
