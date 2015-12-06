#!./.env/bin/python

import os
import sys
sys.path.append(os.path.dirname(__file__))

import json

with open('avalarky.report.kyre') as f:
    settings = json.load(f)

with open('avalarky.report.secret.kyre') as f:
    settings.update(json.load(f))

from marshal.pelican.horrible_monkey_patch import patch_pelican_settings
pelican_settings = patch_pelican_settings(settings['pelican'])

from marshal.everdown import run as everdown_run
everdown_run(settings['everdown'], pelican_settings)

from pelican import main
main()

from deploy import s3
s3.upload(settings['s3'], settings['pelican']['OUTPUT_PATH'])
