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
                import_paths[module_name] = module_import_string
    return import_paths


def get_module(name):
    if name in module_cache:
        return module_cache[name]

    if name not in discovered_modules:
        # TODO: offer to download?
        log.error("Module: {} not discovered".format(name))
        return None

    try:
        module = importlib.import_module(discovered_modules[name])
    except ImportError:
        log.error("Error importing module: {}".format(discovered_modules[name]))
        return None

    module_cache[name] = module
    return module


def get_function(module_name, func_name):
    module = get_module(module_name)

    if not hasattr(module, func_name) or not hasattr(getattr(module, func_name), '__call__'):
        log.error("Module: {} does not have function: {}".format(module_name, func_name))
        return None

    return getattr(module, func_name)


def execute(settings):
    for key, value in settings.iteritems():
        # If the _key_ is an execution then run the referenced function and stop
        if isinstance(key, basestring) and key.startswith(EXECUTION_PREFIX):
            # Execution string is the key with the prefix stripped
            execution_string = key[len(EXECUTION_PREFIX):]
            execution_parts = execution_string.split('.')

            if len(execution_parts) <= 1:
                log.warning("Key: {} has execution prefix but is not a valid module+function")
                continue

            # Module is everything before the last . prefixed by the module directory
            module_str = '.'.join([EXECUTION_DIRECTORY] + execution_parts[:-1])
            # Func is everything after the last .
            func_str = execution_parts[-1]

            func = get_function(module_str, func_str)

            if isinstance(value, dict):
                func(**value)
            elif isinstance(value, list):
                func(*value)
            else:
                func(value)

        # If the _value_ is a dict (and the key is not an execution) try to execute its keys
        elif isinstance(value, dict):
            execute(value)

        # If the _value_ is a list (and the key is not an execution)
        # search through the items and if it is a dict try to execute its keys
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    execute(item)
