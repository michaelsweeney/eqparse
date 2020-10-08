
import eqparse.sim as sim_parse
import glob as gb





def beps(folder, dest = None, write = True):
    if not dest:
        dest = folder
    else:
        dest = dest
        
    sims = gb.glob(folder + '*.SIM')
    
    for sim in sims:
    
        sname = sim.split('\\')[-1].replace('.SIM','')
        beps = sim_parse.RptHandler(sim).beps()
        
        utils = get_utils(beps.index)
        
        beps['UTILITY'] = utils
        beps.index = [x.replace(" ELECTRICITY", "").replace(" NATURAL-GAS","").replace(" STEAM","").replace(" CHILLED-WATER","").strip() for x in beps.index]
     
        beps = beps[[
                'File', 
                'UTILITY',       
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
                'Total', 
                ]]
        
        if write:
            beps.to_csv(dest  + "__BEPS_" + sname + ".csv")
        
        
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
           
           
def make_annual_cost(sim):    
    def try_vrate(mtr, vdict):
        try:
            return vdict[mtr]
            print ('yes')
        except:
            return 0
    

    bepu = sim.bepu()
    
    ese = sim.ese()
    ese['Meters'] = ese['Meters'].apply(lambda x: x[0])

    monthvrate = ese.groupby('Meters').sum()
    monthvrate
    conscol = [x for x in monthvrate.columns if "METERED ENERGY" in x][0]
    costcol = 'ENERGY CHARGE ($)'
    monthvrate = monthvrate[[conscol, costcol]]
    monthvrate['vrate'] = monthvrate[costcol] / monthvrate[conscol]
    vrate = monthvrate.vrate.to_dict()
    bepu = bepu.iloc[1:,:]
    
    
    utils = get_utils(bepu.index)
    bepu['UTILITY'] = utils
    bepu.index = [x.replace(" ELECTRICITY", "").replace(" NATURAL-GAS","").replace(" STEAM","").replace(" CHILLED-WATER","").strip() for x in bepu.index]
    bepu['meter'] = bepu.index
    bepu['vrate'] = bepu['meter'].apply(lambda x: try_vrate(x, vrate))

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
        
        cost['UTILITY'] = utils
        
        
        cost = cost[[
                'UTILITY',    
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
        print (bepu)
        print (sim)
        
    





def cost(folder, dest = None, write = True):
    
    if not dest:
        dest = folder
    else:
        dest = dest
        
    sims = gb.glob(folder + '*.SIM')
    
    for sim in sims:
        sname = sim.split('\\')[-1].replace('.SIM','')
        sim = sim_parse.RptHandler(sim)
        
        ese_annual = make_annual_cost(sim)
        
        
        
        if write:
            ese_annual.to_csv(dest  + "__COST_" + sname + ".csv")
        
        
        
        
        
