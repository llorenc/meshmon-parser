#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Format data gathered from qMp nodes in GuifiSants
## http://dsg.ac.upc.edu/qmpsu/index.php
## meshmon-common.py
## (c) Llorenç Cerdà-Alabern, May 2020.

import click   ## https://click.palletsprojects.com/en/7.x
import sys

verbose = False

def error(msg):
    click.secho(msg, fg="red")

def abort(msg):
    click.secho(msg, fg="red")
    sys.exit()

def say(msg):
    if not type(msg) is str:
        msg = str(msg)
    click.secho(msg, fg="green")

# Local Variables:
# mode: python
# coding: utf-8
# python-indent-offset: 4
# python-indent-guess-indent-offset: t
# End:
