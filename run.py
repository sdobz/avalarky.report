#!/bin/bash

import os
import sys
sys.path.append(os.path.dirname(__file__))

import json

with open('avalarky.report.kyre') as f:
    settings = json.load(f)

from marshall.everdown import run as everdown_run
everdown_run(settings['everdown'])