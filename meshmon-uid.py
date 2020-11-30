# -*- coding: utf-8 -*-
## Add uid to data gathered from qMp nodes in GuifiSants
## http://dsg.ac.upc.edu/qmpsu/index.php
## meshmon-uid.py
## (c) Llorenç Cerdà-Alabern, May 2020.
## debug: import pdb; pdb.set_trace()

import json
import os
import sys
from datetime import date
import warnings
import importlib

cmn = importlib.import_module("meshmon-common")

uidDBfileName = "mmdata-uid-db.json"
uidDB = {}
touid = {}
uidcount = {}
newUID = True
created_new_uids = False

def copy_uid_to_touid(e):
    for key in ['hname', 'ipguifi', 'macs', 'ipv6gl', 'ipv6ll']:
        if key in e:
            if type(e[key]) is str:
	        touid_update(key, {e[key]: e['uid']})
            else:
                for v in e[key]:
	            touid_update(key, {v: e['uid']})

def copy_uidDB_to_touid():
    for e in uidDB['db']:
        copy_uid_to_touid(e)

def load_uid():
    """
    load uids from file uidDBfileName
    """
    global uidDB
    global touid
    uidDB = {}
    touid = {}
    if os.path.exists(uidDBfileName):
        try:
            uidDB = json.load(open(uidDBfileName))
            copy_uidDB_to_touid()
        except:
            cmn.abort("Cannot read uid file. Malformed json? " + uidDBfileName)
    else:
       cmn.error("uid file? " + uidDBfileName)
       uidDB = {'db': []}

def touid_update(k, what):
    global touid
    if k in touid:
        touid[k].update(what)
    else:
        touid.update({k: what})

def update_uidcount(uid):
    if uid in uidcount:
        uidcount[uid] += 1
    else:
        uidcount.update({uid: 1})


## key: hname, ipguifi, macs, ipv6gl, ipv6ll
def to_uid(key, val):
    """
    find a uid for key, creates dictionary if necessary
    """
    global touid
    global uidcount
    global uidDB
    if key in touid and val in touid[key]:
        uid = int(touid[key][val])
        update_uidcount(uid)
        return uid

def uid2hname(uid):
    global touid
    hname = []
    if not type(uid) is str:
        uid = str(uid)
        for h, u in touid['hname'].items():
            if(u == uid): hname.append(h)
    return hname

def create_uid(h, add):
    """
    create a new uid for h,add
    """
    global uidDB
    global created_new_uids
    rec = {'hname': [h], 'fadd': date.today().strftime("%y-%m-%d_%H-%M-%S")}
    if 'inet' in add: rec.update({'ipguifi': add['inet']})
    if 'inet6' in add: rec.update({'ipv6gl': add['inet6']})
    if 'inet6ll' in add: rec.update({'ipv6ll': add['inet6ll']})
    if 'ether' in add: rec.update({'macs': add['ether']})
    uid = len(uidDB['db'])
    rec.update({'uid': uid})
    cmn.say("adding uid: " + str(uid) + " to " + h)
    uidDB['db'].append(rec)
    copy_uid_to_touid(rec)
    created_new_uids = True
    update_uidcount(uid)
    return uid

def seek_uid(h, add):
    """
    seek uid
    """
    uid = to_uid('hname', h)
    if uid != None: return uid
    if add:
        if 'inet' in add:
            for ip in add['inet']:
                uid = to_uid('ipguifi', ip)
                if uid != None: return uid
        if 'ether' in add:
            for mac in add['ether']:
                uid = to_uid('macs', mac.upper())
                if uid != None: return uid
        if 'inet6ll' in add:
            for ip in add['inet6ll']:
                uid = to_uid('ipv6ll', ip)
                if uid != None: return uid
        if 'inet6' in add:
            for ip in add['inet6']:
                uid = to_uid('ipv6gl', ip)
                if uid != None: return uid
    else:
        return None
    return create_uid(h, add)

def get_uid(h, add, new=False):
    """
    return uid or creates a new one if not found
    """
    global uidcount
    uid = seek_uid(h, add)
    if uid != None:
        if cmn.verbose: cmn.say(h + ": " + str(uid))
        if new and (uidcount[uid] > 1):
            hname = uid2hname(uid)
            cmn.abort("ERROR: duplicated uid! " + str(uid) + ": " + 
                      ', '.join(hname) + "\n"
                      "Check uid db: " + uidDBfileName)
        else:
            return uid

def add_uid(d, saveDB=True):
    """
    add uid to dictionary d and saves if new uid are created
    """
    global created_new_uids
    global newUID
    global uidDB
    created_new_uids = False # initialize
    if not 'db' in uidDB: load_uid()
    for n in d.values():
        if not 'hostname' in n:
            warnings.warn('hostname?')
            continue
        if not 'addresses' in n:
            warnings.warn('addresses?')
            n['addresses'] = None
        uid = get_uid(n['hostname'], n['addresses'], newUID)
        if uid == None:
            cmn.error('uid? ' + n['hostname'])
            if n['addresses']:
                cmn.error(n['addresses'])
        else:
            n.update({'uid': uid})
    newUID = False
    if saveDB and created_new_uids:
        cmn.say('Saving ' + uidDBfileName)
        if os.path.exists(uidDBfileName):
            os.rename(uidDBfileName, uidDBfileName+'.old')
        with open(uidDBfileName, 'w') as f:
            f.write(json.dumps(uidDB, indent=2))

##
## testing
##
## debug: import pdb; pdb.set_trace()
# print to_uid('ipv6gl', 'fd66:66:66:ff00:20d:b9ff:fe44:7edc')
# print to_uid('hname', 'BCN-GS-CanBruixa20-RKM5-7bbd')
# print to_uid('hname', 'BCN-GS-Salou2bis-3a56')
# print to_uid('macs', '04:18:d6:64:3a:56'.upper())

# Local Variables:
# mode: python
# coding: utf-8
# python-indent-offset: 4
# python-indent-guess-indent-offset: t
# End:
