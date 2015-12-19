# Pytest make recursive, match test*.py
import re
test_file = re.compile('test.*\\.py')


def pytest_collect_file(path, parent):
    if test_file.match(path.basename):
        return parent.Module(path, parent)
