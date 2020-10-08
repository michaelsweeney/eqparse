
import os
import pandas as pd
from distutils.version import LooseVersion as lv
import numpy as np
import plotly
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import plotly.offline as py
import plotly.graph_objs as go
from plotly import tools
import plotly.express as px
import textwrap






class SimPlot:
    '''
    Plotting tools for SIM files
    '''
    def __init__(self, _self):
        self.sim = _self

    def plotsomething(self):
        # print (self.sim.beps())
        fig = px.bar(self.sim.beps())
        py.iplot(fig)
        return self.sim.beps()






    def monthly_stacked_lines(self):

        traces = [
            go.Scatter(
                x = df.index,
                y  = df[col],
                name = ', '.join(col),
                stackgroup='one'
            )
            for col in df.columns
        ]

        
        layout = go.Layout(
            autosize=False, 
            width = 800,
            height = 600,
            legend={
                'orientation': 'h'
            }
        )


        fig = go.Figure(data = traces, layout = layout)
        fig.show()






    def building_monthly_loads(self, area_normalize=None):
        return




    def space_monthly_loads(self, area_normalize=None):
        return



    def hvac_monthly_loads(self, area_normalize=None):
        return



