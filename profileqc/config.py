#!/usr/bin/env python
# Copyright (c) 2022 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2022-01-04 15:49

@author: johannes
"""
import json
import yaml
import pandas as pd
import geopandas as gp
from shapely.geometry import Point
from pathlib import Path
from profileqc import utils


def qc_fail_message(obj, spec):
    """Print message of QC failure."""
    print('QC-{} failed for {}'.format(obj.__class__.__name__, spec))


def qc_pass_message(obj, spec):
    """Print message of QC approval."""
    print('QC-{} passed for {}'.format(obj.__class__.__name__, spec))


class AdvancedQC:
    """"""

    def __init__(self, file_path=None, basin_shp_path=None):
        self.basin_gf = gp.read_file(basin_shp_path)
        self.data = {}
        xlsx_file = pd.ExcelFile(file_path)
        for sheet in xlsx_file.sheet_names:
            if sheet.startswith('qc_'):
                self.data[sheet] = pd.read_excel(
                    xlsx_file, sheet).set_index('PARAMETER')
                self.data[sheet]['MONTH_LIST'] = self.data[sheet][
                    'MONTHS'].str.replace(' ', '').str.split(',')

    def extract_advanced_settings(self, area, month):
        _data = {}
        for routine, _item in self.data.items():
            boolean = (_item['AREA_NAME'] == area) & (
                _item['MONTH_LIST'].apply(lambda x: month in x))
            cols = [c for c in _item.columns if
                    c not in ('AREA_NAME', 'SEASON')]
            _data.setdefault(routine, _item.loc[boolean, cols].to_dict('index'))
        return _data

    def get_area(self, lat, lon):
        boolean = self.basin_gf.contains(Point((float(lon), float(lat))))
        return self.basin_gf.loc[boolean, 'AREA_NAME'].iloc[0]

    def get_routine_settings(self, latitude=None, longitude=None, month=None):
        area = self.get_area(latitude, longitude)
        return self.extract_advanced_settings(area, str(int(month)))


class Settings:
    """Config class.

    Keep track of available QC routines and parameter settings.
    """

    def __init__(self, routines=None, routine_path=None,
                 advanced_routine_settings=None, advanced_qc_spec_name=None):
        """Initiate settings object."""
        # TODO: enable possibility for local settings

        self.qc_routines = {}
        self.base_directory = utils.get_base_folder()
        self.routines = routines
        self.routine_path = routine_path
        self._load_settings(self.base_directory.joinpath('etc'),
                            routines=routines,
                            routine_path=routine_path,
                            advanced_settings=advanced_routine_settings)
        self.user = Path.home().name
        self.repo_version = utils.git_version()
        if advanced_qc_spec_name:
            if not advanced_qc_spec_name.endswith('.xlsx'):
                advanced_qc_spec_name = advanced_qc_spec_name + '.xlsx'
            self.advanced_spec = AdvancedQC(
                file_path=self.base_directory.joinpath(
                    f'etc/qc_advanced_spec/{advanced_qc_spec_name}'),
                basin_shp_path=self.base_directory.joinpath(
                    'etc/resources/shp/basins.shp')
            )
        else:
            self.advanced_spec = None

    def update_routine_settings(self, latitude=None, longitude=None,
                                month=None):
        """Doc."""
        spec = self.advanced_spec.get_routine_settings(
            latitude=latitude, longitude=longitude, month=month)
        self._load_settings(
            self.base_directory.joinpath('etc'),
            routines=self.routines,
            routine_path=self.routine_path,
            advanced_settings=spec,
            only_routines=True
        )

    def add_routines(self, value):
        """Update class routines."""
        for func in value['routines'].values():
            self.qc_routines.setdefault(func.get('name'), func.get('qc_index'))

    def _load_settings(self, etc_path, routines=None, routine_path=None,
                       advanced_settings=None, only_routines=False):
        """Load settings."""
        settings = {}
        if not only_routines:
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
        if advanced_settings:
            self._update_settings(settings, advanced=advanced_settings)

        self.set_attributes(self, **settings)

    @staticmethod
    def _update_settings(settings, advanced=None):
        """Overwrite with advanced routine specifications."""
        for routine, routine_item in advanced.items():
            for para, para_item in routine_item.items():
                if para in settings[routine]['datasets']:
                    for key, value in para_item.items():
                        if value and key in settings[routine]['datasets'][para]:
                            settings[routine]['datasets'][para][key] = value

    def set_attributes(self, obj, **kwargs):
        """Set attribute to object."""
        for key, value in kwargs.items():
            if 'routines' in value and 'datasets' in value:
                for item in value['routines'].values():
                    item['name'] = key
                value['routines'][key] = item

                for item in value['datasets'].values():
                    item['routine'] = key
                self.add_routines(value)
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
    s = Settings()
    for p in s.qc_range['datasets'].keys():
        print(p)

    # routine_path = Path(
    #     r'C:\Utveckling\TESTING\ctd_qc_advanced\advanced_qc_routine')
    # for fid in routine_path.glob('**/*.yaml'):
    #     with open(fid, encoding='utf8') as fd:
    #         content = yaml.load(fd, Loader=yaml.FullLoader)
    #         content['routines']['_'.join(
    #             fid.stem.split('_')[:2])]['name'] = fid.stem
