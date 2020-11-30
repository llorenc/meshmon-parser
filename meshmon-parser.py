# -*- coding: utf-8 -*-
## Parser data gathered from qMp nodes in GuifiSants
## http://dsg.ac.upc.edu/qmpsu/index.php
## meshmon-parser.py
## (c) Llorenç Cerdà-Alabern, May 2020.
## debug: import pdb; pdb.set_trace()

import re, gzip, os, sys, json
import warnings

if os.path.exists(os.environ['HOME'] + 'recerca/connexio-guifinet/meshmon'):
    os.chdir(os.environ['HOME'] + 'recerca/connexio-guifinet/meshmon')
elif os.path.exists(os.environ['HOME'] + 'sert/meshmon/'):
    os.chdir(os.environ['HOME'] + 'sert/meshmon/')

qmpdb = dict()  # nested_dict()
gathercount = 0

def qmpdb_update(ipv6, what):
    global qmpdb
    global gathercount
    if(ipv6 in qmpdb):
        for k in what.keys():
            if(k in qmpdb[ipv6]):
                qmpdb[ipv6][k].update(what[k])
            else:
                qmpdb[ipv6].update(what)
    else:
        qmpdb.update({ipv6: what})
        qmpdb[ipv6].update({'id': gathercount})
        gathercount += 1

##
## parse sections
##
def parse_hostname(ipv6, content):
    """
    """
    qmpdb_update(ipv6, {'hostname' : content.strip()})
    # print(qmpdb[ipv6])

def parse_cpu_stat(ipv6, content):
    """
    http://www.linuxhowtos.org/System/procstat.htm
    """
    fields = "user nice system idle iowait irq softirq".split(' ')
    pat = "^cpu"
    for f in fields: pat += "\s+(?P<" + f + ">\d+)"
    rx_pat = re.compile(pat, re.MULTILINE | re.VERBOSE)
    match = rx_pat.search(content)
    ## {f : match.group(f) for f in fields}
    if match:
        qmpdb_update(ipv6, {'cpu_stat' : {f : float(match.group(f)) for f in fields}})
    else:
        warnings.warn("cpu_stat " + ipv6 + "?")
    ##
    fields = "intr ctxt btime".split(' ')
    pat=""
    for f in fields: pat += "^" + f + "\s+(?P<" + f + ">\d+)\s[\s\S]*"
    rx_pat = re.compile(pat, re.MULTILINE | re.VERBOSE)
    match = rx_pat.search(content)
    if match:
        qmpdb_update(ipv6, {'cpu_stat' : {f : float(match.group(f)) for f in fields}})

def parse_cpu_info(ipv6, content):
    """
    """
    fields = "system machine cpu BogoMIPS".split(' ')
    pat = ""
    for f in fields: pat += "[\s\S]*^" + f + ".*:\s(?P<" + f + ">.+)$"
    rx_pat = re.compile(pat, re.MULTILINE | re.VERBOSE)
    match = rx_pat.search(content)
    if match:
        qmpdb_update(ipv6, {'cpu_info' : {f : match.group(f) for f in fields}})
    else:
        warnings.warn("cpu_info " + ipv6 + "?")

def parse_net_dev(ipv6, content):
    """
    """
    pat = "^\s*(?P<dev>\S+):"
    rx_fields = "rx_bytes rx_packets rx_errors".split(' ')
    for f in rx_fields: pat += "\s+(?P<" + f + ">\d+)"
    pat += "\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+"
    tx_fields = "tx_bytes tx_packets tx_errors".split(' ')
    for f in tx_fields: pat += "\s*(?P<" + f + ">\d+)"
    pat += '.*$'
    rx_pat = re.compile(pat, re.MULTILINE | re.VERBOSE)
    for d,rxb,rxp,rxe,txb,txp,txe in re.findall(rx_pat, content):
        # if float(rxp) > 0 or float(txp) > 0:
        qmpdb_update(ipv6, {'net_dev': 
                            {d: {'rxb': float(rxb), 'rxp': float(rxp), 'rxe': float(rxe), 
                                 'txb': float(txb), 'txp': float(txp), 'txe': float(txe)}}})

def parse_loadavg(ipv6, content):
    """
    https://stackoverflow.com/questions/11987495/linux-proc-loadavg
    """
    fields = "m1 m5 m15".split(' ')
    pat="^"
    for f in fields: pat += "\s*(?P<" + f + ">\d+\.\d+)\s"
    rx_pat = re.compile(pat, re.VERBOSE)
    match = rx_pat.search(content)
    if match:
        qmpdb_update(ipv6, {'loadavg' : {f : float(match.group(f)) for f in fields}})

def parse_meminfo(ipv6, content):
    """
    https://www.thegeekdiary.com/understanding-proc-meminfo-file-analyzing-memory-utilization-in-linux/
    taken from munin:
    apps        Memory used by user-space applications.
    page_tables Memory used to map between virtual and physical memory addresses.
    swap_cache  A piece of memory that keeps track of pages that have been fetched from swap but not yet been modified.
    slab_cache  Memory used by the kernel (major users are caches like inode, dentry, etc).
    vmalloc_used 'VMalloc' (kernel) memory used
    committed   The amount of memory allocated to programs. Overcommitting is normal, but may indicate memory leaks.
    mapped      All mmap()ed pages.
    active      Memory recently used. Not reclaimed unless absolutely necessary.
    inactive    Memory not currently used.
    shmem       Shared Memory (SYSV SHM segments, tmpfs).
    cached       Parked file data (file content) cache.
    buffers     Block device (e.g. harddisk) cache. Also where "dirty" blocks are stored until written.
    swap        Swap space used.
    free        Wasted memory. Memory that is not used for anything at all.
    """
    varval = {}
    rx_vv = re.compile(r'''
    ^(?P<var>[\w()]+):\s*(?P<val>\d+?)\skB
    ''', re.MULTILINE | re.VERBOSE)
    for var,val in ((line.group('var'), line.group('val')) 
              for line in rx_vv.finditer(content)):
        varval.update({var : float(val)*1024})
    ##
    apps = varval['MemTotal'] - varval['MemFree'] - varval['Buffers'] - varval['Cached'] -\
        varval['Slab'] - varval['SwapCached'] - varval['PageTables'] - varval['VmallocUsed']
    qmpdb_update(ipv6, {'cpu_meminfo' : {'apps' : apps}})
    qmpdb_update(ipv6, {'cpu_meminfo' : {'page_tables' : varval['PageTables']}})
    qmpdb_update(ipv6, {'cpu_meminfo' : {'swap_cache' : varval['SwapCached']}})
    qmpdb_update(ipv6, {'cpu_meminfo' : {'slab_cache' : varval['Slab']}})
    qmpdb_update(ipv6, {'cpu_meminfo' : {'vmalloc_used' : varval['VmallocUsed']}})
    qmpdb_update(ipv6, {'cpu_meminfo' : {'committed' : varval['Committed_AS']}})
    qmpdb_update(ipv6, {'cpu_meminfo' : {'mapped' : varval['Mapped']}})
    qmpdb_update(ipv6, {'cpu_meminfo' : {'active' : varval['Active']}})
    qmpdb_update(ipv6, {'cpu_meminfo' : {'active_anon' : varval['Active(anon)']}})
    qmpdb_update(ipv6, {'cpu_meminfo' : {'active_file' : varval['Active(file)']}})
    qmpdb_update(ipv6, {'cpu_meminfo' : {'inactive' : varval['Inactive']}})
    qmpdb_update(ipv6, {'cpu_meminfo' : {'shmem' : varval['Shmem']}})
    qmpdb_update(ipv6, {'cpu_meminfo' : {'cached' : varval['Cached']}})
    qmpdb_update(ipv6, {'cpu_meminfo' : {'buffers' : varval['Buffers']}})
    qmpdb_update(ipv6, {'cpu_meminfo' : {'swap' : varval['SwapTotal']-varval['SwapFree']}})
    qmpdb_update(ipv6, {'cpu_meminfo' : {'free' : varval['MemFree']}})

def parse_uptime(ipv6, content):
    """
    uptime in seconds
    """
    qmpdb_update(ipv6, {'uptime' : float(content.split()[0])})

def parse_processes(ipv6, content):
    """
    number of running processes
    """
    qmpdb_update(ipv6, {'processes' : float(content)})

def parse_bmx6(ipv6, content):
    """
    https://github.com/bmx-routing/bmx6/blob/master/README.md
    credits: https://stackoverflow.com/questions/38211773/how-to-get-an-expression-between-balanced-parentheses
    """
    content = content.replace('\/', '/')
    stack = 0
    startIndex = None
    results = {}
    originators = []
    for i, c in enumerate(content):
        if c == '{':
            if stack == 0:
                startIndex = i
            stack += 1 # push to stack
        elif c == '}':
            stack -= 1 # pop stack
            if stack == 0:
                try:                    
                    field = json.loads(content[startIndex:i+1])
                except:
                    warnings.warn("parse_bmx6: json.loads")
                    field = None
                if field:
                    if 'blocked' in field.keys():
                        originators.append(field)
                    else:                       
                        if not 'OPTIONS' in field:
                            results.update(field)
    if originators:
        results.update({'originators': originators})
        qmpdb_update(ipv6, {'bmx6' : results})

def parse_addresses_section(content):
    """
    """
    res = {}
    rx_pat = re.compile("""
    ^\s+link/ether\s(?P<ether>[\w:]+)|
    ^\s+inet\s(?P<inet>10[\w:.]+)|
    ^\s+inet6\s(?P<inet6>fd66[\w:]+)|
    ^\s+inet6\s(?P<inet6ll>fe80[\w:]+)
    """, re.MULTILINE | re.VERBOSE)
    for field,add in ((f, m.group(f)) 
                      for f in ['ether', 'inet', 'inet6', 'inet6ll']
                      for m in rx_pat.finditer(content)):
        if add and add != '00:00:00:00:00:00':
            if field in res.keys():
                if not add in res[field]:
                    res[field].append(add)
            else:
                res.update({field: [add]})
    return res

def parse_addresses(ipv6, content):
    """
    """
    rx_section = re.compile(r'''
    ^\d+:.*BROADCAST.*
    (?P<section_content>[\s\S]+?)
    (?=^\d+|\Z)
    ''', re.MULTILINE | re.VERBOSE)
    res = {}
    for c in (section.group('section_content')
              for section in rx_section.finditer(content)):
        data = parse_addresses_section(c)
        if data:
            for field in data.keys():
                if field in res.keys():
                    res[field] = list(set(res[field])|set(data[field]))
                else:
                    res.update({field: data[field]})
    if res:
        qmpdb_update(ipv6, {'addresses': res})

def parse_iwdump_section(content):
    """
    """
    varval = {}
    rx_vv = re.compile(r'''
    ^\s+(?P<var>[\s\w]+):\s*(?P<val>\d+\.\d+|-*\d+)\D
    ''', re.MULTILINE | re.VERBOSE)
    for var,val in ((line.group('var'), line.group('val')) 
                    for line in rx_vv.finditer(content)):
        varval.update({var : float(val)})
    ##
    return varval

def parse_iwdump(ipv6, content):
    """
    """
    rx_section = re.compile(r'''
    ^Station\s(?P<section_name>[\w:]+)\s\(on\s(?P<if_name>\w+)\)
    (?P<section_content>[\s\S]+?)
    (?=^Station\s|\Z)
    ''', re.MULTILINE | re.VERBOSE)
    res = {}
    for s,i,c in ((section.group('section_name'), section.group('if_name'), section.group('section_content'))
              for section in rx_section.finditer(content)):
        data = parse_iwdump_section(c)
        if i in res: res[i].update({s: data})
        else: res.update({i: {s: data}})
    if res: qmpdb_update(ipv6, {'iwdump': res})

def parse_brctl(ipv6, content):
    """
    """
    rx_section = re.compile(r'''
    (?:(?P<br>^[\w-]+).*|^\s*)\s(?P<ifce>[\S]+$)
    ''', re.MULTILINE | re.VERBOSE)
    res = {}
    br = None
    for b,i in ((line.group('br'), line.group('ifce'))
              for line in rx_section.finditer(content)):
        if b == 'bridge': continue
        if b and i:
            br = b
            res.update({br: [i]})
        elif br in res and i:
            res[br].append(i)
    if res: qmpdb_update(ipv6, {'brctl': res})

def parse_vmstat(ipv6, content):
    """
    """
    varval = {}
    rx_vv = re.compile(r'''
    ^(?P<var>[\w]+)\s+(?P<val>\d+)\D
    ''', re.MULTILINE | re.VERBOSE)
    for var,val in ((line.group('var'), line.group('val')) 
                    for line in rx_vv.finditer(content)):
        varval.update({var : int(val)})
    ##
    if varval: qmpdb_update(ipv6, {'vmstat': varval})

##
## find sections
##
def find_section(ipv6, name, content):
    """
    """
    # print(name)
    # print(content)
    parse_func = "parse_%s" % name
    try:
        if callable(getattr(sys.modules[__name__], parse_func)):
            getattr(sys.modules[__name__], parse_func)(ipv6, content)
    except:
        # print(parse_func + ": not in scope!")
        pass

def find_node(name, content):
    """
    """
    # rx_name = re.compile(r'''(?P<ipv6>[0-9a-fA-F][0-9a-fA-F:])+\s\((?P<name>\S+)\)\s''')
    (ipv6, nname, _) = re.split(r'[\s()]+', name, 2)
    # print(ipv6)
    rx_section = re.compile(r'''
    ^\#\#\sstart\s(?P<section_name>.+$)
    (?P<section_content>[\s\S]+?)
    (?=^\#\#\sstart\s|\Z)
    ''', re.MULTILINE | re.VERBOSE)
    for s,c in ((section.group('section_name'), section.group('section_content'))
              for section in rx_section.finditer(content)):
        find_section(ipv6, s,c)

def parse_file(filepath):
    global qmpdb
    global gathercount
    if(re.search(r'gz$', filepath)): 
        string = gzip.open(filepath).read()
    else: 
        string = open(filepath).read()
    qmpdb = dict()  # initialize
    gathercount = 0 # initialize
    rx_node = re.compile(r'''
    ^\#\sstart\s(?P<node_name>.+$)
    (?P<node_content>[\s\S]+?)
    (?=^\#\sstart\s |\Z)
    ''', re.MULTILINE | re.VERBOSE)
    for n,c in ((node.group('node_name'), node.group('node_content'))
              for node in rx_node.finditer(string)):
        find_node(n,c)
##
##
##
def print_qmpdb(what=None):
    for n in qmpdb:
        print(n)
        for s in qmpdb[n]:
            if(what == None or s == what):
                print("\t%s: %s" % (s, qmpdb[n][s]))

def print_keys(d, pref=None):
    for k in d.keys():
        if type(d[k]) is dict:
            if pref:
                print_keys(d[k], pref+'.'+k)
            else:
                print_keys(d[k], k)
        else:
            if type(d[k]) is float:
                if pref:
                    print("%s.%s: %f" % (pref, k, d[k]))
                else:
                    print("%s: %f" % (k, d[k]))
            elif type(d[k]) is str:
                print("%s: %s" % (k, d[k]))

##
## testing
##
## debug: import pdb; pdb.set_trace()

# interrupts
# bmx6_tunnels
# qmpversion
# default-gw
# community-gw
# iwinfo
# netstat
# df

# Local Variables:
# mode: python
# coding: utf-8
# python-indent-offset: 4
# python-indent-guess-indent-offset: t
# End:
