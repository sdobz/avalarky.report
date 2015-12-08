import importlib
import os
from logging import getLogger
log = getLogger(__name__)

# Is this the right way to do this??
# Default values:
EXECUTION_PREFIX = '!'
REFERENCE_PREFIX = '{{'
REFERENCE_SUFFIX = '}}'
EXECUTION_DIRECTORY = 'modules'

module_cache = {}
discovered_modules = {}


def setup(execution_prefix=EXECUTION_PREFIX,
          reference_prefix=REFERENCE_PREFIX,
          reference_suffix=REFERENCE_SUFFIX,
          execution_directory=EXECUTION_DIRECTORY):

    # Update the values
    global EXECUTION_PREFIX, REFERENCE_PREFIX, REFERENCE_SUFFIX, EXECUTION_DIRECTORY
    EXECUTION_PREFIX = execution_prefix
    REFERENCE_PREFIX = reference_prefix
    REFERENCE_SUFFIX = reference_suffix
    EXECUTION_DIRECTORY = execution_directory

    global discovered_modules
    discovered_modules = discover_modules()


def discover_modules():
    import_paths = {}
    for root, dirs, files in os.walk(EXECUTION_DIRECTORY):
        # Finds the last component, modules/vendor/name -> name
        module_name = os.path.split(root)[1]
        for file in files:
            if file == '__init__.py':
                module_import_string = root.replace(os.sep, '.')
                log.info("Discovered module {} -> {}".format(module_name, module_import_string))
                import_paths[EXECUTION_PREFIX + module_name] = module_import_string
    return import_paths


def execute(settings):
    if hasattr(settings, '__iter__'):
        if not hasattr(settings, 'iteritems'):
            for item in settings:
                execute(item)
        else:
            iteritems = settings.iteritems()
            assert hasattr(iteritems, '__call__')
            for key, value in settings.iteritems():
                if not execute_key_if_func(key, value)


def execute_key_if_func(key, value):
    # If the _key_ is an execution then run the referenced function and stop
    if not isinstance(key, basestring) or not key.startswith(EXECUTION_PREFIX):
        return False

    try:
        module_str, func_str = key.split('.')
    except ValueError:
        # It couldn't unpack it, so didn't have exactly one .
        return False

    module = get_module(module_str)
    if not module:
        return False

    func = get_function(module_str, func_str)
    if not func:
        return False

    call_func_with_arguments(func, value)

    return True


def get_module(name):
    if name in module_cache:
        return module_cache[name]

    if name not in discovered_modules:
        return None

    try:
        module = importlib.import_module(discovered_modules[name])
    except ImportError:
        log.error("Error importing module: {}".format(discovered_modules[name]))
        return None

    module_cache[name] = module
    return module


def get_function(module_str, func_str):
    module = get_module(module_str)

    if not module:
        return None

    if not hasattr(module, func_str) or not hasattr(getattr(module, func_str), '__call__'):
        log.error("Module: {} does not have function: {}".format(module_str, func_str))
        return None

    return getattr(module, func_str)


def call_func_with_arguments(func, value):
    if isinstance(value, dict):
        func(**value)
    elif isinstance(value, list):
        func(*value)
    else:
        func(value)
