# eqparse

Python processing for eQUEST SIM, HSR, and INP files

### Installing

Use pip to install this package (you can always clone and manually import it as well):

```
pip install eqparse
```

to Load a SIM file, use LoadSim and do not use a file extension:

'''
mysim = eq.LoadSim('C:/myinputfile')
'''

This allows access to 'sim', 'hsr', and 'inp' modules (inp module is currently a work in progress. Support will be added to handle running simulations and creating ECMs.

Most reports can be accessed like this, returning Pandas Dataframes:


>mysim.sim.bepu()
>mysim.sim.ssa()


HSR files can be accessed like this:


>df = mysim.hsr.df



There are also some plotting functions, using Plotly, optimized for eQUEST HSR files:

>mysim.hsr.plot.line(df)
>mysim.hsr.plot.heatmap(df, 0) # < 0 refers to column number


## Authors

Michael Sweeney (github.com/michaelsweeney)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

Thanks to Santosh Philip and his excellent Eppy project for inspiration!
