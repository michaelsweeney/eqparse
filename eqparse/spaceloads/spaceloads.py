import pandas as pd
import numpy as np



def try_numeric(df):
    def lambda_numeric(x):
        try:
            return pd.to_numeric(x, errors='raise')
        except:
            return x

    df = df.apply(lambda x: lambda_numeric(x))
    return df


def spaceloads(spaceloadscsv):
    '''
    takes spaceloads and changes to more easily manipulable df file
    '''
    df = pd.read_csv(spaceloadscsv, skiprows=4, header=None, keep_default_na=False, encoding='cp1252')
    
    df = df.replace('', np.nan)
    cols = df.iloc[0:4,:].fillna(method='ffill', axis=1)
    multi = pd.MultiIndex.from_arrays(cols.values)
    df.columns = multi
    df = df.iloc[4:,:]
    
    df = try_numeric(df)
    return df



