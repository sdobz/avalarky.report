#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.dirname(__file__))

import json

with open('avalarky.report.kyre') as f:
    settings = json.load(f)

from marshall.everdown import run as everdown_run
everdown_run(settings['everdown'])

from marshall.pelican.horrible_monkey_patch import patch_pelican_settings
patch_pelican_settings(settings['pelican'])

from pelican import main
sys.exit(main())