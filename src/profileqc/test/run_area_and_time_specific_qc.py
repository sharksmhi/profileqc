#!/usr/bin/env python
# Copyright (c) 2022 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2022-10-12 15:43

@author: johannes
"""
from ctdpy.core.session import Session
from ctdpy.core.utils import generate_filepaths, get_reversed_dictionary
from profileqc.qc import SessionQC
import warnings
warnings.filterwarnings("ignore")


if __name__ == "__main__":
    base_dir = r'C:\Arbetsmapp\datasets\Profile\2021\SHARK_Profile_2021_COD_SMHI\processed_data'  # noqa: E501

    files = generate_filepaths(base_dir, endswith='.txt')
    s = Session(filepaths=files, reader='ctd_stdfmt')
    datasets = s.read()

    qc_run = SessionQC(None, advanced_settings_name='smhi_expedition')

    for dset_name, item in datasets[0].items():
        parameter_mapping = get_reversed_dictionary(
            s.settings.pmap, item['data'].keys()
        )
        qc_run.update_data(item, parameter_mapping=parameter_mapping,
                           dataset_name=dset_name)
        qc_run.update_routines()
        qc_run.run()

    qc_run.write_log('C:/ctdpy_exports/qc_log.yaml', reset_log=True)

    data_path = s.save_data(
        datasets,
        writer='ctd_standard_template',
        return_data_path=True,
        save_path='C:/ctdpy_exports'
    )
