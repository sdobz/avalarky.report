from execution import get_module
# Dependency injection??


def inject(*module_names):
    """
    Use this decorator to inject a module dependency into your function

    from kyre import inject
    @inject('cache', 'db')
    def process_data(cache, db, arg1, arg2):
        pass

    :param module_names: module names to inject
    :rtype func:
    """
    # Decorator with arguments returns an actual decorator
    # f = (inject('modulename'))(f)
    def wrap(f):
        # Decorators work like so:
        # f = wrap(f)

        # Wrap returns a function that accepts any arguments, and calls the original function with the modules prepended
        def injected_func(*real_args, **real_kwargs):
            # Load the modules as a list
            modules = [get_module(name) for name in module_names]
            # Combine the module list with the real argument list
            new_args = modules + list(real_args)
            # Call the original function and return its result
            return f(*new_args, **real_kwargs)
        return injected_func
    return wrap
