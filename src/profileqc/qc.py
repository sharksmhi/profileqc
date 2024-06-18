#!/usr/bin/env python
# Copyright (c) 2022 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2022-01-04 17:05

@author: johannes
"""
import logging
import pandas as pd
from profileqc.config import Settings
from profileqc.utils import (
    get_time_as_format,
    get_pressure_str,
    get_float_list,
    get_parameter_str,
    QcLog
)
from profileqc.parameter_dependencies import ParameterDependencies

logger = logging.getLogger(__file__)


class SessionQC:
    """Main class of ProfileQC.

    Run quality control routines and flag data under the Q0-fields.
    The intent is that each parameter has two corresponding flag fields:
        - Q0_'PARAMTER_NAME': Flag field that represents the automatic QC
                              of this package.
        - Q_'PARAMTER_NAME':  Main flag field that inherits flags from Q0.
                              Can later be change on visual inspection.

    SHARK Quality control flags:
        0: No QC was performed
        A: Accepted/Good value
        B: Bad value
        S: Suspicious value
        E: Suspect extreme value that is checked and OK. (not implemented)
        <: Value is under the limit of quantification. (not implemented)
    """

    meta_columns = {'YEAR', 'MONTH', 'DAY', 'HOUR', 'MINUTE', 'SECOND',
                    'CRUISE', 'STATION', 'LATITUDE_DD', 'LONGITUDE_DD',
                    'COMNT_SAMP', 'SCAN_BIN_CTD'}

    default_comnt = '//COMNT_QC; AUTOMATIC QC PERFORMED BY {}; TIMESTAMP {}; {}'

    def __init__(self, data_item, parameter_mapping=None, routines=None,
                 routine_settings=None, routine_path=None, dataset_name=None,
                 advanced_settings_name=None):
        """Initiate."""
        QcLog()
        self.parameter_mapping = parameter_mapping
        self._parameter_dependencies = ParameterDependencies()
        if data_item:
            self.df = data_item.get('data')
            self.meta = data_item.get('metadata')
        self.dataset_name = dataset_name
        self.routines = routines
        self.routine_path = routine_path
        self.routine_settings = routine_settings
        self.advanced_settings_name = advanced_settings_name
        self.settings = Settings(
            routines=self.routines,
            routine_path=self.routine_path,
            advanced_routine_settings=self.routine_settings,
            advanced_qc_spec_name=self.advanced_settings_name
        )

    def update_data(self, data_item, parameter_mapping=None, dataset_name=None):
        """Update data."""
        self.dataset_name = dataset_name
        self.parameter_mapping = parameter_mapping
        self.df = data_item.get('data')
        self.meta = data_item.get('metadata')

    def update_routines(self):
        """Doc."""
        self.settings.update_routine_settings(
            latitude=self.df['LATITUDE_DD'][0],
            longitude=self.df['LONGITUDE_DD'][0],
            month=self.df['MONTH'][0]
        )

    def initialize_qc_object(self, setting, name, item):
        """Return QC routine."""
        return setting['routines'][name]['routine'](self.df, **item)

    def run(self):
        """Run QC routines."""
        self._open_up_flag_fields()

        for qc_routine, qc_index in self.settings.qc_routines.items():
            qc_setting = getattr(self.settings, qc_routine)

            for par, item in qc_setting['datasets'].items():

                # Check if parameters exists
                if not self.parameters_available(item):
                    continue

                # Check if data exists
                if not self.data_available(item):
                    continue

                # Get QC routine
                qc_func = self.initialize_qc_object(qc_setting, qc_routine,
                                                    item)

                # Run QC routine
                qc_func()

                par_dep = self._parameter_dependencies.get_dependent_qf_parameters(par)

                # Check results and execute appropriate action (flag the data)
                # self.add_qflag(qc_func.flag_return, item.get('q_parameters'), qc_index)
                self.add_qflag(qc_func.flag_return, par_dep, qc_index)

                if qc_func.inverted_boolean.any():
                    # pressure_string = get_pressure_str(
                    #     self.df.loc[
                    #         qc_func.inverted_boolean,
                    #         self.parameter_mapping.get('PRES_CTD')
                    #     ]
                    # )
                    pressure_list = get_float_list(
                        self.df.loc[
                            qc_func.inverted_boolean,
                            self.parameter_mapping.get('PRES_CTD')
                        ]
                    )

                    para_string = get_parameter_str(item)
                    para_data_list = self._get_parameter_diff_list(para_string, qc_func)
                    if not para_data_list:
                        try:
                            para_data_list = get_float_list(
                                self.df.loc[
                                    qc_func.inverted_boolean,
                                    self.parameter_mapping.get(para_string)
                                ]
                            )
                        except KeyError as e:
                            logger.info(f'-No parameter_mapping found for key: {para_string}')
                            logger.debug(f'   = {item=}')
                            logger.debug(f'   - {para_string=}')
                            logger.debug(f'   - {self.parameter_mapping.get(para_string)=}')

                    QcLog.update_info(
                        serie=self.dataset_name,
                        routine_name=qc_routine,
                        parameter=para_string,
                        pressure=pressure_list,
                        parameter_data=para_data_list,
                        # pressure=pressure_string,
                        flag=str(qc_func.q_flag),
                        qc_index=qc_index,
                        info=f'Flagged with: {qc_func.q_flag}'
                    )

        self._close_flag_fields()
        self.synchronize_flag_fields()
        self.append_qc_comment()

    def _get_parameter_diff_list(self, para_string, qc_func):
        if '-' not in para_string:
            return False
        par1, par2 = [par.strip() for par in para_string.split('-')]
        par1_data_list = get_float_list(
            self.df.loc[
                qc_func.inverted_boolean,
                self.parameter_mapping.get(par1)
            ]
        )
        par2_data_list = get_float_list(
            self.df.loc[
                qc_func.inverted_boolean,
                self.parameter_mapping.get(par2)
            ]
        )
        return [p1-p2 for p1, p2 in zip(par1_data_list, par2_data_list)]

    def synchronize_flag_fields(self):
        """Sync auto-flags with primary-flag.

        Auto-QC corresponds to flag field "Q0_{parameter}",
        when calling synchronize_flag_fields() we import flags from
        this field into the primary q-flag field "Q_{parameter}".
        Example:
            Q0_TEMP_CTD             Q_TEMP_CTD
            A00BA       ------>     B
            A00AS       ------>     S
            A00BS       ------>     B
            A00AA       ------>
        A-flags will not be visible in primary flag field.
        During manual quality control we only change the primary flag field.
        """
        q0_fields = iter(q for q in self.df.columns if q.startswith('Q0_'))

        for q0_key in q0_fields:
            primary_q_key = q0_key.replace('Q0_', 'Q_')
            for f in ('S', 'B'):
                self._sync_flag(q0_key, primary_q_key, f)

    def _sync_flag(self, q0_key, q_key, flag):
        """Set flag to flag field."""
        boolean = self.df[q0_key].str.contains(flag, regex=False)
        if boolean.any():
            self.df.loc[boolean, q_key] = flag

    def add_qflag(self, flag_field, q_flag_keys, qc_index):
        """Add flag to the correct index.

        Args:
            flag_field (list): eg. ['0', '0', '0', '0', '0']
            q_flag_keys (list): Data q-flag keys
                                eg. ['Q0_TEMP_CTD', 'Q0_DENS_CTD'].
            qc_index (int): index of flag_field (list).
        """
        for flag_key in q_flag_keys:
            if flag_key not in self.df:
                continue

            for qf_list, qf in zip(self.df[flag_key], flag_field):
                if qf_list[qc_index] == '0' or qf_list[qc_index] == 'A':
                    qf_list[qc_index] = qf
                elif qf_list[qc_index] == 'S' and qf == 'B':
                    qf_list[qc_index] = qf
                elif qf == 'S':  # qf_list[qc_index] != 'B'
                    qf_list[qc_index] = qf

    def set_qc0_standard_format(self, key=None):
        """Set default QC0 format."""
        self.df[key] = '0' * self.settings.number_of_routines

    def _open_up_flag_fields(self):
        """Open up QC0-flag field.

        Convert string format to list format.
        Eg. ['AAAAA', 'BSAAA'] --> [['A', 'A', 'A', 'A', 'A'],
                                    ['B', 'S', 'A', 'A', 'A']]
        """
        for key in self.df:
            key = key.split(' ')[0]
            if key not in self.meta_columns:
                if not key.startswith('Q'):
                    if 'Q0_' + key not in self.df:
                        self.set_qc0_standard_format(key='Q0_' + key)
                elif key.startswith('Q0_'):
                    if not type(self.df[key][0]) == str:
                        # In case we have a column for the QC-0 flags
                        # but not the correct format ('xxxxx').
                        self.set_qc0_standard_format(key=key)
                    elif not len(self.df[key][0]):
                        self.set_qc0_standard_format(key=key)

        for q_key in self.df:
            if q_key.startswith('Q0_'):
                self.df[q_key] = self.df[q_key].apply(list)

    def _close_flag_fields(self):
        """Close down QC0-flag field.

        Convert list format to string format.
        Eg. [['A', 'A', 'A', 'A', 'A'],
             ['B', 'S', 'A', 'A', 'A']] --> ['AAAAA', 'BSAAA']
        """
        for q_key in self.df:
            if q_key.startswith('Q0_'):
                self.df[q_key] = self.df[q_key].apply(''.join)

    def parameters_available(self, item):
        """Check if parameter(s) exists in self.df."""
        if item.get('parameter'):
            if item.get('parameter') in self.df:
                return True
            if self.parameter_mapping.get(item['parameter']):
                new_param = self.parameter_mapping.get(item['parameter'])
                if new_param in self.df:
                    item['parameter'] = new_param
                    return True

        if item.get('parameters'):
            if all(x in self.df for x in item.get('parameters')):
                return True
            mapped = [self.parameter_mapping.get(p) for p in
                      item.get('parameters')]
            if all(mapped):
                if all(x in self.df for x in mapped):
                    item['parameters'] = mapped
                    return True

    def data_available(self, item):
        """Check if the parameter(s) in self.df have any data."""
        if item.get('parameter'):

            print(f"{item.get('parameter')=}")
            print(f"{self.df[item.get('parameter')]=}")
            print(f"{type(self.df[item.get('parameter')])=}")
            print(f"{self.df[item.get('parameter')].any()=}")
            if self.df[item.get('parameter')].any():
                return True

        if item.get('parameters'):
            if all(self.df[p].any() for p in item.get('parameters')):
                return True

    def append_qc_comment(self):
        """Append comment to metadata series."""
        time_stamp = get_time_as_format(now=True, fmt='%Y%m%d%H%M')
        self.meta[len(self.meta) + 1] = self.default_comnt.format(
            self.settings.user, time_stamp, self.settings.repo_version
        )

    def reset_log(self):
        """Reset log."""
        QcLog.update_info(reset_log=True)

    def write_log(self, path, reset_log=False):
        """Write log to file."""
        QcLog.write(path)
        if reset_log:
            self.reset_log()


if __name__ == "__main__":
    df = {'metadata': pd.Series([1, 2, 3, 4, 5]),
          'data': pd.DataFrame({'a': [1, 2, 3, 4, 5]})}
    qcb = SessionQC(df)
