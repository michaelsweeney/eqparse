'''

the 'load' module provides common access to the 'sim' and 'hsr' modules, including
automated batch routines and plotting. all parsing logic for sim files/reports should
be accomplished in 'sim.py' or 'hsr.py'; this is mainly an API for script-running.

'''


import os
import xlwings as xw
import shutil
import pandas as pd

from .sim.sim import RptHandler
from .sim import batch

from .hsr.hsr import hsr_df as hsr_df

from .hsr.unit_dict import unit_dict
from .inp import inp

from .spaceloads.spaceloads import spaceloads




class LoadSim:

    '''
    Main entry-point for eqparse module. 
    Can pass in sim file or hourly file or just general extensionless name, e.g.
    "Prop.SIM", "Prop.hsr", "Prop" will all work.
    '''

    def __init__(self, file, hsr = True, inpfile = None):
        file = file.replace('.SIM','').replace('.hsr','')
        self.fname = file.split("\\")[-1].split("/")[-1]
        self.sim = RptHandler(file + '.SIM')
        self.path = os.path.dirname(file)
        
        if hsr:
            try:
                self.hsr = hsr_df(file + '.hsr')
            except:
                print ("HSR validation failed. Check eQUEST component names for commas or other special characters.")

        if inpfile is not None:
            self.inpfile = inpfile
        
        ## doesn't work, needs further parsing.
        # spcloadfile = '-'.join(file.split('-')[:-1]) + '- SpaceLoads.csv'
        # try:
        #     self.spaceloads = spaceloads(spcloadfile)
        # except:
        #     self.spaceloads = 'Not Loaded: {0}'.format(spcloadfile)



    def tidy_enduses(self, dropzeros = True, includetotal=False, rename=True):
        '''
        returns tidy dataframe with concatenated enduses + value
        '''
        try:
            beps, bepu, cost = self.annual_summaries(writecsv=False)
            iscost = True
        except:
            beps, bepu = self.annual_summaries(writecsv=False)
            iscost = False

        if iscost:
            costmelt = pd.melt(cost, id_vars=['File', 'Rate', 'Meter', 'Utility'])
            costmelt['Enduse'] = costmelt['variable'] + ' - ' + costmelt['Meter']

        bepsmelt = pd.melt(beps, id_vars=['File', 'Meter', 'Utility', 'Value'])
        bepsmelt['Enduse'] = bepsmelt['variable'] + ' - ' + bepsmelt['Meter']

        bepumelt = pd.melt(bepu, id_vars=['File', 'Meter', 'Utility', 'Value'])
        bepumelt['Enduse'] = bepumelt['variable'] + ' - ' + bepumelt['Meter']
           
        if dropzeros:
            if iscost:
                costmelt = costmelt[costmelt.value != 0]
            bepumelt = bepumelt[bepumelt.value != 0]
            bepsmelt = bepsmelt[bepsmelt.value != 0]
        
        if not includetotal:
            if iscost:
                costmelt = costmelt[costmelt.variable != 'Total']
            bepumelt = bepumelt[bepumelt.variable != 'Total']
            bepsmelt = bepsmelt[bepsmelt.variable != 'Total']

        if iscost:
            costmelt = costmelt[['Enduse', 'value']].set_index('Enduse', drop=True)
        bepumelt = bepumelt[['Enduse', 'value']].set_index('Enduse', drop=True)
        bepsmelt = bepsmelt[['Enduse', 'value']].set_index('Enduse', drop=True)
        
        if rename:
            if iscost:
                costmelt.columns = [self.fname + ' - COST']
            bepumelt.columns = [self.fname + ' - BEPU']
            bepsmelt.columns = [self.fname + ' - BEPS']
        if iscost:

            return {
                'beps': bepsmelt,
                'bepu': bepumelt,
                'cost': costmelt
            }
        else:
            return {
                'beps': bepsmelt,
                'bepu': bepumelt,
            }  

    def annual_summaries(self, writecsv=True, opencsv=True):
        '''
        Exports the following: 
            fname_BEPS.csv, 
            fname_BEPU.csv, 
            fname_COST.csv, 
            fname_UNMET.csv,

        Also returns dict of Pandas Dataframes
        Available Kwargs: 
        writecsv: Bool
        opencsv: Bool
        reports: 
        '''


        beps = self.sim.beps()
        bepu = self.sim.bepu()

        iscost = True
        try:
            cost = self.annual_cost_enduse()
        except:
            iscost = False
            print ('Rates have not been defined for this project; cost outputs will not be created.')

        unmet_df, cool_ssr, heat_ssr = self.sim.unmet()

        if writecsv:

            beps_file = self.path + "/" + "__BEPS_"+self.fname+".csv"
            bepu_file = self.path + "/" + "__BEPU_"+self.fname+".csv"
            unmet_file = self.path + "/" + "__UNMET_"+self.fname+".csv"


            beps.to_csv(beps_file, index=False)
            bepu.to_csv(bepu_file, index=False)



            if iscost:
                cost_file = self.path + "/" + "__COST_"+self.fname+".csv"
                cost.to_csv(cost_file, index=False)

            # UNMET CONCAT
            with open(unmet_file, 'w', newline='\n') as f:
                unmet_df.to_csv(f)
                
            with open(unmet_file, 'a', newline='\n') as f:
                heat_ssr.to_csv(f)
                cool_ssr.to_csv(f)
                        

            if opencsv:
                book = xw.Book(beps_file)
                book.close()
                book = xw.Book(bepu_file)
                book.close()
                if iscost:
                    book = xw.Book(cost_file)
                    book.close()
                book = xw.Book(unmet_file)
                book.close()
        else:
            if iscost:
                return beps, bepu, cost
            else:
                return beps, bepu


    def hourly(self):
        return self.hsr.df

    def hourlyreports(self):
        return self.hsr.df.columns


    def hourly_results(self):
        self.hsr.df.to_csv(self.path + "/" + self.fname + ".csv")

    def leed_enduses(self, write_csv=True, open_csv = True):
        leed_psf =  self.sim.psf(leedpivot=True)
        if write_csv:
            fname = self.path + "/" + "__LEED_ENDUSES_"+self.fname+".csv"
            leed_psf.to_csv(fname)
            if open_csv:
                book = xw.Book(fname)
                book.close()
        return leed_psf



    def sim_print(self, reportlist):
        '''
        for printing sim files (i.e. for code/LEED submission) tio PDF, returns 
        new *.SIM with only the items in the reportlist (e.g. ['ES-D', 'BEPS', 'BEPU'])
        '''

        directory = "Report Outputs"

        simpath = self.path + '/' + self.fname + '.SIM'
        fdir =  self.path + '/' + directory
        fname = '_outputs_' + self.fname + '.SIM'
        fpath = fdir + '/' + fname

        if not os.path.exists(fdir):
            os.makedirs(fdir)
        
        if os.path.isfile(fpath):
            os.remove(fpath)
        
        with open(simpath) as f:
            f_list = f.readlines()
            rptstart = []
            for num, line in enumerate(f_list,0):
                for r in reportlist:
                    if r == 'PV-A':
                        parse_mod = True
                    else:
                        parse_mod = False
                        
                    if r in line:
                        if parse_mod:
                            rptstart.append(int(num)-2)
                        else:
                            rptstart.append(int(num)-2)
                        
            for r in rptstart:  
                lines = 0
                scan = f_list[r+3:(r+1000)]
                while lines is 0:  
                    for num, line in enumerate(scan):
                        rptlen = []
                        if "REPORT" in line:
                            rptlen.append(num)
                            lines = lines + 1
                            break
                            


                rpt_text_list = (f_list[r:(r+rptlen[0]+1)])
                if 'PV-A' in rpt_text_list[2] or 'PS-E' in rpt_text_list[2]  or 'PS-F' in rpt_text_list[2]:
                    rpt_text_list[-1] = rpt_text_list[-1][:-2]



                with open(fpath, 'a') as output:
                    for l in rpt_text_list:
                        output.write(l)

            print ('Successfully Printed Requested Reports to {0}'.format((fpath)))


    def annual_cost_enduse(self):    

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
                
        bepu = self.sim.bepu()
        ese = self.sim.ese()

    
        mdict = {}
        rate = list(ese.Object)
        meters = list(ese.Meters)

        for num, mtrlist in enumerate(meters):
            for mtr in mtrlist:
                mdict[mtr] = rate[num]

        rdict = ese.groupby('Object').sum()[['TOTAL CHARGE ($)', 'METERED ENERGY (KWH)']]
        rdict['vrate'] = rdict['TOTAL CHARGE ($)'] / rdict['METERED ENERGY (KWH)']

        vrate = rdict['vrate'].to_dict()
        metervrate = {}

        for key, value in mdict.items():
            metervrate[key] = vrate[value]

        utils = get_utils(bepu.index)

        def try_rate(x):
            try:
                return mdict[x]
            except:
                return 0


        def try_vrate(rate, metervrate):
            try:
                return metervrate[rate]
            except:
                if rate == 0:
                    return 0
                else:
                    print('could not find associated vrate from meter: {0}'.format(rate))
        
        bepu['UTILITY'] = utils
        bepu.index = [x.replace(" ELECTRICITY", "").replace(" NATURAL-GAS","").replace(" STEAM","").replace(" CHILLED-WATER","").strip() for x in bepu.index]
        bepu['meter'] = bepu.index
        bepu['rate'] = bepu['meter'].apply(lambda x: try_rate(x))
        bepu['vrate'] = bepu['rate'].apply(lambda x: try_vrate(x, vrate))
        bepu['vrate'] = bepu['vrate'].fillna(0)

        try:
            cost = bepu[['Lights',
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
                        'Total']].apply(lambda x: x * bepu['vrate'])
            
            cost['Utility'] = utils
            cost['File'] = bepu['File']
            cost['Rate'] = bepu['rate']
            cost['Meter'] = bepu['meter']
            
            
            cost = cost[[
                    'File',
                    'Rate',
                    'Meter',
                    'Utility',
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
            
            return cost
      
        except:
            print('COULDNT\'T PARSE BEPU AND VRATE. CHECK FOR NAN OR -NAN IN RESULTS')
            # print (bepu)
            # print (sim)


    def systemsummaries(self):
        ssl = self.sim.ssl()
        ssa = self.sim.ssa()

        ssl['Month'] = ssl.index
        sslsumm = ssl.copy()
        sslsumm['Fan Power (kWh)'] = sslsumm['FAN ELEC DURING HEATING (KWH)'] + sslsumm['FAN ELEC DURING COOLING (KWH)'] + sslsumm['FAN ELEC DURING FLOATING (KWH)'] - sslsumm['FAN ELEC DURING HEAT & COOL KWH)']

        sslsumm = sslsumm[['Month', 'Object', 'File', 'Fan Power (kWh)']]

        ssasumm = ssa[['Month', 'Cooling Energy (MMBtu)', 'Heating Energy (MMBtu)', 'Object', 'File']]
        systemsummaries = ssasumm.merge(sslsumm, how='left', left_on=['Month', 'Object'], right_on = ['Month', 'Object'])
        systemsummaries = systemsummaries[[
            'Month','Cooling Energy (MMBtu)','Heating Energy (MMBtu)','Object','File_x','Fan Power (kWh)'
        ]]
        systemsummaries = systemsummaries[[
            'Object',
            'Month',
            'Cooling Energy (MMBtu)',
            'Heating Energy (MMBtu)',
            'Fan Power (kWh)',
            'File_x'
        ]]

        systemsummaries.columns = [x.replace("File_x","File") for x in systemsummaries]
        return systemsummaries

                    


    def monthly_cost_enduse(self):
        # only needed for rate parsing by month. otherwise use monthly_enduses
        def monthly_vrate_dict(ese):
            month_rate_costs = ese.groupby(['Object', 'Month'], sort=False).sum()['VIRTUAL RATE ($/UNIT)'].reset_index()
            month_rate_cost_dict = {}
            for rate in month_rate_costs['Object'].unique():
                month_rate_cost_dict[rate] = {}
                for month in month_rate_costs['Month'].unique():
                    month_rate_cost_dict[rate][month] = month_rate_costs[(month_rate_costs['Object'] == rate) & (month_rate_costs['Month'] == month)]['VIRTUAL RATE ($/UNIT)'].tolist()[0]
            return month_rate_cost_dict

        ese = self.sim.ese()
        psf = self.sim.psf()
        vrate_dict = monthly_vrate_dict(ese)

        psf = psf[(psf['Cons_Demand'] == 'Consumption')].groupby(['Object', 'Month'], sort=False).sum().drop('Total', axis=1).reset_index()

        enduses = ['Lights', 'Task Lights',
            'Misc Equip', 'Space Heating', 'Space Cooling', 'Heat Reject',
            'Pumps & Aux', 'Vent Fans', 'Refrig Display', 'Ht Pump Supplem',
            'Domest Hot Wtr', 'Ext Usage']

        mdict = {}
        rate = list(ese.Object)
        meters = list(ese.Meters)

        for num, mtrlist in enumerate(meters):
            for mtr in mtrlist:
                mdict[mtr] = rate[num]

        def try_rate(x):
            try:
                return mdict[x]
            except:
                try:
                    
                    return mdict[x[0:4]]
                except:
                    return 0

        psf['rate'] = psf['Object'].apply(lambda x: try_rate(x))
        def try_vrate(x, vrate_dict):
            month = x['Month']
            rate = x['rate']
            try:
                byrate = vrate_dict[rate]
                bymonth = byrate[month]
                return bymonth
            except:
                return 0

        psf['vrate'] = psf.apply(lambda x: try_vrate(x, vrate_dict), axis=1)
        cost_monthly_enduse = psf.copy()
        for col in cost_monthly_enduse.columns:
            try:
                cost_monthly_enduse[col] = cost_monthly_enduse[col].astype(float) * cost_monthly_enduse['vrate'].astype(float)
            except:
                pass

        dflist = []
        for meter in cost_monthly_enduse['Object'].unique():
            mtrdf = cost_monthly_enduse[cost_monthly_enduse['Object'] == meter]
            for use in enduses:
                if mtrdf[use].sum() != 0:
                    series = mtrdf[use]
                    series.index = mtrdf.Month
                    series.name = series.name + '-' + meter            
                    dflist.append(mtrdf[use])
        cost_df = pd.DataFrame(dflist).T
        return cost_df






    def simrpt(self, listofsims, rpt):
        return pd.concat([RptHandler(sim) for sim in listofsims], axis=0)



            











        











