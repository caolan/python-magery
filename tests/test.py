from glob import glob
import unittest
import json
import os
import io
import magery
import html5lib
from codecs import open


def normalize_html(source):
    out = io.StringIO()
    tree = html5lib.parse(source, treebuilder='dom')
    walker = html5lib.getTreeWalker('dom')
    stream = walker(tree)
    s = html5lib.serializer.HTMLSerializer()
    for txt in s.serialize(stream):
        out.write(txt)
    result = out.getvalue()
    out.close()
    return result


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
        result = templates['main'].render_to_string(data)
        self.assertEqual(normalize_html(result), normalize_html(expected))
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
        globals()[klassname] = type(
            klassname,
            (DynamicClassBase,),
            {'test_{0}'.format(basename): test_func}
        )

    # run unit tests
    unittest.main()
