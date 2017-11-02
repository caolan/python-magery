from glob import glob
import unittest
import json
import os
import magery
import html5lib
from codecs import open

from lxml.doctestcompare import LXMLOutputChecker
from doctest import Example


class LHTML5OutputChecker(LXMLOutputChecker):
    def get_default_parser(self):
        return html5lib.parse


def assert_html_equal(got, want):
    checker = LHTML5OutputChecker()
    if not checker.check_output(want, got, 0):
        message = checker.output_difference(Example("", want), got, 0)
        raise AssertionError(message)


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
            expected = expected_file.read()
        data = json.loads(data_content)
        templates = magery.compile_templates(templatefile)
        result = templates.render_to_string('app-main', data)
        assert_html_equal(result, expected)
    return test


if __name__ == '__main__':
    # change to directory containing this module
    d = os.path.dirname(__file__)
    if d:
        os.chdir(d)

    # create a test function for each directory in portable test suite
    for filename in glob('magery-tests/components/*'):
        basename = os.path.basename(filename)

        test_func = make_test_function(basename, filename)
        klassname = 'Test_{0}'.format(basename)
        globals()[klassname] = type(
            klassname,
            (DynamicClassBase,),
            {'test_{0}'.format(basename): test_func}
        )

    # run unit tests
    unittest.main()
