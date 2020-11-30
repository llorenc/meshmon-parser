# -*- coding: utf-8 -*-
## Add uid to data gathered from qMp nodes in GuifiSants
## http://dsg.ac.upc.edu/qmpsu/index.php
## meshmon-format.py
## (c) Llorenç Cerdà-Alabern, May 2020.
## debug: import pdb; pdb.set_trace()

import json

cache = {}
graph = []
tabs = {}

def find_node_by_address(d, k, v):
    """
    find address v in d[*]['addresses'][k]
    k: ether, inet6, inet, inet6ll
    """
    if v in cache:
        return cache[v]
    else:
        for n in d.values():
            if 'addresses' in n and k in n['addresses']:
                for a in n['addresses'][k]:
                    if v == a:
                        cache.update({v: n})
                        return n
    return None

def add_ids_to_link(d, links):
    """
    """
    for l in links:
        if 'llocalIp' in l:
            n = find_node_by_address(d, 'inet6ll', l['llocalIp'])
            if n: l.update({'id': n['id']})

def add_iwdump_to_l(d, links, ifces, w):
    """
    """
    for i in w.values():
        for m in i.keys():
            n = find_node_by_address(d, 'ether', m)
            if n and 'id' in n:
                for l in links:
                    if 'id' in l and l['id'] == n['id'] and l['viaDev'] in ifces \
                       and ifces[l['viaDev']] == 'wireless':
                        l.update({'iwdump': i[m]})
                        break

def get_interfaces(ifces):
    """
    """
    res = {}
    for i in ifces:
        if 'devName' in i and 'type' in i: 
            res.update({i['devName']: i['type']})
    return res

def add_links(d, ng, n):
    """
    """
    i = get_interfaces(n['bmx6']['interfaces'])
    ng.update({'interfaces': i})
    l = n['bmx6']['links']
    add_ids_to_link(d, l)
    if 'iwdump' in n:
        add_iwdump_to_l(d, l, i, n['iwdump'])
    ng.update({'links': l})

def add_net_dev(ng, nd):
    """
    """
    res = {}
    for k,v in nd.items():
        if k in ng['interfaces']: res.update({k: v})
    if res: ng.update({'net_dev': res})

def build_graph(d):
    """
    build a graph with the data gathered from the mesh in dict d
    """
    global graph ; graph = [] # initialize
    global cache ; cache = {} # initialize
    for i in sorted(d.keys(), key=lambda k: d[k]['id']):
        c = {}
        for w in "loadavg cpu_info cpu_meminfo hostname uid id uptime processes cpu_stat brctl vmstat".split(' '):
            if w in d[i]:
                c.update({w: d[i][w]})
            c.update({'ipv6': i})
        graph.append(c)
        if 'bmx6' in d[i] and 'interfaces' in d[i]['bmx6'] and 'links' in d[i]['bmx6']:
            add_links(d, graph[-1], d[i])
            if 'net_dev' in d[i]: add_net_dev(graph[-1], d[i]['net_dev'])

def si2f(x):
    n = x.find('K')
    if(n >= 0):  
        return float(x[:n]+'e3')
    n = x.find('M')
    if(n >= 0):  
        return float(x[:n]+'e6')
    n = x.find('G')
    if(n >= 0):  
        return float(x[:n]+'e9')

def build_rt(d):
    """
    build rt with the data gathered from the mesh in dict d
    """
    global tabs # initialize
    tabs = {}
    num_nodes = len(d) ;
    rt =[[None] * num_nodes for n in range(0,num_nodes)]
    adj =[[0] * num_nodes for n in range(0,num_nodes)]
    metric = [[None] * num_nodes for n in range(0,num_nodes)]
    uid = [None] * num_nodes
    for i in sorted(d.keys(), key=lambda k: d[k]['id']):
        nid = d[i]['id']
        uid[nid] = d[i]['uid']
        if 'originators' in d[i]['bmx6']:
            for o in d[i]['bmx6']['originators']:
                if 'primaryIp' in o:
                    n = find_node_by_address(d, 'inet6', o['primaryIp'])
                    if n:
                        if 'viaIp' in o:
                            via = find_node_by_address(d, 'inet6ll', o['viaIp'])
                            if via: 
                                rt[nid][n['id']] = via['id']
                                if n['id'] == via['id']: adj[nid][n['id']] = 1
                        if 'metric' in o:
                            metric[nid][n['id']] = si2f(o['metric'])
    tabs.update({'uid': uid})
    tabs.update({'rt': rt})
    tabs.update({'adj': adj})
    tabs.update({'metric': metric})
    tabs.update({'out_degree': [sum(x) for x in adj]})
    tabs.update({'in_degree': [sum(x) for x in zip(*adj)]})

def show(i):
    ""
    ""
    print(json.dumps(graph[i], indent=2))

# Local Variables:
# mode: python
# coding: utf-8
# python-indent-offset: 4
# python-indent-guess-indent-offset: t
# End:
