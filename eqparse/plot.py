'''
generalized convenience plotting features for 
dataframes with plotly.

'''


import os
import xlwings as xw
import shutil
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


def tabledonut(df, title='', as_figure=False, sort=True, width=700, height=400):
    ''' 
    accepts pandas series i.e. df['base]
    index must be set to grouped values.

    example:

          A_htg  
    JAN     -    
    FEB     -    
    MAR     -    
    APR     -    

    '''

    if sort:
        df = df.sort_values(by=df.columns[0], ascending=False)

    values = df.values
    labels = df.index

    data = go.Pie(
        values=values,
        labels=labels,
        marker_colors=px.colors.qualitative.D3,
        hole=0.6,
        textinfo='label+percent',
        textposition='outside',
        showlegend=False
    )

    layout = go.Layout(
        width=width,
        height=height,
        title={
            'text': title,
            'x': 0
        },
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    fig = go.Figure(data=data, layout=layout)

    if as_figure:
        return fig

    else:
        fig.show()


def tablebar(df, title='', as_figure=False, sort=True, width=800, height=500):
    ''' 
    accepts dataframe with individual columns for each series. 
    index must be set to grouped values.

    example:

          A_htg   B_clg   C_htg    D_clg
    JAN     -       -       -       -
    FEB     -       -       -       -
    MAR     -       -       -       -
    APR     -       -       -       -
    .......

    '''
    if sort:
        df = df.sort_values(by=df.columns[0], ascending=False)

    data = [go.Bar(
        x=df.index,
        y=df[col],
        name=col,
        # marker_color=px.colors.qualitative.D3[num]


    ) for num, col in enumerate(df.columns)]

    layout = go.Layout(
        width=width,
        height=height,
        title={
            'text': title,
            'x': 0
        },
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    fig = go.Figure(data=data, layout=layout)

    if as_figure:
        return fig

    else:
        fig.show()
