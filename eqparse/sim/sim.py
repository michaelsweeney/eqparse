'''
sim table parser
'''

import re
import time
import numpy as np
import pandas as pd

from .plot import SimPlot


months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
          'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
month_sort_dict = {'JAN': '01_JAN',
                   'FEB': '02_FEB',
                   'MAR': '03_MAR',
                   'APR': '04_APR',
                   'MAY': '05_MAY',
                   'JUN': '06_JUN',
                   'JUL': '07_JUL',
                   'AUG': '08_AUG',
                   'SEP': '09_SEP',
                   'OCT': '10_OCT',
                   'NOV': '11_NOV',
                   'DEC': '12_DEC'}


def try_numeric(df):
    def lambda_numeric(x):
        try:
            return pd.to_numeric(x, errors='raise')
        except:
            return x

    df = df.apply(lambda x: lambda_numeric(x))
    return df


def str_to_new_col(df, col, text, newcol):
    '''finds textstr in col of df, puts it into newcol'''
    if type(text) == str:
        df[newcol] = df[col].apply(
            lambda x: str(x) if text in str(x) else np.nan)
    elif type(text) == list:
        df[newcol] = df[col].apply(
            lambda x: str(x) if str(x) in text else np.nan)
    return df


def filter_numerics(df, col, inverse=False):
    def try_numeric_filt(string):
        try:
            return float(string)
        except:
            return (string)

    df[col] = df[col].apply(lambda x: try_numeric_filt(x))
    if not inverse:
        df = df[pd.to_numeric(df[col], errors='coerce').notnull()]
    elif inverse:
        df = df[~pd.to_numeric(df[col], errors='coerce').notnull()]
    return df


def shiftcol(df, col, steps):
    '''shifts column by number of steps'''
    df[col] = df[col].shift(steps)
    return df


def inlist(df, col, filtlist, inverse=False):
    '''FILTERS OUT ROWS WHERE ROW OF COL IN DF IS NOT A MONTH'''
    if inverse:
        df = df[df[col].isin(filtlist)]
    elif not inverse:
        df = df[~df[col].isin(filtlist)]
    return df


def add_normalization(df, numerator, denominator, replacecolstr, newcolstr, replacefrom='numerator',
                      factor=1, ):  # todo: handle inf and nans
    '''takes df and list or string of numerators/denominators (one has to be a single value),
    adds new columns to dataframe based on replacecolstr, newcolstr'''

    if replacefrom == 'numerator':
        newcolstr = df[numerator].name.replace(replacecolstr, newcolstr)

    elif replacefrom == 'denominator':
        newcolstr = df[denominator].name.replace(replacecolstr, newcolstr)

    df[newcolstr] = (df[numerator].astype(float) /
                     df[denominator].astype(float)) * factor
    # df[newcolstr] = df[newcolstr].apply(lambda x: x.replace(np.inf,0))
    return df


class RptHandler:
    '''container for customized report dataframes, can pass on various metadata
    into it (zone/volume, etc) and transformation methods'''

    def __init__(self, path):
        self.path = path
        self.plot = SimPlot(self)  # exposes 'plot.py' for Sim files

        def _sim_to_text_dict(self):
            '''parses sim file, returns dictionary of tables and sub tables'''
            with open(self.path) as f:
                fstr = f.read()
            fstr = fstr + '\f'
            rpt_text = re.findall(r'(REPORT.*?\f)', fstr, re.DOTALL)

            # handle tables
            rptdict = {}
            for r in rpt_text:
                report = re.findall("REPORT-.*WEATHER", r)[0]

                report = report.replace(
                    "REPORT- ", "").replace("WEATHER", "").strip()

                # handle special parse cases

                if "DESIGN DAY" in report:
                    top = re.split(r'\s{2,}', report)[0] + ' (DESIGN DAY)'
                    try:
                        bottom = re.split(r'\s{2,}', report)[1]
                        if bottom == "":
                            bottom = 'None'
                    except:
                        bottom = 'None'

                elif "LS-J Daylight Illuminance Frequency" in report:
                    top = "LS-J Daylight Illuminance Frequency"
                    bottom = report.replace((top + " "), "")

                elif "LS-M Daylight Illuminance Ref Pnt 1" in report:
                    top = "LS-M Daylight Illuminance Ref Pnt 1"
                    bottom = report.replace((top + " "), "")

                elif "SS-P Heating Performance Summary of" in report:
                    top = "SS-P Heating Performance Summary of"
                    bottom = report.replace((top + " "), "")

                elif "SS-P Cooling Performance Summary of" in report:
                    top = "SS-P Cooling Performance Summary of"
                    bottom = report.replace((top + " "), "")
                elif "SS-Q Heat Pump Cooling Summary for" in report:
                    top = "SS-Q Heat Pump Cooling Summary for"
                    bottom = report.replace((top + " "), "")

                elif "SS-Q Heat Pump Heating Summary for" in report:
                    top = "SS-Q Heat Pump Heating Summary for"
                    bottom = report.replace((top + " "), "")

                else:
                    top = re.split(r'\s{2,}', report)[0]
                    try:
                        bottom = re.split(r'\s{2,}', report)[1]
                        if bottom == "":
                            bottom = 'None'
                    except:
                        bottom = 'None'
                # rptdata = r.split("\n")[3:] # changed on 2020-01-30 for lv-d
                rptdata = r.split("\n")[2:]
                # populate dictionaries
                if top not in rptdict:
                    rptdict[top] = {bottom: rptdata}

                else:
                    if bottom in rptdict[top]:
                        rptdict[top][bottom] = rptdict[top][bottom] + rptdata
                    else:
                        rptdict[top].update({bottom: rptdata})
            return rptdict

        self.txtdict = _sim_to_text_dict(self)

    def _make_dirty_rpt_list(self, report):
        '''
        takes either full report or simplified, without hyphen:
        LV-C Details of Space is accessible via LV-C, LVC, lfc, or
        LV-C Details of Space
        returns dirty list
        '''
        rptlist = [key for key in self.txtdict.keys()]
        for rpt in rptlist:
            find = report.replace("-", "").upper()
            rpt_fmt = rpt.replace("-", "").upper()
            pattern = "^" + find + ".*"

            match = re.search(pattern, rpt_fmt)
            if match:
                return self.txtdict[rpt]

    def _make_dirty_rpt_df(self, rptname, colpat, colnames=None, fullname=None):
        '''
        takes rpt list and
        returns df with column pattern and column length.
        rpt_ref used in case name of report generated
        is different from sim name. ex: 'unmet' is
        taken from 'beps'report;
        'rpt' = unmet, rpt_ref = 'beps'
        '''
        txtlist = self._make_dirty_rpt_list(rptname)
        poslist = [i for i, letter in enumerate(colpat) if letter == '%']

        dflist = []
        for key, value in txtlist.items():  #
            collist = []
            this_row = []
            for row in value:
                this_row = []
                for num in range(len(poslist)):
                    try:
                        this_row_col = row[poslist[num]                                           :poslist[num + 1]].strip()
                        this_row.append(this_row_col)
                    except:
                        pass
                this_row = [x if len(x) > 0 else np.nan for x in this_row]
                collist.append(this_row)
            if colnames is not None:
                df = pd.DataFrame(collist, columns=colnames)
            df = df.dropna(how='all')
            df['Object'] = key

            #     return df
            dflist.append(df)

        df_concat = pd.concat(dflist)
        if fullname is not None:
            df_concat.index.name = fullname
        df_concat = df_concat.apply(pd.to_numeric, errors='ignore')
        return df_concat

    def _make_dirty_rpt_df_large_num_reports(self, rptname, colpat, colnames=None, fullname=None):
        '''
        takes rpt list and
        returns df with column pattern and column length.
        rpt_ref used in case name of report generated
        is different from sim name. ex: 'unmet' is
        taken from 'beps'report;
        'rpt' = unmet, rpt_ref = 'beps'
        '''
        rptlist = [key for key in self.txtdict.keys()]
        for rpt in rptlist:
            find = rptname.replace("-", "").upper()
            rpt_fmt = rpt.replace("-", "").upper()
            pattern = "^" + find + ".*"
            match = re.search(pattern, rpt_fmt)
            if match:
                rpt_dict = self.txtdict[rpt]
        poslist = [i for i, letter in enumerate(colpat) if letter == '%']
        pos_startlist = [i for i, letter in enumerate(colpat) if letter == '%']
        pos_endlist = [i + 1 for i in pos_startlist]
        pos_endlist.append(pos_endlist[-1] + 1)

        rpt_dict = {key: [line for line in val if len(
            line) >= pos_endlist[-1]-1] for key, val in rpt_dict.items()}
        return rpt_dict

        df_concat = pd.concat(dflist)
        if fullname is not None:
            df_concat.index.name = fullname
        df_concat = df_concat.apply(pd.to_numeric, errors='ignore')
        return df_concat

    # report dataframes

    def lvd(self):
        lvd_cols = ['Surface',
                    'Window U-Val',
                    'Window Area',
                    'Wall U-Val',
                    'Wall Area',
                    'Wall+Win U-Val',
                    'Wall+Window Area',
                    'Azimuth']
        lvd_col_pat = '%                                  - - % W I N D O W%S - - -    % - - - W A L % - - - -   %W A L L + W I % D O W S- %          %'
        lvd_full_name = 'LV-D Details of Exterior Surfaces'
        lvd = self._make_dirty_rpt_df(
            'lvd', lvd_col_pat, lvd_cols, lvd_full_name)
        lvd = str_to_new_col(lvd, 'Surface', 'in space', 'Space')
        lvd = shiftcol(lvd, 'Space', -1)
        lvd = filter_numerics(lvd, 'Window U-Val')
        lvd = filter_numerics(lvd, 'Azimuth', inverse=True)
        lvd['Space'] = lvd['Space'].apply(
            lambda x: str(x).replace("in space: ", ""))
        lvd['File'] = self.path
        lvd = try_numeric(lvd)
        return lvd

    def psf(self, leedpivot=False):

        # psf_col_pat = '%            %------  %------  %------  %------  %------  %------  %------  %------  %------  %------  %------  %------  %------%'

        # KWH           412983.       0.  303023.   23531.  222225.   68337.  198567. 1086346.  169060.       0.       0.   23170.

        psf_col_pat = '%            %------  %------  %------  %------  %------  %------  %------  %------  %------  %------  %------  %------  %------  %'
        psf_cols = ['Value',
                    'Lights',
                    'Task Lights',
                    'Misc Equip',
                    'Space Heating',
                    'Space Cooling',
                    'Heat Reject',
                    'Pumps & Aux',
                    'Vent Fans',
                    'Refrig Display',
                    'Ht Pump Supplem',
                    'Domest Hot Wtr',
                    'Ext Usage',
                    'Total']

        psf_full_name = 'PS-F Energy End-Use Summary for'
        psf = self._make_dirty_rpt_df(
            'psf', psf_col_pat, psf_cols, psf_full_name)

        psf = str_to_new_col(psf, 'Value', months, 'Month')
        psf = psf.reset_index(drop=True)

        psf['Month'] = psf['Month'].fillna(method='ffill')

        psf = filter_numerics(psf, 'Lights', inverse=False)
        psf = inlist(psf, 'Value', ['PEAK ENDUSE', 'PEAK PCT'])
        psf = psf.reset_index(drop=True)
        psf['Cons_Demand'] = psf['Value'].apply(
            lambda x: "Demand" if "MAX" in x else "Consumption")
        psf['File'] = self.path
        psf = try_numeric(psf)

        # handle 'totals' being set to 'december'.
        objlist = list(set((psf['Object'].values)))
        for obj in objlist:
            dec_total_consumption = (
                psf[(psf['Object'] == obj) & (psf['Cons_Demand'] == 'Consumption') & (psf['Month'] == 'DEC')])
            dec_total_demand = (
                psf[(psf['Object'] == obj) & (psf['Cons_Demand'] == 'Demand') & (psf['Month'] == 'DEC')])
            try:
                idx_consumption = dec_total_consumption.index[1]
                idx_demand = dec_total_demand.index[1]
                psf = psf.drop(idx_consumption, axis=0)
                psf = psf.drop(idx_demand, axis=0)
            except:
                pass

        psf = try_numeric(psf)

        if leedpivot:
            demand = psf[psf['Cons_Demand'] ==
                         'Demand'].groupby('Object').max().T
            consumption = psf[psf['Cons_Demand'] ==
                              'Consumption'].groupby('Object').sum().T
            merged = pd.concat([consumption, demand], axis=1, sort=False, keys=[
                               'Consumption', 'Demand']).dropna(how='any')
            return merged

        else:
            return psf

    def ssr(self):
        ssr_col_pat = '%---------------  %------ %------- %------- %-------      %---  %---  %---  %---  %---  %---  %---  %---  %---  %---  %---  %--%'
        ssr_cols = ['ZONE',
                    'ZONE OF MAXIMUM HTG DEMAND (HOURS)',
                    'ZONE OF MAXIMUM CLG DEMAND (HOURS)',
                    'ZONE UNDER HEATED HOURS',
                    'ZONE UNDER COOLED HOURS',
                    '0%-10%',
                    '10%-20%',
                    '20%-30%',
                    '30%-40%',
                    '40%-50%',
                    '50%-60%',
                    '60%-70%',
                    '70%-80%',
                    '80%-90%',
                    '90%-100%',
                    '100+%',
                    ' TOTAL RUN HOURS']

        ssr_full_name = 'SS-R Zone Performance Summary for'
        ssr = self._make_dirty_rpt_df(
            'ssr', ssr_col_pat, ssr_cols, ssr_full_name)
        ssr = ssr.reset_index(drop=True)
        ssr['zoneconcat'] = ssr['ZONE'] + \
            ssr['ZONE OF MAXIMUM HTG DEMAND (HOURS)'].apply(lambda x: str(x))
        ssr = shiftcol(ssr, 'zoneconcat', 1)
        ssr = ssr.loc[ssr['zoneconcat'].notnull(), :]
        ssr['ZONE'] = ssr['zoneconcat'].apply(lambda x: x.replace("nan", ""))
        ssr = ssr.drop('zoneconcat', axis=1)
        ssr = ssr.loc[ssr['ZONE OF MAXIMUM HTG DEMAND (HOURS)'].notnull(), :]
        exclude = ['ZONE(HOURS)', 'TOTAL', '---']
        ssr = inlist(ssr, 'ZONE', exclude, inverse=False)
        ssr = inlist(ssr, 'ZONE OF MAXIMUM HTG DEMAND (HOURS)',
                     ['ZONE OF'], inverse=False)
        ssr = ssr.loc[ssr['ZONE OF MAXIMUM CLG DEMAND (HOURS)'].notnull(), :]
        ssr['File'] = self.path

        ssr = try_numeric(ssr)

        return ssr

    def ssl(self):
        ssl_col_pat = '%-----  %------------%-----------%-----------%-----------%   ----% ----% ----% ----% ----% ----% ----% ----% ----% ----% ----% -----%'
        ssl_cols = ['MONTH',
                    'FAN ELEC DURING HEATING (KWH)',
                    'FAN ELEC DURING COOLING (KWH)',
                    'FAN ELEC DURING HEAT & COOL KWH)',
                    'FAN ELEC DURING FLOATING (KWH)',
                    '0%-10%',
                    '10%-20%',
                    '20%-30%',
                    '30%-40%',
                    '40%-50%',
                    '50%-60%',
                    '60%-70%',
                    '70%-80%',
                    '80%-90%',
                    '90%-100%',
                    '100+%',
                    ' TOTAL RUN HOURS']

        ssl_full_name = 'SS-R Zone Performance Summary for'
        ssl = self._make_dirty_rpt_df(
            'ssl', ssl_col_pat, ssl_cols, ssl_full_name)

        ssl = ssl.reset_index(drop=True)
        isinlist = [
            'JAN',
            'FEB',
            'MAR',
            'APR',
            'MAY',
            'JUN',
            'JUL',
            'AUG',
            'SEP',
            'OCT',
            'NOV',
            'DEC',
        ]

        ssl['File'] = self.path
        ssl = ssl[ssl.MONTH.isin(isinlist)]

        ssl = try_numeric(ssl)
        ssl = ssl.set_index('MONTH', drop=True)
        ssl = try_numeric(ssl)

        # total fan from detailed simulation reports summary, for convenience
        ssl['Total Fan'] = ssl['FAN ELEC DURING HEATING (KWH)'] + ssl['FAN ELEC DURING COOLING (KWH)'] + \
            ssl['FAN ELEC DURING FLOATING (KWH)'] - \
            ssl['FAN ELEC DURING HEAT & COOL KWH)']
        return ssl

    def psh(self):
        '              MON  PEAK   (KBTU/HR)   (KBTU/HR)   (KBTU/HR)   (KBTU/HR)       10    20    30    40    50    60    70    80    90   100    +  HOURS'
        psh_col_pat = '%--  %---  %-------  %-------  ---%---  %-------  %------%    %---  %---  %---  %---  %---  %---  %---  %---  %---  %---  %---  %--%'
        psh_cols = ['MONTH',
                    'SUM/PEAK',
                    'HEAT LOAD (MBTU) (KBTU/HR)',
                    'COOL LOAD (MBTU) (KBTU/HR)',
                    'PIPE GAIN (MBTU) (KBTU/HR)',
                    'NET LOAD (MBTU) (KBTU/HR)',
                    'OVER LOAD (MBTU) (KBTU/HR)',
                    'MEASUREMENT TYPE',
                    '0%-10%',
                    '10%-20%',
                    '20%-30%',
                    '30%-40%',
                    '40%-50%',
                    '50%-60%',
                    '60%-70%',
                    '70%-80%',
                    '80%-90%',
                    '90%-100%',
                    '100+%',
                    ' TOTAL RUN HOURS']

        psh_full_name = 'PS-H Loads and Energy Usage for'
        psh = self._make_dirty_rpt_df(
            'psh', psh_col_pat, psh_cols, psh_full_name)
        psh['MONTH'] = psh['MONTH'].apply(lambda x: str(x))
        psh = str_to_new_col(psh, 'MONTH', months, 'MONTHNEW')
        psh['MONTHNEW'] = psh['MONTHNEW'].fillna(method='ffill')
        psh['MONTH'] = psh['MONTHNEW']
        psh = psh.drop('MONTHNEW', axis=1)
        psh = filter_numerics(psh, '40%-50%')
        psh = inlist(psh, 'MONTH', months, inverse=True)
        psh['File'] = self.path
        psh = try_numeric(psh)
        return psh

    def lvb(self):
        lvb_col_pat = '%PACE                         MULTIP%IER  %YPE % AZIM %SQFT ) %EOPLE  %QFT )%      METHOD % ACH   % (SQFT )   %  (CUFT %'
        lvb_cols = ['SPACE',
                    'SPACE*FLOOR MULTIPLIER',
                    'SPACE TYPE',
                    'AZIM',
                    'LIGHTS (W/SF)',
                    'PEOPLE',
                    'EQUIP (W/SF)',
                    'INFILTRATION METHOD',
                    'ACH',
                    'AREA (SQ FT)',
                    'VOLUME (CU FT)']

        lvb_full_name = 'LV-B Summary of Spaces'
        lvb = self._make_dirty_rpt_df(
            'lvb', lvb_col_pat, lvb_cols, lvb_full_name)
        lvb = lvb.loc[lvb['SPACE*FLOOR MULTIPLIER'].notnull(), :]
        lvb = filter_numerics(lvb, 'SPACE*FLOOR MULTIPLIER')
        lvb['File'] = self.path
        lvb = try_numeric(lvb)
        return lvb

    def bepu(self):  # value       lights     task       eq      htg     clg      ht      pumps     fans      ref     ht p      dhw      ext      total
        # bepu_col_pat = '%           %---------  %------%  ------  %------%  ------  %------% ------%   ------  %------  % -----   %------  %-----%  -------%'

        bepu_col_pat = '%           %----------%------%  ------ %--------%  ------ %------% ------ %   -----%------  % -----  %------  %------  %  -------%'

        bepu_cols = ['Value',
                     'Lights',
                     'Task Lights',
                     'Misc Equip',
                     'Space Heating',
                     'Space Cooling',
                     'Heat Reject',
                     'Pumps & Aux',
                     'Vent Fans',
                     'Refrig Display',
                     'Ht Pump Supplem',
                     'Domest Hot Wtr',
                     'Ext Usage',
                     'Total']

        bepu_full_name = 'BEPU Building Utility Performance'
        bepu = self._make_dirty_rpt_df(
            'bepu', bepu_col_pat, bepu_cols, bepu_full_name)

        def concatmeter(x):
            if str(x['Lights']) == 'nan':
                return x['Value']
            else:
                return str(x['Value']).strip() + str(x['Lights']).strip()

        bepu['Meter'] = bepu.apply(lambda x: concatmeter(x), axis=1)

        bepu.index = bepu['Meter']
        bepu = shiftcol(bepu, 'Meter', 1)

        # bepu = bepu.drop('Meter', axis=1)
        bepu['Object'] = "Building"
        bepu['File'] = self.path
        bepu = bepu.dropna(how='any', axis=0)

        def get_utils(series):
            utilcols = []
            for s in series:
                if "ELECTRICITY" in s:
                    utilcols.append('Electricity')
                if "NATURAL-GAS" in s:
                    utilcols.append('Natural-Gas')
                if "STEAM" in s:
                    utilcols.append('Steam')
                if "CHILLED" in s:
                    utilcols.append('Chilled-Water')
            return utilcols

        bepu['Utility'] = get_utils(bepu.index)

        bepu = try_numeric(bepu)

        bepu = bepu[[

            'File',
            'Meter',
            'Utility',
            'Value',
            'Lights',
            'Task Lights',
            'Misc Equip',
            'Space Heating',
            'Space Cooling',
            'Heat Reject',
            'Pumps & Aux',
            'Vent Fans',
            'Refrig Display',
            'Ht Pump Supplem',
            'Domest Hot Wtr',
            'Ext Usage',
            'Total'
        ]]

        return bepu

    def unmet(self):
        unmetlist = self._make_dirty_rpt_list('beps')
        unmetlist = [[y.strip() for y in x.split("=")] for x in unmetlist['None']
                     if "COOLING THROTTLING RANGE" in x or "HEATING THROTTLING RANGE" in x]
        ssr = self.ssr()

        unmet_df = pd.DataFrame(unmetlist)

        heat_ssr = ssr.sort_values(
            'ZONE UNDER HEATED HOURS', ascending=False).iloc[0:10, :]
        cool_ssr = ssr.sort_values(
            'ZONE UNDER COOLED HOURS', ascending=False).iloc[0:10, :]
        unmet_df.columns = ['UNMET SUMMARY', 'Hours']
        unmet_df.index = unmet_df['UNMET SUMMARY']
        unmet_df = pd.DataFrame(unmet_df['Hours'])
        unmet_df

        cool_ssr.index = cool_ssr['ZONE']
        cool_ssr.index.name = 'SORTED BY COOLING'
        cool_ssr.drop('ZONE', axis=1, inplace=True)
        cool_ssr

        heat_ssr.index = heat_ssr['ZONE']
        heat_ssr.index.name = 'SORTED BY HEATING'
        heat_ssr.drop('ZONE', axis=1, inplace=True)
        heat_ssr

        return unmet_df, cool_ssr, heat_ssr

    def beps(self):
        beps_col_pat = '%            %-------  %------  %------ %-------  %------  %------  %------  %------  %------  %------  %------  %------  %------%'
        beps_cols = ['Value',
                     'Lights',
                     'Task Lights',
                     'Misc Equip',
                     'Space Heating',
                     'Space Cooling',
                     'Heat Reject',
                     'Pumps & Aux',
                     'Vent Fans',
                     'Refrig Display',
                     'Ht Pump Supplem',
                     'Domest Hot Wtr',
                     'Ext Usage',
                     'Total']

        def concatmeter(x):
            if str(x['Lights']) == 'nan':
                return x['Value']
            else:
                return str(x['Value']).strip() + str(x['Lights']).strip()

        beps_full_name = 'BEPS Building Energy Performance'
        beps = self._make_dirty_rpt_df(
            'beps', beps_col_pat, beps_cols, beps_full_name)
        beps['Meter'] = beps.apply(lambda x: concatmeter(x), axis=1)

        beps = shiftcol(beps, 'Meter', 1)

        beps = beps.dropna(how='any', axis=0)

        beps.index = beps['Meter']

        # beps = beps.drop('meterconcat', axis=1)
        beps['Object'] = "Building"

        beps['File'] = self.path

        beps['Value'] = 'MMBTU'

        beps = beps.loc[[s for s in beps.index if 'nan==' not in s]]

        def get_utils(series):
            utilcols = []
            for s in series:
                if "ELECTRICITY" in s:
                    utilcols.append('Electricity')
                if "NATURAL-GAS" in s:
                    utilcols.append('Natural-Gas')
                if "STEAM" in s:
                    utilcols.append('Steam')
                if "CHILLED" in s:
                    utilcols.append('Chilled-Water')
            return utilcols

        beps = try_numeric(beps)
        beps['Utility'] = get_utils(beps.index)

        beps = beps[[

            'File',
            'Meter',
            'Utility',
            'Value',
            'Lights',
            'Task Lights',
            'Misc Equip',
            'Space Heating',
            'Space Cooling',
            'Heat Reject',
            'Pumps & Aux',
            'Vent Fans',
            'Refrig Display',
            'Ht Pump Supplem',
            'Domest Hot Wtr',
            'Ext Usage',
            'Total'
        ]]

        return beps

    def ssg(self, keepcols=True):
        ssa_col_pat = '%    %  -COOLING  %  T%ME % DRY-% WET- %     COOLING    %   HEATING %   %IME % DRY- %WET- %     HEATING %      TRICAL  %    ELE%'

        ssg_col_pat = '%AN  %   0.00000 % 31 %24 % 35.F %31.F  %      0.000    %    -1.250%  19 %10 % 13.F %10.F %      -5.109 %        376.  %   0.66%'

        ssg_cols = [
            'Month',
            'Cooling Energy (MMBtu)',
            'Cooling Time Of Max Dy',
            'Cooling Time Of Max Hr',
            'Cooling Drybulb Temp',
            'Cooling Wetbulb Temp',
            'Maximum Cooling Load (kBtu/Hr)',
            'Heating Energy (MMBtu)',
            'Heating Time Of Max Dy',
            'Heating Time Of Max Hr',
            'Heating Drybulb Temp',
            'Heating Wetbulb Temp',
            'Maximum Heating Load (kBtu/Hr)',
            'Electrical Energy (kWh)',
            'Maximum Elec Load, kW']

        ssg_full_name = 'SS-A System Loads Summary for'
        ssg = self._make_dirty_rpt_df(
            'ssg', ssg_col_pat, ssg_cols, ssg_full_name)

        # return ssg
        ssg = inlist(ssg, "Month", months, inverse=True)
        ssg['File'] = self.path

        keepcols = [
            'Month',
            'Cooling Energy (MMBtu)',
            'Maximum Cooling Load (kBtu/Hr)',
            'Heating Energy (MMBtu)',
            'Maximum Heating Load (kBtu/Hr)',
            'Electrical Energy (kWh)',
            'Maximum Elec Load, kW',
            'File',
            'Object'
        ]
        if keepcols:
            ssg = ssg[keepcols]

        ssg = try_numeric(ssg)

        return ssg

    def ssa(self, keepcols=True):
        ssa_col_pat = '%    %  -COOLING  %  T%ME % DRY-% WET- %     COOLING    %   HEATING %   %IME % DRY- %WET- %     HEATING %      TRICAL  %    ELE%'
        ssa_cols = [
            'Month',
            'Cooling Energy (MMBtu)',
            'Cooling Time Of Max Dy',
            'Cooling Time Of Max Hr',
            'Cooling Drybulb Temp',
            'Cooling Wetbulb Temp',
            'Maximum Cooling Load (kBtu/Hr)',
            'Heating Energy (MMBtu)',
            'Heating Time Of Max Dy',
            'Heating Time Of Max Hr',
            'Heating Drybulb Temp',
            'Heating Wetbulb Temp',
            'Maximum Heating Load (kBtu/Hr)',
            'Electrical Energy (kWh)',
            'Maximum Elec Load, kW']

        ssa_full_name = 'SS-A System Loads Summary for'
        ssa = self._make_dirty_rpt_df(
            'ssa', ssa_col_pat, ssa_cols, ssa_full_name)
        ssa = inlist(ssa, "Month", months, inverse=True)
        ssa['File'] = self.path

        keepcols = [
            'Month',
            'Cooling Energy (MMBtu)',
            'Maximum Cooling Load (kBtu/Hr)',
            'Heating Energy (MMBtu)',
            'Maximum Heating Load (kBtu/Hr)',
            'Electrical Energy (kWh)',
            'Maximum Elec Load, kW',
            'File',
            'Object'
        ]
        if keepcols:
            ssa = ssa[keepcols]

        ssa = try_numeric(ssa)

        return ssa

    def ssb(self, keepcols=True):
        ssb_col_pat = '%ONTH%       (MBTU)%     (KBTU/HR)%        (MBTU)%     (KBTU/HR)%        (MBTU)%     (KBTU/HR)%        (MBTU)%     (KBTU/HR%'
        ssb_cols = [
            'Month',
            'Cooling By Zone Coils Or Nat Ventilation (MMBtu)',
            'Max Cooling By Zone Coils or Nat VEntilation (kBtu/hr)',
            'Heating By Zone Coils or Furnace (MMBtu)',
            'Max Heating by Zone Coils or Furnace (kBTu/hr)',
            'Baseboard Heating Energy (MMBtu)',
            'Max Baseboard Heating Energy (kBtu/hr)',
            'Preheat Coil Energy or Elec for Furn Fan (MMBtu)',
            'Max Preheat Coil Energy or Elec for Furn Fan (kBtu/hr)'
        ]

        ssb_full_name = 'SS-B System Loads Summary for'
        ssb = self._make_dirty_rpt_df(
            'ssb', ssb_col_pat, ssb_cols, ssb_full_name)
        ssb = inlist(ssb, "Month", months, inverse=True)
        ssb['File'] = self.path

        keepcols = [
            'Month',
            'Cooling By Zone Coils Or Nat Ventilation (MMBtu)',
            'Max Cooling By Zone Coils or Nat VEntilation (kBtu/hr)',
            'Heating By Zone Coils or Furnace (MMBtu)',
            'Max Heating by Zone Coils or Furnace (kBTu/hr)',
            'Baseboard Heating Energy (MMBtu)',
            'Max Baseboard Heating Energy (kBtu/hr)',
            'Preheat Coil Energy or Elec for Furn Fan (MMBtu)',
            'Max Preheat Coil Energy or Elec for Furn Fan (kBtu/hr)',
            'File',
            'Object'
        ]
        if keepcols:
            ssb = ssb[keepcols]

        ssb = try_numeric(ssb)

        return ssb

    def ese(self):
        ese_col_pat = '%----  %-------  %-------  %-------  %-------  %------  %------  %------  %------  %------  %------  %------  %------  %------%'
        ese_cols = [
            'Month',
            'METERED ENERGY (KWH)',
            'BILLING ENERGY (KWH)',
            'METERED DEMAND (KW)',
            'BILLING DEMAND (KW)',
            'ENERGY CHARGE ($)',
            'DEMAND CHARGE ($)',
            'ENERGY CST ADJ ($)',
            'TAXES($)',
            'SURCHG($)',
            'FIXED CHARGE($)',
            'MINIMUM CHARGE($)',
            'VIRTUAL RATE ($/UNIT)',
            'TOTAL CHARGE ($)']

        ese_full_name = 'ES-E Summary of Utility-Rate:'
        ese = self._make_dirty_rpt_df(
            'ese', ese_col_pat, ese_cols, ese_full_name)
        ese = inlist(ese, "Month", months, inverse=True)
        ese['File'] = self.path

        # handle meters

        ratelist = self._make_dirty_rpt_list("ese")

        ratedict = {}
        for key, value in ratelist.items():
            ratelist = ([re.findall("METERS\:.*", line, re.DOTALL)
                         for line in value])
            ratelist = [rate[0] for rate in ratelist if len(rate) > 0][0]
            ratelist = re.split(r'\s{2,}', ratelist)[1:]
            ratelist = [rate for rate in ratelist if len(rate) > 0]
            ratedict[key] = ratelist

        ese['Meters'] = ese['Object'].apply(lambda x: ratedict[x])
        return try_numeric(ese)

    def ratedict(self):
        ratelist = self._make_dirty_rpt_list("ese")
        ratedict = {}
        for key, value in ratelist.items():
            ratelist = ([re.findall("METERS\:.*", line, re.DOTALL)
                         for line in value])
            ratelist = [rate[0] for rate in ratelist if len(rate) > 0][0]
            ratelist = re.split(r'\s{2,}', ratelist)[1:]
            ratelist = [rate for rate in ratelist if len(rate) > 0]
            for rate in ratelist:
                ratedict[rate] = key
        return ratedict

    def lsb(self='self'):
        lsb_col_pat = '%                           %-------   % -----  %------- % -----                     %-------  %------%'
        lsb_cols = ['Nothing',
                    'LOAD COMPONENT',
                    'COOLING SENSIBLE KBTU/H',
                    'COOLING SENSIBLE KW',
                    'COOLING LATENT KBTU/H',
                    'COOLING LATENT KW',
                    'HEATING SENSIBLE KBTU/H',
                    'HEATING SENSIBLE KW',
                    'Nothing',
                    'Space']

        lsb_full_name = 'LS-B Space Peak Load Components'

        lsb = self._make_dirty_rpt_df_large_num_reports(
            'lsb', lsb_col_pat, lsb_cols, lsb_full_name)  # todo bottleneck here

        dflist = []
        for key, val in lsb.items():
            lines = pd.DataFrame([re.split(r'\s{2,}', line.replace('LIGHT     TO SPACE', 'LIGHT TO SPACE').replace(
                'PROCESS   TO SPACE', 'PROCESS TO SPACE')) for line in val])
            lines['Object'] = key
            dflist.append(lines)

        lsb = pd.concat(dflist, axis=0)
        lsb = lsb.dropna(how='all', axis=1)
        lsb.columns = lsb_cols

        rowlist = ['WALL CONDUCTION',
                   'ROOF CONDUCTION',
                   'WINDOW GLASS+FRM COND',
                   'WINDOW GLASS SOLAR',
                   'DOOR CONDUCTION',
                   'INTERNAL SURFACE COND',
                   'UNDERGROUND SURF COND',
                   'OCCUPANTS TO SPACE',
                   'LIGHT TO SPACE',
                   'EQUIPMENT TO SPACE',
                   'PROCESS TO SPACE',
                   'INFILTRATION',
                   'TOTAL']

        lsb = inlist(lsb, 'LOAD COMPONENT', rowlist, inverse=True)
        lsb = try_numeric(lsb)
        lsb['File'] = self.path
        lsb['COOLING TOTAL KBTU/H'] = lsb['COOLING SENSIBLE KBTU/H'] + \
            lsb['COOLING LATENT KBTU/H']
        lsb['COOLING TOTAL KW'] = lsb['COOLING SENSIBLE KW'] + \
            lsb['COOLING LATENT KW']

        spaces = self.lvb()
        spaces = spaces[['SPACE', 'SPACE*FLOOR MULTIPLIER', 'AREA (SQ FT)']]
        lsb = lsb.merge(spaces, left_on='Space', right_on='SPACE')

        lsb['COOLING SENSIBLE BTUH/SF'] = (
            lsb['COOLING SENSIBLE KBTU/H'] * 1000) / lsb['AREA (SQ FT)']
        lsb['COOLING LATENT BTUH/SF'] = (lsb['COOLING LATENT KBTU/H']
                                         * 1000) / lsb['AREA (SQ FT)']
        lsb['COOLING TOTAL BTUH/SF'] = (lsb['COOLING TOTAL KBTU/H']
                                        * 1000) / lsb['AREA (SQ FT)']

        lsb['HEATING SENSIBLE BTUH/SF'] = (
            lsb['HEATING SENSIBLE KBTU/H'] * 1000) / lsb['AREA (SQ FT)']
        lsb = lsb.drop('Nothing', axis=1)
        lsb = lsb.drop('SPACE', axis=1)
        lsb = lsb.replace(np.inf, 0)
        lsb = lsb[lsb['LOAD COMPONENT'] != 'TOTAL']

        return lsb

    def lsd(self='self'):
        lsd_col_pat = '%ONTH%    (MBTU)%  DY% HR%  TEMP% TEMP%    (KBTU/HR)%        (MBTU)%  DY% HR%  TEMP% TEMP%    (KBTU/HR)%        (KWH)%      (KW)%'

        lsd_cols = [
            'MONTH',
            'COOLING ENERGY (MBTU)',
            'CLG TIME OF MAX - DY',
            'CLG - TIME OF MAX - HR',
            'CLG - DRY-BULB TEMP',
            'CLG - WET-BULB TEMP',
            'MAX COOLING LOAD (KBTU/HR)',
            'HEATING ENERGY (MBTU)',
            'HTG TIME OF MAX - DY',
            'HTG - TIME OF MAX - HR',
            'HTG - DRY-BULB TEMP',
            'HTG - WET-BULB TEMP',
            'MAX HEATING LOAD (KBTU/HR)',
            'ELECTRICAL ENERGY (KWH)',
            'MAX ELEC LOAD (KW)'
        ]

        lsd_full_name = 'LS-D Building Monthly Loads Summary'
        lsd = self._make_dirty_rpt_df(
            'lsd', lsd_col_pat, lsd_cols, lsd_full_name)

        lsd = lsd.dropna(how='any', axis=0)
        lsd = lsd[lsd.MONTH != 'MONTH']
        lsd = lsd.set_index('MONTH', drop=True)
        lsd.Object = 'Building'

        for col in lsd.columns:
            lsd[col] = lsd[col].apply(lambda x: x.replace('.F', ''))

        lsd = try_numeric(lsd)
        return lsd

    def ssd(self='self'):
        ssd_col_pat = '%ONTH%    (MBTU)%  DY% HR%  TEMP% TEMP%    (KBTU/HR)%        (MBTU)%  DY% HR%  TEMP% TEMP%    (KBTU/HR)%        (KWH)%      (KW)%'

        ssd_cols = [
            'MONTH',
            'COOLING ENERGY (MBTU)',
            'CLG TIME OF MAX - DY',
            'CLG - TIME OF MAX - HR',
            'CLG - DRY-BULB TEMP',
            'CLG - WET-BULB TEMP',
            'MAX COOLING LOAD (KBTU/HR)',
            'HEATING ENERGY (MBTU)',
            'HTG TIME OF MAX - DY',
            'HTG - TIME OF MAX - HR',
            'HTG - DRY-BULB TEMP',
            'HTG - WET-BULB TEMP',
            'MAX HEATING LOAD (KBTU/HR)',
            'ELECTRICAL ENERGY (KWH)',
            'MAX ELEC LOAD (KW)'
        ]

        ssd_full_name = 'SS-D Building HVAC Load Summary'
        ssd = self._make_dirty_rpt_df(
            'ssd', ssd_col_pat, ssd_cols, ssd_full_name)

        ssd = ssd.dropna(how='any', axis=0)
        ssd = ssd[ssd.MONTH != 'MONTH']
        ssd = ssd.set_index('MONTH', drop=True)
        ssd.Object = 'Building'

        for col in ssd.columns:
            ssd[col] = ssd[col].apply(lambda x: x.replace('.F', ''))

        ssd = try_numeric(ssd)
        return ssd

    def lse(self='self'):

        lse_col_pat = '%   %HEATNG %   0.000  %  0.000 %   0.000 %  -0.939  %  0.000  %  0.000  %  0.000  %  0.080  %  0.244   % 0.098  %  0.000  % -0.516%'

        lse_cols = ['MONTH', 'TYPE', 'WALLS', 'ROOFS', 'INTERIOR SURFACE', 'UNDERGROUND SURFACE', 'INFILTRATION',
                    'WINDOW CONDUCTION', 'WINDOW SOLAR', 'OCCUPANCY', 'LIGHTS', 'EQUIP', 'SOURCE', 'TOTAL']
        lse_full_name = 'LS-E Space Monthly Load Component'
        lse = self._make_dirty_rpt_df(
            'lse', lse_col_pat, lse_cols, lse_full_name)

        lse = filter_numerics(lse, 'TOTAL')
        lse = shiftcol(lse, 'MONTH', -1)
        lse['MONTH'] = lse['MONTH'].fillna(method='ffill')
        lse = lse.fillna(0)
        lse = lse.rename(columns={'Object': 'Space'})
        lse = try_numeric(lse)
        lse['File'] = self.path
        return lse

    def sva(self='self'):

        sva_dirty = self._make_dirty_rpt_list('sv-a')

        def find_between(s, first, last):
            try:
                start = s.index(first) + len(first)
                end = s.index(last, start)
                return s[start:end]
            except ValueError:
                return ""

        def find_between_r(s, first, last):
            try:
                start = s.rindex(first) + len(first)
                end = s.rindex(last, start)
                return s[start:end]
            except ValueError:
                return ""

        def getzones(svaobj):
            zonestartstring = '     NAME                     (CFM )    (CFM )      (KW)    (FRAC)    (CFM ) (KBTU/HR)    (FRAC) (KBTU/HR) (KBTU/HR) (KBTU/HR) MULT'
            write = False
            zonelist = []

            for line in svaobj:
                if write:
                    zonelist.append(line)
                if line == zonestartstring:
                    write = True

            zonesplit = [re.split(r'\s{2,}', x)
                         for x in zonelist if len(x) > 1]
            return pd.DataFrame(zonesplit)

        def getsys(svaobj):

            sysstartstring = 'TYPE     FACTOR    (SQFT )     PEOPLE      RATIO  (KBTU/HR)      (SHR)  (KBTU/HR)  (BTU/BTU)  (BTU/BTU)  (KBTU/HR)'
            sysendstring = '                     DIVERSITY    POWER       FAN     STATIC   TOTAL    MECH                         MAX FAN   MIN FAN'
            parsed = find_between_r(str(svaobj), sysstartstring, sysendstring)
            parsed = parsed.split(',')
            parsed = [x for x in parsed if len(x) > 3]
            parsed = re.split(r'\s{2,}', parsed[0])
            parsed = [x.replace('"', "").replace("'", "").strip()
                      for x in parsed]
            return parsed

        def getfans(svaobj):
            fanstartstring = '     TYPE    (CFM )     (FRAC)     (KW)       (F) (IN-WATER)  (FRAC)  (FRAC)   PLACEMENT   CONTROL    (FRAC)    (FRAC)'
            fanendstring = '                              SUPPLY   EXHAUST             MINIMUM   OUTSIDE   COOLING          EXTRACTION   HEATING  ADDITION'
            parsed = find_between_r(str(svaobj), fanstartstring, fanendstring)
            parsed = parsed.split(',')

            parsed = [x for x in parsed if len(x) > 3]

            supplyparse = re.split(r'\s{2,}', parsed[0])
            supplyparse = [x.replace('"', "").replace(
                "'", "").strip() for x in supplyparse]
            supplyparse = [x for x in supplyparse if len(x) > 0]

            if len(parsed) > 1:
                returnparse = re.split(r'\s{2,}', parsed[1])
                returnparse = [x.replace('"', "").replace(
                    "'", "").strip() for x in returnparse]
                returnparse = [x for x in returnparse if len(x) > 0]

            else:
                returnparse = ['0']*12

            fanconcat = supplyparse + returnparse
            return fanconcat

        sysdict = {}
        fandict = {}
        zonedict = {}

        for key in sva_dirty.keys():
            report = sva_dirty[key]
            zones = getzones(report)
            zonedict[key] = zones
            try:
                systems = getsys(report)
                sysdict[key] = systems
            except:
                print('Possible \'SUM\' system failure:')
                print(key)
            try:
                fans = getfans(report)
                fandict[key] = fans
            except:
                print('Possible \'SUM\' system failure:')
                print(key)

        def cleanspaces(obj):
            newdict = {}
            for k, v in obj.items():
                newitemlist = []
                for item in v:
                    if len(item.split(" ")) > 1:
                        newitemlist += item.split(" ")
                    else:
                        newitemlist.append(item)
                newdict[k] = newitemlist
            return newdict

        sysdf = try_numeric(pd.DataFrame(cleanspaces(sysdict)).T)
        fandf = try_numeric(pd.DataFrame(cleanspaces(fandict)).T)
        zonedf = try_numeric(pd.concat(zonedict).reset_index())

        zonedf = zonedf.set_index('level_0')
        zonedf = zonedf.drop('level_1', axis=1)

        sysinfostring = "System Type    Altitude Factor   Floor Area (sqft)   Max People   Outside Air Ratio   Cooling Capacity (kBTU/hr)   Sensible (SHR)   Heating Capacity (kBTU/hr)   Cooling EIR (BTU/BTU)   Heating EIR (BTU/BTU)   Heat Pump Supplemental Heat (kBTU/hr)"

        faninfostring = "Fan Type   Capacity (CFM)   Diversity Factor (FRAC)   Power Demand (kW)   Fan deltaT (F)   Static Pressure (in w.c.)   Total efficiency   Mechanical Efficiency   Fan Placement   Fan Control   Max Fan Ratio (Frac)   Min Fan Ratio (Frac)"

        zoneinfostring = "Zn Name   Supply Flow (CFM)   Exhaust Flow (CFM)   Fan (kW)   Minimum Flow (Frac)   Outside Air Flow (CFM)   Cooling Capacity (kBTU/hr)   Sensible (FRAC)   Extract Rate (kBTU/hr)   Heating Capacity (kBTU/hr)   Addition Rate (kBTU/hr)   Zone Mult"

        sysinfocols = [x.strip() for x in re.split(r'\s{2,}', sysinfostring)]
        supplyinfocols = ["Supply_" + x.strip()
                          for x in re.split(r'\s{2,}', faninfostring)]
        returninfocols = ["Return_" + x.strip()
                          for x in re.split(r'\s{2,}', faninfostring)]
        faninfocols = supplyinfocols + returninfocols
        zoneinfocols = [x.strip() for x in re.split(r'\s{2,}', zoneinfostring)]

        sysdf.columns = sysinfocols
        fandf.columns = faninfocols
        zonedf.index.name = 'System Name'
        zonedf.columns = zoneinfocols

        sysdf['File'] = self.path
        fandf['File'] = self.path
        zonedf['File'] = self.path

        sysdf['System'] = sysdf.index
        fandf['System'] = fandf.index
        zonedf['System'] = zonedf.index

        systemdf = pd.concat([sysdf, fandf], axis=1)

        return systemdf, zonedf

    def sspcool(self):
        sspcool = self._make_dirty_rpt_list('SS-P COOLING')
        sspcooldict = {}

        for k, v in sspcool.items():
            for num, line in enumerate(v):
                if "UNIT TYPE is" in line:
                    topline = v[num]

                if "YR" in line and "SUM" in line:
                    midline = v[num]
                    bottline = v[num+1]

            unittype = re.search(
                'UNIT TYPE is(.*)COOLING-CAPACITY', topline).group(1).strip()
            coolcap = re.search('COOLING-CAPACITY =(.*)KBTU/HR',
                                topline).group(1).replace("(", "").replace(")", "").strip()
            cooleir = re.search('COOLING-EIR =(.*)BTU/BTU',
                                topline).group(1).replace("(", "").replace(")", "").strip()
            supplyflow = re.search(
                'SUPPLY-FLOW =(.*)CFM', topline).group(1).replace("(", "").replace(")", "").strip()
            unitload_sum = re.split(r'\s{1,}', midline)[2]
            unitload_peak = re.split(r'\s{1,}', bottline)[2]
            energyuse_sum = re.split(r'\s{1,}', midline)[3]
            energyuse_peak = re.split(r'\s{1,}', bottline)[3]
            compressor_sum = re.split(r'\s{1,}', midline)[4]
            compressor_peak = re.split(r'\s{1,}', bottline)[3]
            fanenergy_sum = re.split(r'\s{1,}', midline)[5]
            fanenergy_peak = re.split(r'\s{1,}', bottline)[3]
            sspcooldict[k] = {
                'Unit Type': unittype,
                'Cooling Capacity (kBtu/hr)': coolcap,
                'Cooling EIR': cooleir,
                'Supply Flow (CFM)': supplyflow,
                'Unit Load Sum (MMBtu)': unitload_sum,
                'Unit Load Peak (kBtu/hr)': unitload_peak,
                'Energy Use Sum (kWh)': energyuse_sum,
                'Energy Use Peak (kW)': energyuse_peak,
                'Compressor Sum (kWh)': compressor_sum,
                'Compressor Peak (kW)': compressor_peak,
                'Fan Energy Sum (kWh)': fanenergy_sum,
                'Fan Energy Peak (kW)': fanenergy_peak
            }

        sspcooldf = try_numeric(pd.DataFrame(sspcooldict).T)
        sspcooldf['Object'] = sspcooldf.index
        sspcooldf['File'] = self.path
        sspcooldf['rptname'] = 'SSP_COOL'
        sspcooldf = sspcooldf.reset_index(drop=True)
        return sspcooldf

    def sspheat(self):
        sspheat = self._make_dirty_rpt_list('SS-P HEATING')

        sspheatdict = {}

        for k, v in sspheat.items():
            for num, line in enumerate(v):
                if "UNIT TYPE is" in line:
                    topline = v[num]

                if "YR" in line and "SUM" in line:
                    midline = v[num]
                    bottline = v[num+1]
            unittype = re.search(
                'UNIT TYPE is(.*)HEATING-CAPACITY', topline).group(1).strip()
            heatcap = re.search('HEATING-CAPACITY =(.*)KBTU/HR',
                                topline).group(1).replace("(", "").replace(")", "").strip()
            heateir = re.search('HEATING-EIR =(.*)BTU/BTU',
                                topline).group(1).replace("(", "").replace(")", "").strip()
            supplyflow = re.search(
                'SUPPLY-FLOW =(.*)CFM', topline).group(1).replace("(", "").replace(")", "").strip()
            unitload_sum = re.split(r'\s{1,}', midline)[2]
            unitload_peak = re.split(r'\s{1,}', bottline)[2]
            energyuse_sum = re.split(r'\s{1,}', midline)[3]
            energyuse_peak = re.split(r'\s{1,}', bottline)[3]
            compressor_sum = re.split(r'\s{1,}', midline)[4]
            compressor_peak = re.split(r'\s{1,}', bottline)[3]
            fanenergy_sum = re.split(r'\s{1,}', midline)[5]
            fanenergy_peak = re.split(r'\s{1,}', bottline)[3]
            sspheatdict[k] = {
                'Unit Type': unittype,
                'Heating Capacity (kBtu/hr)': heatcap,
                'Cooling EIR': heateir,
                'Supply Flow (CFM)': supplyflow,
                'Unit Load Sum (MMBtu)': unitload_sum,
                'Unit Load Peak (kBtu/hr)': unitload_peak,
                'Energy Use Sum (kWh)': energyuse_sum,
                'Energy Use Peak (kW)': energyuse_peak,
                'Compressor Sum (kWh)': compressor_sum,
                'Compressor Peak (kW)': compressor_peak,
                'Fan Energy Sum (kWh)': fanenergy_sum,
                'Fan Energy Peak (kW)': fanenergy_peak
            }

        sspheatdf = try_numeric(pd.DataFrame(sspheatdict).T)
        sspheatdf['Object'] = sspheatdf.index
        sspheatdf['File'] = self.path
        sspheatdf['rptname'] = 'SSP_HEAT'
        sspheatdf = sspheatdf.reset_index(drop=True)

        return sspheatdf

    def ssqcool(self):

        ssqcool = self._make_dirty_rpt_list('SS-Q HEAT PUMP COOLING')

        ssqcooldict = {}

        for k, v in ssqcool.items():
            for num, line in enumerate(v):
                if "ANNUAL" in line:
                    topline = v[num]
                if "CSPF (WITH PARASITICS)" in line:
                    midline = v[num]
                if "CSPF (WITHOUT PARASITICS)" in line:
                    bottomline = v[num]

            topsplit = re.split(r'\s{1,}', topline)

            unitruntime = topsplit[1]
            totalloadonunit = topsplit[2]
            energyintounit = topsplit[3]
            auxiliaryenergy = topsplit[4]
            supunitload = topsplit[5]
            supunitenergy = topsplit[6]
            wasteheatgen = topsplit[7]
            wasteheatuse = topsplit[8]
            unnamed = topsplit[9]
            indoorfanenergy = topsplit[10]
            cspfwithparasitics = midline.replace(
                'CSPF (WITH PARASITICS)    =', '').replace("(KBTU/HR)", "").strip()
            cspfwithoutparasitics = bottomline.replace(
                'CSPF (WITHOUT PARASITICS)    =', '').replace("(BTU/BTU)", "").strip()

            ssqcooldict[k] = {
                'Unit Run Time (Hours)': unitruntime,
                'Total Load On Unit (MBtu)': totalloadonunit,
                'Energy Into Unit (MBtu)': energyintounit,
                'Auxiliary Energy (MBtu)': auxiliaryenergy,
                'Sup Unit Load (MBtu)': supunitload,
                'Sup Unit Energy (MBtu)': supunitenergy,
                'Waste Heat Generated (MBtu)': wasteheatgen,
                'Waste Heat Use (MBtu)': wasteheatuse,
                'Unnamed': unnamed,
                'Indoor Fan Energy (MBtu)': indoorfanenergy,
                'CSPF (WITH PARASITICS)': cspfwithparasitics,
                'CSPF (WITHOUT PARASITICS)': cspfwithoutparasitics
            }

        ssqcooldf = try_numeric(pd.DataFrame(ssqcooldict).T)

        ssqcooldf['Object'] = ssqcooldf.index

        ssqcooldf['File'] = self.path

        ssqcooldf['rptname'] = 'SSQ_COOL'

        ssqcooldf = ssqcooldf.reset_index(drop=True)

        return ssqcooldf

    def ssqheat(self):

        ssqheat = self._make_dirty_rpt_list('SS-Q HEAT PUMP HEATING')

        ssqheatdict = {}

        for k, v in ssqheat.items():
            for num, line in enumerate(v):
                if "ANNUAL" in line:
                    topline = v[num]
                if "CSPF (WITH PARASITICS)" in line:
                    midline = v[num]
                if "CSPF (WITHOUT PARASITICS)" in line:
                    bottomline = v[num]

            topsplit = re.split(r'\s{1,}', topline)

            unitruntime = topsplit[1]
            totalloadonunit = topsplit[2]
            energyintounit = topsplit[3]
            auxiliaryenergy = topsplit[4]
            supunitload = topsplit[5]
            supunitenergy = topsplit[6]
            wasteheatgen = topsplit[7]
            wasteheatuse = topsplit[8]
            unnamed = topsplit[9]
            indoorfanenergy = topsplit[10]

            cspfwithparasitics = midline.replace('CSPF (WITH PARASITICS)', '').replace(
                "=", "").replace("(KBTU/HR)", "").strip()
            cspfwithoutparasitics = bottomline.replace(
                'CSPF (WITHOUT PARASITICS)', '').replace("=", "").replace("(BTU/BTU)", "").strip()

            ssqheatdict[k] = {
                'Unit Run Time (Hours)': unitruntime,
                'Total Load On Unit (MBtu)': totalloadonunit,
                'Energy Into Unit (MBtu)': energyintounit,
                'Auxiliary Energy (MBtu)': auxiliaryenergy,
                'Sup Unit Load (MBtu)': supunitload,
                'Sup Unit Energy (MBtu)': supunitenergy,
                'Waste Heat Generated (MBtu)': wasteheatgen,
                'Waste Heat Use (MBtu)': wasteheatuse,
                'Unnamed': unnamed,
                'Indoor Fan Energy (MBtu)': indoorfanenergy,
                'CSPF (WITH PARASITICS)': cspfwithparasitics,
                'CSPF (WITHOUT PARASITICS)': cspfwithoutparasitics

            }

        ssqheatdf = try_numeric(pd.DataFrame(ssqheatdict).T)
        ssqheatdf['Object'] = ssqheatdf.index
        ssqheatdf['File'] = self.path
        ssqheatdf['rptname'] = 'SSQ_HEAT'

        ssqheatdf = ssqheatdf.reset_index(drop=True)

        return ssqheatdf

    def hourly(self='self'):

        with open(self.path) as f:
            fstr = f.read()

        pages_raw = [x.split('\n') for x in fstr.split('\f')]
        pages_raw = [x for x in pages_raw if len(x) > 1]

        pages = [x for x in pages_raw if "HOURLY REPORT" in x[2]]

        hourlydict = {}
        for page in pages:
            columns = page[4:11]
            rows = page[11:35]

            spacingrow = columns[-1]

            # attempt to add delimeters by both "----( 7)" and "----302-". other conditions?
            spacingrow = spacingrow.replace(
                "----(", "%---(").replace("----", "%--(")

            poslist = [i for i, letter in enumerate(
                spacingrow) if letter == '%']
            poslist.append(len(spacingrow))

            # get columns
            parsed_cols = []
            for col in columns:
                parsed_col = []
                lastpos = poslist[0]
                for pos in poslist[1:]:
                    parsed_col.append(col[lastpos:pos].strip())
                    lastpos = pos
                parsed_cols.append(parsed_col)

            col_df_transposed = pd.DataFrame(parsed_cols).T.values
            cols = ['_'.join(x).replace('__', '_').replace(
                "----( ", "(") for x in col_df_transposed]

            # testing column parsing
            # if "ERV" in ''.join(cols):
            # print(cols[5:])

            # get data values and date index
            for row in rows:
                date = row[:6]

                rowsplit = re.split(r'\s{2,}', row)

                date = rowsplit[0]

                vals = rowsplit[1:]

                for num, val in enumerate(vals):
                    colname = cols[num]
                    if colname in hourlydict:
                        hourlydict[colname][date] = val
                    else:
                        hourlydict[colname] = {}
                        hourlydict[colname][date] = val

        df = pd.DataFrame.from_dict(hourlydict)
        df = try_numeric(df)

        df['dt'] = df.index

        df['dt'] = df['dt'].apply(lambda x: str(x).replace(' ', '0'))
        df['month'] = df['dt'].apply(lambda x: x[:2])
        df['day'] = df['dt'].apply(lambda x: x[2:4])
        df['hour'] = df['dt'].apply(lambda x: x[4:6])

        df['year'] = '2021'
        dtindex = pd.to_datetime(df[['year', 'month', 'day', 'hour']])

        df = df.set_index(dtindex)
        df = df.drop(['dt', 'year', 'month', 'day', 'hour'], axis=1)

        return df
