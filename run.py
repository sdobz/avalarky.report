#!./marshall/env/bin/python

import os
import sys
sys.path.append(os.path.dirname(__file__))

from kyre.settings import load_settings
settings = load_settings(['avalarky.report.kyre', 'avalarky.report.secret.kyre'])

from marshall.pelican.horrible_monkey_patch import patch_pelican_settings
pelican_settings = patch_pelican_settings(settings['pelican'])

from marshall.everdown import run as everdown_run
everdown_run(settings['everdown'], pelican_settings)

from pelican import main
main()

from deploy import s3
s3.upload(settings['s3'], settings['pelican']['OUTPUT_PATH'])
