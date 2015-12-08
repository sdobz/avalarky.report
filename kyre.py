#!.env/bin/python

import sys
import logging
from modules.kyre import setup_execution, execute_files
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

setup_execution(prefix='~',
                directory='modules')

if __name__ == '__main__':
    settings_files = sys.argv[1:]
    if len(settings_files) == 0:
        print "Usage: {} <settings.kyre> <additional settings.kyre> ...".format(sys.argv[0])
        sys.exit(1)

    execute_files(settings_files)
