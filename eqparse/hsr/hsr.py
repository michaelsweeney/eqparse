'''
makes neat dataframe out of hsr hourly results file
'''
import pandas as pd
import numpy as np
import warnings
import re

try:
    from . import plot
    from plotly.offline import download_plotlyjs, init_notebook_mode, plot
except:
    pass

from . import unit_dict


class hsr_df:
    '''hsr dataframe object.'''

    def __init__(self, hsrfile, getunits=True, multicol=True, show_warnings=False):
        self.df = make_df(hsrfile, getunits=getunits, multicol=multicol)
        self.name = str(hsrfile).split("\\")[-1].replace(": ]", "")
        self.path = str(hsrfile)
        self.units = [x[-1] for x in self.df.columns]

        def make_legend(self, long=True):
            tuplist = [x[-3:-1] for x in self.df.columns]
            tuplist = [[str(y) for y in x] for x in tuplist]

            if long:
                col_list = [self.name.replace(
                    ".hsr", "") + ", " + x[0] + ", " + x[1] for x in tuplist]
            else:
                col_list = [x[0] + ", " + x[1] for x in tuplist]
            return col_list

        def make_cols(self, long=True):
            if long:
                cols = [list(x) for x in self.df.columns]
                cols = [[str(y) for y in x] for x in cols]
                [col.insert(0, self.name.replace(".hsr", "")) for col in cols]

                cols = [', '.join(col) for col in cols]
                cols = [x[1:] if x[0] == '/' else x for x in cols]
                return cols
            else:
                cols = [list(x) for x in self.df.columns]
                cols = [[str(y) for y in x] for x in cols]

                cols = [', '.join(col) for col in cols]
                cols = [x[1:] if x[0] == '/' else x for x in cols]
                return cols

        self.cols_short = make_cols(self, long=False)
        self.cols_long = make_cols(self)
        self.legend_long = make_legend(self)
        self.legend_short = make_legend(self, long=False)

    def line(self, **kwargs):
        plot.line(self.df, **kwargs)

    def heatmap(self, x, **kwargs):
        plot.heatmap(self.df, x, **kwargs)

    def scatter(self, x, y, **kwargs):
        plot.scatter(self.df, x, y, **kwargs)

    def range(self, x, **kwargs):
        plot.line_dailyrange(self.df, x, **kwargs)

    def surface(self, x, **kwargs):
        plot.surface(self.df, x, **kwargs)

    def hist(self, x, **kwargs):
        plot.hist(self.df, x, **kwargs)


class HSR_Info:
    '''hsr dataframe object for columns only, for speed.
    need: 
        dfcols (everything, for filtering)
        tidycols (pull out unnecessary things, make it look nice for filtering)
        legend (even more pulled out, for plotting)

    '''

    def __init__(self, hsrfile, getunits=True, multicol=True, show_warnings=False, cols_only=True):
        self.name = str(hsrfile).split("\\")[-1].replace(": ]", "")
        self.path = str(hsrfile)

        def make_cols(hsrfile):
            coldf = make_df(hsrfile, getunits=getunits,
                            multicol=False, cols_only=True)
            cols = coldf.T.values.tolist()
            [col.insert(0, self.name.replace(".hsr", "")) for col in cols]

            return cols
        self.cols = make_cols(hsrfile)

        def make_frame():
            ####
            pass


def dflist_to_colstring(hsr_filelist):
    '''take list of hsr files, pass strings for preview/filtering'''
    colstringlist = []
    for file in hsr_filelist:
        hsr = HSR_Info(file)
        colstring = [', '.join(col) for col in hsr.cols]
        colstringlist.append(colstring)
    colstringlist = [item for sublist in colstringlist for item in sublist]
    return colstringlist


def filter_string_to_df(folderpath, filterlist):
    '''take filtered list for multiple hsr files, return to concatenated dataframe'''

    if folderpath[-1] != '\\\\' or folderpath[-1] != '/':
        folderpath = folderpath + '/'

    files = list(set([x.split(", ")[0] for x in filterlist]))

    dflist = []
    for f in files:
        hsrfile = folderpath + f + '.hsr'
        #print ("-----****-----")
        #print (hsrfile)
        hsr = hsr_df(hsrfile, multicol=False)
        allcols = hsr.cols_long
        filterdf = hsr.df
        filterdf.columns = allcols
        filt_collist = []
        for col in allcols:
            for series in filterlist:
                if series in col:
                    filt_collist.append(col)

        filterdf = filterdf.loc[:, filt_collist]
        dflist.append(filterdf)

    concatdf = pd.concat(dflist, axis=1)
    if len(filterlist) != len(concatdf.columns):
        warnings.warn(
            "Warning: Filtered List not same as concatenated dataframe list. Inspect returned columns for accuracy.")
    return concatdf


def make_df(fname, year=2019, dayshift=0, getunits=True, multicol=True, novars=True, show_warnings=False, cols_only=False):
    '''makes and returns pandas dataframe out of hourly results .hsr file'''

    with open(fname, 'r', encoding='latin-1') as f:
        flist = f.readlines()
    coldf = pd.DataFrame(flist, columns=['flist'])
    coldf['flist'] = coldf['flist'].str.replace(', ', ' ')
    coldf = coldf['flist'].str.split(',', expand=True).iloc[4:10:, :-1]

    if novars:
        coldf = coldf.drop([8])
    if coldf.iloc[0, -1] == '\n':
        coldf = coldf.iloc[:, :-1]

    coldf = coldf.replace('', np.nan, regex=True)
    coldf = coldf.fillna(method='ffill', axis=1)
    coldf = coldf.replace("\"", "")
    collist = coldf.values.tolist()
    collist = [[str(x).replace("\"", "") if type(
        x) == str else x for x in y] for y in collist]
    # collist = [[str(x) if np.isnan(x) else x for x in y] for y in collist]

    if cols_only:
        return pd.DataFrame(collist).iloc[:, 4:]

    valdf = pd.DataFrame(flist[10:], columns=['vals'])
    valdf = valdf['vals'].str.split(',', expand=True)
    if valdf.iloc[0, -1] == '\n':
        valdf = valdf.iloc[:, :-1]

    valdf.columns = collist
    valdf = valdf

    # make datetime
    valdf['Year'] = year
    dtcols = pd.DataFrame([valdf.iloc[:, -1], valdf.iloc[:, 0], valdf.iloc[:, 1],
                           valdf.iloc[:, 2]]).transpose().astype(float, errors='raise')
    dtcols.columns = ['Year', 'Month', 'Day', 'Hour']
    hsrdatetime = pd.to_datetime(dtcols)
    valdf.index = hsrdatetime
    valdf = valdf.astype(float, errors='ignore')
    valdf.index = valdf.index + pd.Timedelta(str(dayshift) + " days")
    valdf = valdf.iloc[:, 4:-1]

    # change df based on args
    if getunits:
        valdf = get_units(valdf, show_warnings=show_warnings)

    valdf.columns.set_levels([l.fillna('N/A')
                              for l in valdf.columns.levels], inplace=True)

    if not multicol:
        pass
    return valdf


def get_units(df, show_warnings=False):
    '''takes hsr_unit_dict.csv and tries to lookup units. returns
    new partial multiindex tuplelist'''
    # unitdict = 'hsr_unit_dict.csv'
    # rptdf = pd.read_csv('./eqparse/hsr/hsr_unit_dict.csv')

    # print (rptdf)

    rows = unit_dict.unit_dict.split('\n')

    cols = [row.split(',') for row in rows]
    rptdf = pd.DataFrame(cols).iloc[2:, :3]
    rptdf.columns = ['Type', 'Name', 'Units']

    rpttype = [x[2] for x in df.columns]
    rptname = [x[4] for x in df.columns]
    rpt_tup = list(zip(rpttype, rptname))

    unitlist = []
    for tup in rpt_tup:
        try:
            unit = rptdf[(rptdf['Type'] == tup[0]) & (
                rptdf['Name'] == tup[1])]['Units'].values[0]
            unitlist.append(unit)
        except:
            if show_warnings:
                warnings.warn(
                    """"Warning: {0} not found in lookup between .hsr and equest standard report dictionary. consider inspecting/appending hsr_unit_dict.csv located at {1}""".format(tup[1], unitdictfile))
                unitlist.append('-')
            else:
                unitlist.append('-')

    unit_tuples = list(zip(rpttype, rptname, unitlist))
    for u in unit_tuples:
        if u[2] == '*':
            if show_warnings:

                warnings.warn(
                    """"Warning: units not found in dictionary for {0}. Unit set to "-". Consider inspecting/appending hsr_unit_dict.csvlocated at {1} ("*" val for unit indicates potentital missing unit; "-" val for unit indicates no units likely required.)""".format(str(u[0:2]), str(unitdictfile)))

    # add unitlist of tuples to dataframe
    unitdf = df.copy()
    unit_collist = []
    if len(df.columns) != len(unit_tuples):
        raise ValueError(
            "Error: dataframe column length different from unit column length.")
    for num, col in enumerate(df.columns):
        tolist = list(col)
        tolist.append(unit_tuples[num][2])
        unit_collist.append(tuple(tolist))
    multi = pd.MultiIndex.from_tuples(unit_collist)
    unitdf.columns = multi
    return unitdf
