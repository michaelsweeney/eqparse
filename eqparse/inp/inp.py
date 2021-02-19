'''
a series of functions allowing user to collect objects in equest
and assign new values to them and also update existing values.

'''

from collections import OrderedDict
import re
import numpy as np
import pandas as pd
import operator
import os
import shutil


parentdict = {
    "ZONE":"SYSTEM",
    "SPACE":"FLOOR",
    "EXTERIOR-WALL":"SPACE",
    "INTERIOR-WALL":"SPACE",
    "UNDERGROUND-WALL":"SPACE",
    "WINDOW":"EXTERIOR-WALL",
    "DOOR":"EXTERIOR-WALL"
    }



def openinp(inpread):
    with open(inpread) as f:
        inpfile = f.readlines()
    return inpfile



def get(listname, inptype="", parent=True):
    '''returns nested dictionary, one level deep.
    inptype is type from inp file.
    i.e., 'SYSTEM', 'FLOOR'
    DOESN'T WORK FOR SCHEDULES
    parent argument does not function

    '''
    localparent = 'none'
    topdict = OrderedDict()
    write = False
    bottomdict = OrderedDict()
    for num, line in enumerate(listname):

        #ESTABLISH WHEN TO WRITE
        if "= " + inptype in line:
            write = True
            topkey = re.sub('=.*', '', line).strip().strip("\"")

            #WRITE PARENT (IF APPLICABLE)
            if parent:
                if inptype in parentdict:
                    for x in reversed(listname[0:num]):
                        if "= " + parentdict[inptype] + "  " in x:
                            localparent = re.sub('=.*', '', x).strip().strip("\"")
                            break

        #POPULATE DICTIONARIES
        if write:
            if "=" in line:
                bottomkey = re.sub('=.*', '', line).strip()#.strip("\"")
                bottomval = re.sub('.*=', '', line).strip()#.strip("\"")
                bottomdict[bottomkey] = bottomval

            if ".." in line and parent:
                topdict[topkey] = bottomdict
                bottomdict['parent'] = localparent
                bottomdict = OrderedDict()
                write = False
                
            if ".." in line and not parent:
                topdict[topkey] = bottomdict
                bottomdict = OrderedDict()
                write = False
    
    #dict modifiers for extraneous info for certain inptypes
    if inptype == 'POLYGON':
        topdict = remove(topdict,'SHAPE')
    if inptype == 'SPACE':
        topdict = remove(topdict,'WASTE-HEAT-USE')
      
    #update this with if clause
    try:
        topdict.pop('LOCATION')
    except:
        pass
    return topdict






def getall(listname):
    '''returns nested dictionary, one level deep.
    of all objects. needs to have equest pre-formatting,
    in particular, object name needs to have zero spaces in 
    front of it and object values need to have there spaces
    in front of them

    '''
    topdict = OrderedDict()
    write = False
    bottomdict = OrderedDict()
    for  line in listname:

        #ESTABLISH WHEN TO WRITE
        if "= " in line and line[0:2] !="  ":
            write = True
            topkey = re.sub('=.*', '', line).strip().strip("\"")

        #POPULATE DICTIONARIES
        if write:
            if "=" in line:
                bottomkey = re.sub('=.*', '', line).strip()#.strip("\"")
                bottomval = re.sub('.*=', '', line).strip()#.strip("\"")
                bottomdict[bottomkey] = bottomval

            if ".." in line:
                topdict[topkey] = bottomdict
                bottomdict = OrderedDict()
                write = False
        
    return topdict





def get_sys_zones(inpin):
    '''uses 'get' module and adds a list of zones served by the system.
    returns ordered dictionary of systems
    '''

    inpin = openinp(inpin)
    
    sys_dict = get(inpin,"SYSTEM")
    zndict = get(inpin,"ZONE")
    
    for k, v in zndict.items():
        if v['parent'] in sys_dict:
            
            if "attached_zones" not in sys_dict[v['parent']].keys():
                sys_dict[v['parent']]['attached_zones'] = [k]
                
            else:
                sys_dict[v['parent']]['attached_zones'].append(k)#sysdict[v['parent']]['attached_zones'].append(k)

    return sys_dict



def remove(dictionary,str_remove, str_save=None):
    '''
    removes keys and associated values from an 
    ordereddictionary, likely created using 'get',
    based on str_remove. 
    optional: str_save: remove exception (keep these)   
    
    '''
    if str_save:
        removedict = OrderedDict({k:v for k,v in dictionary.items() if str_remove not in k or str_save in k})

    else:
        removedict = OrderedDict({k:v for k,v in dictionary.items() if str_remove not in k})
    return removedict



def stripvals(dictionary, key_remove, key_save=None):#,val_remove):#,str_save='None'):
    
    '''
    strips out keys within all objects
    (i.e. "EQUIP-LATENT")
    
    '''
    
    removekeys = []
    removedict = OrderedDict()#dictionary
    if key_save:
        for key, value in dictionary.items():
            removedict[key] = OrderedDict({k1:v1 for k1,v1 in value.items() if key_remove not in k1 or key_save in k1})
    if not key_save:
         for key, value in dictionary.items():
            removedict[key] = OrderedDict({k1:v1 for k1,v1 in value.items() if key_remove not in k1})
    return removedict



def objectvaluetuple(dictname, innervalue, nullval = None, fromparent=False, parentdict=None):
    '''makes a list of tuples of outervalue / innervalue,
    i.e. "Zn 1", "Unconditioned" from 
    nested ODict created using "get" function

    '''
    if not fromparent:
        odict = OrderedDict()
        for k, v in dictname.items():
            try:
                odict[k] = v[innervalue].strip("\"")
            except:
                odict[k] = nullval
        odict = list(odict.items())
        return odict
    
    if fromparent:
        odict = OrderedDict()
        for k, v in dictname.items():
            try:
                parent = v['parent']
                odict[k] = parentdict[parent][innervalue].strip("\"")
            except:
                odict[k] = nullval
        odict = list(odict.items())
        return odict     
        	


def filterdictbyvalue(dictname,valkey,valvalue):
    '''takes only objects from a given set if they match the value specified.
    e.g. filterdictbyvalue(zones,'TYPE','CONDITIONED')
    yields a dict of dict of all conditioned zones
    '''
    filtlist = {k:v for k, v in dictname.items() if v[valkey] == valvalue}
    return filtlist



def updatedict(dictionary, topkey, bottomkey, value):
    '''
    updates dictionary after using 'get'
    '''
    
    dictionary[topkey][bottomkey] = value





def objectdump(bottomdict,listname=None):
    '''
    take a single object and append it to a list, including "..":
    '''
    if listname == None:
        dumplist = []
        for k1, v1 in bottomdict.items():
            if 'parent' != k1:
                dumplist.append(k1 + " = " + v1)        
    else:       
        for k1, v1 in bottomdict.items():
            if 'parent' != k1:
                listname.append(k1 + " = " + v1)                    
        listname.append('..')
        dumplist = listname
    
    return dumplist
    


def replace_inp_section(inplistname,newlist,startreplace,endreplace):
    '''
    substitues an entire chunk of an inp file with another.
    example: replace all systems/zones with a completely
    different, reordered list. 
    "= SYSTEM" = startreplace
    "Metering & Misc HVAC" = endreplace
    
    '''
    sysstart = []
    sysend = []
    
    for num, line in enumerate(inplistname):
        if startreplace in line:
            sysstart.append(num)
            sysend.append(num-1)
        if endreplace in line:
            sysend.append(num-3)
            sysend = sysend[1:]
    #write new inp
    f_listnew = []
    list1 = inplistname[0:sysstart[0]]
    list2 = newlist
    list3 = inplistname[sysend[-1]:]
    f_listnew.append(list1)
    for l in list2:
        f_listnew.append(l)
    f_listnew.append(list3)    
    flistappend = list1 + list2 + list3
    return flistappend


def obj_insert(flist,objtoinsert,afterobject):
    '''
    inserts a bottomdict/ordereddict-style object into
    an input file in list form
    '''
    insertlist = objectdump(objtoinsert)   
    location = obj_location(flist,afterobject)
    flistinserted = flist[0:(location[1]+1)] + insertlist + flist[(location[1]):]
    return flistinserted



def obj_location(flist, objname):
    '''
    enumerates flist, returns start and end location of
    object in tuple form
    '''
    pattern = objname
    length = int(len(objname))+2
    start = False
    for num, line in enumerate(flist):
        if ("\"" + objname + "\"") in line[0:length]:
            objstart = num
            start = True
        if start:
            if ".." in line:
                objend = num
                start = False
                break      
    return objstart, objend
    


def removeobject(flist,objname,objtype):
    '''
    go through flist and remove objname (changes to '$'
    to avoid issues with mutation while looping.)
    '''
    pattern = "\"" + objname + "\"" + " = "

    start = False
    flistdelete = flist
    for num, f in enumerate(flist):
        if pattern in f:
            start = True
        if start:
            flistdelete[num] = '$$$ '
        if ".." in f:
            start = False
    return flistdelete
   


def writeinp_fromlist(listname,newinp,subdir=None):
    '''
    simple writeinp, just takes list and prints to file.
    also provides func
    '''
    listname = [i for i in listname if len(i) > 1]
    
    if subdir != None:
        if not os.path.exists(subdir):
            os.makedirs(subdir)
            
        fname = subdir + "/" + newinp
        with open(fname, 'w') as new:
            for item in listname:
                new.write("%s\n" % item)

    else:
        fname = newinp
        with open(fname, 'w') as new:
            for item in listname:
                new.write("%s\n" % item)     
        
    

def writeinp(listname, newinp, dictname, write=True):
    '''
    define types to update:
    go through list
    if a string matches the type, log the tag matching the dictionary
    if the tag matches a key in the dictionary,
    delete from that string til the next '..'
    insert, at the same place in flist, each key/value pair, except parent, with " = " in between
    '''

    listname = [i for i in listname if len(i) > 1]

    for num, line in enumerate(listname):
        topkey = re.sub('=.*', '', line).strip().strip("\"")
        if topkey != 'LOCATION' and topkey in dictname.keys():
            delete = True
            tlist = []
            for k1, v1 in dictname[topkey].items():

                if 'parent' not in k1 and str(np.nan) not in str(v1):
                    tlist.append(str(k1) + " = " + str(v1))

            tlist.append("   ..")
            listname[num] = [t for t in tlist]

    #remove older elements
    n_list = listname
    delete = False
    for num, line in enumerate(listname):
        if type(line) == list:
            delete = True
        if delete and type(line) != list:
            n_list[num] = "$"
        if "  .." in line:
            delete = False

    flat_list = []
    for n in n_list:
        if type(n) == str:
            flat_list.append(n)
        if type(n) == list:
            for x in n:
                flat_list.append(x)

    flat_list = list(filter(lambda x: x != "$", flat_list))
    flat_list = [f for f in flat_list if len(f) > 2 or "\n" not in f or ".." in f or "}" in f]
    
    if write:
        with open(newinp, 'w') as new:
            for item in flat_list:
                new.write("%s\n" % item)
 
    return flat_list
