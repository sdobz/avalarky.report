#!.env/bin/python

import sys
from modules.kyre import setup, load_settings, dereference_settings, execute

setup(execution_prefix='!',
      reference_prefix='{{',
      reference_suffix='}}',
      execution_directory='modules')

if __name__ == '__main__':
    settings_files = sys.argv[1:]
    if len(settings_files) == 0:
        print "Usage: {} <settings.kyre> <additional settings.kyre> ...".format(sys.argv[0])
        sys.exit(1)

    settings = load_settings(settings_files)
    dereference_settings(settings)
    execute(settings)
