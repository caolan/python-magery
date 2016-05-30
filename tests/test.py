from glob import glob
import unittest
import json
import os
import magery
from codecs import open


class DynamicClassBase(unittest.TestCase):
    longMessage = True
    maxDiff = None

def make_test_function(description, path):
    def test(self):
        datafile = os.path.join(path, 'data.json')
        templatefile = os.path.join(path, 'template.html')
        expectedfile = os.path.join(path, 'expected.html')
        with open(datafile, 'r', encoding='utf-8') as data_file:
            data_content = data_file.read()
        with open(expectedfile, 'r', encoding='utf-8') as expected_file:
            expected_content = expected_file.read()
        data = json.loads(data_content)
        templates = magery.loadFile(templatefile)
        result = magery.render_to_string(templates, 'main', data)
        self.assertEqual(result, expected_content)
    return test

if __name__ == '__main__':
    # change to directory containing this module
    d = os.path.dirname(__file__)
    if d:
        os.chdir(d)

    # create a test function for each directory in portable test suite
    for filename in glob('magery-tests/base/valid/*'):
        basename = os.path.basename(filename)

        test_func = make_test_function(basename, filename)
        klassname = 'Test_{0}'.format(basename)
        globals()[klassname] = type(klassname,
                                   (DynamicClassBase,),
                                   {'test_{0}'.format(basename): test_func})

    # run unit tests
    unittest.main()

