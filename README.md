# eqparse

Python processing for eQUEST SIM and HSR files

### Getting Started

Use pip to install this package (you can always clone and manually import it as well):

```
pip install eqparse
```

to Load a SIM file, use LoadSim and do not use a file extension:

'''
mysim = eq.LoadSim('C:/myinputfile')
'''


### Installing
The 'loadSim' object allows access to 'sim' and 'hsr' modules

Most reports can be accessed like this, returning Pandas Dataframes:


>mysim.sim.bepu()
>mysim.sim.ssa()


HSR files can be accessed as DataFrames as follows:

>df = mysim.hsr.df

### Convenience functions

In general, the primary functionality eqparse has been designed to be as unopinionated as possible. However, some convenience functions break this paradigm in order to satisfy specific end-user requests.

A few example methods (these are generally located at the top-level LoadSim object):

>mysim.annual_summaries() # < returns a dictionary of 'beps', 'bepu', and 'cost' end-use summary dataframes
>
>mysim.annual_cost_enduses() # < calculates virtual utility rates and provides cost-level end-use summary similar to standard BEPS / BEPU outputs.
>
>mysim.leed_enduses() # < pivots PS-F reports into a more LEED-friendly format for data entry.
>
>mysim.sim_print() # < accepts a list of report names, outputs a working SIM file with only the reports passed (useful for compliance-based report export)

eqparse also has some plotting functions, using Plotly:
>hsr_df = mysim.hsr.df
>mysim.hsr.plot.line(df)
>mysim.hsr.plot.heatmap(df, 0) # < 0 refers to column number


Group airside system ss-a reports by system name, pull total cooling & heating energy from each:
>ssa_df = mysim.sim.ssa().groupby('Object').sum()

Create barplot of cooling/heating for each system:
>eq.plot.tablebar(ssa_df)

### 

## Authors

Michael Sweeney (github.com/michaelsweeney)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

Thanks to Santosh Philip and his excellent Eppy project for inspiration!
