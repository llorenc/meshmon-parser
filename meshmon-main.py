#!/usr/bin/python -d
# -*- coding: utf-8 -*-
## Format data gathered from qMp nodes in GuifiSants
## http://dsg.ac.upc.edu/qmpsu/index.php
## meshmon-main.py
## (c) Llorenç Cerdà-Alabern, May 2020.
## debug: import pdb; pdb.set_trace()

import os
import sys

locallib = os.environ['HOME'] + '/python2.7/site-packages/'
if os.path.exists(locallib):
    print(locallib)
    sys.path.append(locallib)

import json
import importlib
from operator import itemgetter
import click   ## https://click.palletsprojects.com/en/7.x
import fnmatch
import re
import gzip

# sys.path.append('parser')
cmn = importlib.import_module("meshmon-common")
par = importlib.import_module("meshmon-parser")
uid = importlib.import_module("meshmon-uid")
fmt = importlib.import_module("meshmon-format")

def get_date(f):
    re_pat = re.compile('(?P<date>\d\d-\d\d-\d\d_\d\d-\d\d-\d\d)', re.VERBOSE)
    match = re_pat.search(f)
    if match:
        return(match.group('date'))

def read_qmpdb(f):
    par.parse_file(f)
    uid.add_uid(par.qmpdb)

def build_graph(f):
    read_qmpdb(f)
    res = True
    try:
        fmt.build_graph(par.qmpdb)
    except:
        res = False
    return res

def build_rt(f):
    read_qmpdb(f)
    fmt.build_rt(par.qmpdb)

def get_ofile_name(f, odir, suf, skip):
    date = get_date(f)
    if date:
        ofile = odir + '/' + date + '-' + suf + ".json"
        ofilegz = odir + '/' + date + '-' + suf + ".json.gz"
        if (os.path.isfile(ofile) or os.path.isfile(ofilegz)) and skip:
            click.secho("skip "+ofile, fg="red")
        else:
            return ofile

def save_json(ofile, data):
    click.secho(ofile, fg="green")
    if(re.search(r'gz$', ofile)):
        with gzip.open(ofile, 'wb') as f:
            f.write(json.dumps(data, indent=2))
    else:
        with open(ofile, 'w') as f:
            f.write(json.dumps(data, indent=2))

def save_raw_json(f, save, odir, skip):
    if save:
        ofile = get_ofile_name(f, odir, "meshmon-raw", skip) + '.gz'
        if ofile:
            read_qmpdb(f)
            save_json(ofile, par.qmpdb)
    else:
        read_qmpdb(f)
        print(json.dumps(par.qmpdb, indent=2))

def save_graph_json(f, save, odir, skip):
    if save:
        ofile = get_ofile_name(f, odir, "meshmon-graph", skip) + '.gz'
        if ofile:
            if build_graph(f):
                save_json(ofile, fmt.graph)
            else:
                cmn.error("could not build graph, skipping " + f)
    else:
        build_graph(f)
        print(json.dumps(fmt.graph, indent=2))

def save_rt(f, save, odir, skip):
    if save:
        ofile = get_ofile_name(f, odir, "meshmon-rt", skip)
        if ofile:
            build_rt(f)
            save_json(ofile, fmt.tabs)
    else:
        build_rt(f)
        print(json.dumps(fmt.tabs, indent=2))


def proc_file(f, save, odir, skip, outformat):
    """
    """
    save_func = "save_%s" % outformat
    try:
        if callable(getattr(sys.modules[__name__], save_func)):
            getattr(sys.modules[__name__], save_func)(f, save, odir, skip)
    except:
        cmn.error(f + "?")

@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.argument('file', type=str, nargs=-1)
@click.option('-c', '--count', type=int, default=None, help='Number of file to process (-1 for all)')
@click.option('-d', '--dir', type=str, default='mmdata/20-08', show_default=True, help='File dir')
@click.option('-s', '--save/--no-save', default=True, show_default=True, help='Save output file')
@click.option('-v', '--verbose/--no-verbose', default=False, show_default=True, help='Verbose')
@click.option('-o', '--odir', type=str, default='.', show_default=True, help='Output dir')
@click.option('-k', '--skip/--no-skip', default=True, show_default=True, help='Skip existing files')
@click.option('-f', '--outformat', type=str, default='graph_json', show_default=True, 
              help='Output format [raw_json graph_json rt]')
def process(file, count, dir, save, verbose, odir, skip, outformat):
    cmn.verbose = verbose
    if file:
        file_list = file
        if not count: count = -1
        dirname = os.path.dirname(file_list[0])
        if dirname: dir = None
    else:
        file_list = fnmatch.filter(os.listdir(dir), 
                                   '*-qmpnodes-gather-meshmon*.data.gz')
    if not count: count = 1
    file_list = sorted(file_list, reverse=False)
    if(count > 0): file_list = file_list[0:count]
    for f in file_list:
        if(dir): f = dir + '/' + f
        if os.path.isfile(f):
            click.echo(f)
            if outformat in ['raw_json', 'graph_json', 'rt']:
                proc_file(f, save, odir, skip, outformat)
            else:
                cmn.abort(outformat + '?')

if __name__ == '__main__':
    process()

exit()

##
## testing
##
filepath = 'mmdata/20-05/20-05-24_11-50-02-qmpnodes-gather-meshmon.log.gz'
par.parse_file(filepath)
uid.add_uid(par.qmpdb)
fmt.build_graph(par.qmpdb)

len(fmt.graph)
print(json.dumps(fmt.graph[3], indent=2))


fmt.show(1)

# for i in sorted(par.qmpdb.keys(), key=lambda k: par.qmpdb[k]['id']):
#     print par.qmpdb[i]['id']

node = fmt.find_node_by_address(par.qmpdb, 'ether', "44:d9:e7:7e:87:10")
if node: print(str(node['uid']) + ": " + node['hostname'])

for n in sorted(par.qmpdb.values(), key=itemgetter('id')):
    print(n['hostname'] + ": " + str(n['id']) + ", " + str(n['uid']))

with open("meshmon.dump", 'w') as f:
    f.write(json.dumps(par.qmpdb, indent=2))

with open("meshmon-graph.dump", 'w') as f:
    f.write(json.dumps(fmt.graph, indent=2))

par.qmpdb[par.qmpdb.keys()[0]].keys()


par.print_keys(par.qmpdb[par.qmpdb.keys()[0]])


# print_qmpdb('net_dev')
# print_qmpdb()


v = ''
# for f in sorted(par.qmpdb.keys()):


par.qmpdb['fd66:66:66:7:feec:daff:fe7b:4525']['bmx6'].keys()

par.qmpdb['fd66:66:66:7:feec:daff:fe7b:4525']['bmx6']['originators'][0]

par.qmpdb['fd66:66:66:7:feec:daff:fe7b:4525']['bmx6']['links'][0]

par.qmpdb[par.qmpdb.keys()[0]]['bmx6']['originators'][0]

n = 1
par.qmpdb[par.qmpdb.keys()[n]]['bmx6']['status']['name']
par.qmpdb[par.qmpdb.keys()[n]]['bmx6']['status']
par.qmpdb[par.qmpdb.keys()[n]]['bmx6']['interfaces']
par.qmpdb[par.qmpdb.keys()[n]]['bmx6']['originators']
par.qmpdb[par.qmpdb.keys()[n]]['bmx6']['OPTIONS']
print(json.dumps(par.qmpdb[par.qmpdb.keys()[n]]['bmx6'], indent=2)) #['links']

n = 0
print par.qmpdb[par.qmpdb.keys()[n]]['hostname']
print par.qmpdb[par.qmpdb.keys()[n]]['id']
print par.qmpdb[par.qmpdb.keys()[n]]['iwdump'][par.qmpdb[par.qmpdb.keys()[n]]['iwdump'].keys()[0]].keys()

uid.get_uid(par.qmpdb[par.qmpdb.keys()[n]]['hostname'], par.qmpdb[par.qmpdb.keys()[n]]['addresses'])



sys.getsizeof(par.qmpdb)

exit

## par.qmpdb memory size:
import pickle
len(pickle.dumps(par.qmpdb))

##
## testing
##
nodesec = next(nodes)[1]

(name, content) = next(sections)

print(name)
print(content)

for s in sections: print(s[0])


for n in nodes: print(n[0])


print("%s: %s" % (match.start(), match.group('node_name')))


for i in result: print(i)

pathlib.Path(__file__).parent.absolute()

os.getcwd()

par.qmpdb['fd66:66:66:7:feec:daff:fe7b:4525']['bmx6']['originators'][0]

par.qmpdb[par.qmpdb.keys()[0]]['bmx6']['originators'][0]

n = 1
par.qmpdb[par.qmpdb.keys()[n]]['bmx6']['status']['name']
par.qmpdb[par.qmpdb.keys()[n]]['bmx6']['status']
par.qmpdb[par.qmpdb.keys()[n]]['bmx6']['interfaces']
par.qmpdb[par.qmpdb.keys()[n]]['bmx6']['originators']
par.qmpdb[par.qmpdb.keys()[n]]['bmx6']['OPTIONS']
par.qmpdb[par.qmpdb.keys()[n]]['bmx6']['links']

sys.getsizeof(par.qmpdb)

exit

## par.qmpdb memory size:
import pickle
len(pickle.dumps(par.qmpdb))

# Local Variables:
# mode: python
# coding: utf-8
# python-indent-offset: 4
# python-indent-guess-indent-offset: t
# End:
