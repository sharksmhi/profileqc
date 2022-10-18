import pandas as pd
import geopandas as gp
from shapely.geometry import Point
import pathlib
from typing import Union, Dict, List
from functools import lru_cache

SpecificSettingsType = Dict[str, pd.DataFrame]


DIRECTORY = pathlib.Path(__file__).parent.absolute()
USERS_DIRECTORY = pathlib.Path(DIRECTORY, 'etc')


SEASONS = {
    1: 'winter',
    2: 'winter',
    3: 'spring',
    4: 'spring',
    5: 'spring',
    6: 'summer',
    7: 'summer',
    8: 'summer',
    9: 'autumn',
    10: 'autumn',
    11: 'autumn',
    12: 'winter'
}


@lru_cache
def _get_basin_gf() -> gp.GeoDataFrame:
    return gp.read_file(str(pathlib.Path(DIRECTORY, 'shp', 'basins.shp')))


@lru_cache
def _get_area(lat: float, lon: float) -> str:
    basin_gf = _get_basin_gf()
    boolean = basin_gf.contains(Point((float(lon), float(lat))))
    return basin_gf.loc[boolean, 'AREA_NAME'].iloc[0]


def _get_season(month:  Union[str, int]) -> str:
    return SEASONS.get(int(month))


@lru_cache
def _get_advanced_settings(file_path: Union[str, pathlib.Path]) -> SpecificSettingsType:
    data = {}
    xlsx_file = pd.ExcelFile(file_path)
    for sheet in xlsx_file.sheet_names:
        if sheet.startswith('qc_'):
            data[sheet] = pd.read_excel(
                xlsx_file, sheet).set_index('PARAMETER')
    return data


def _get_settings_path_for_user(user: str) -> pathlib.Path:
    for path in USERS_DIRECTORY.iterdir():
        if user == path.stem.split('-')[-1]:
            return path


def _get_advanced_settings_for_user(user: str) -> SpecificSettingsType:
    path = _get_settings_path_for_user(user)
    if not path:
        raise FileNotFoundError(f'No advanced settings for user {user}')
    return _get_advanced_settings(path)


def _extract_advanced_settings(area: str = None,
                               season: str = None,
                               month: Union[str, int] = None,
                               advanced_settings: SpecificSettingsType = None) -> SpecificSettingsType:
    def _filter_month(item: str, month: Union[str, int]) -> bool:
        if not item:
            return False
        if pd.isna(item):
            return False
        parts = [int(float(s.strip())) for s in str(item).split(';')]
        if int(month) in parts:
            return True
        return False

    data = {}
    for routine, item in advanced_settings.items():
        cols = [c for c in item.columns if c not in ('MONTHS', 'AREA_NAME', 'SEASON')]
        area_boolean = item['AREA_NAME'] == area
        season_boolean = item['SEASON'] == season
        boolean = area_boolean & season_boolean
        item_dict = item.loc[boolean, cols].to_dict('index')
        if month and 'MONTHS' in item.columns:
            month_boolean = item['MONTHS'].apply(_filter_month, args=(month,))
            boolean = area_boolean & month_boolean
            item_month_dict = item.loc[boolean, cols].to_dict('index')
            if item_month_dict:
                item_dict.update(item_month_dict)
        data.setdefault(routine, item_dict)
    return data


def get_specific_qc_users() -> List[str]:
    users = []
    for path in USERS_DIRECTORY.iterdir():
        if not path.suffix == '.xlsx':
            continue
        if not path.stem.startswith('area_specific_qc'):
            continue
        users.append(path.stem.split('-')[-1])
    return users


def get_specific_qc_settings(user: str = None,
                             lat: float = None,
                             lon: float = None,
                             month: Union[str, int] = None) -> SpecificSettingsType:
    advanced_sett = _get_advanced_settings_for_user(user)
    area = _get_area(lat, lon)
    season = _get_season(month)
    return _extract_advanced_settings(area=area,
                                      season=season,
                                      month=month,
                                      advanced_settings=advanced_sett)


if __name__ == '__main__':
    users = get_specific_qc_users()
    sett = get_specific_qc_settings(
        user='test',
        lat=56.,
        lon=12.,
        month=4
    )

    sett = get_specific_qc_settings(
        user='test',
        lat=55.,
        lon=18.,
        month=9
    )

