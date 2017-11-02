import sys
if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO


class TemplateSet(object):
    def __init__(self):
        self._templates = {}
        self._raw = {}

    def add(self, name, render, src):
        self._templates[name] = render
        self._raw[name] = src

    def has(self, name):
        return name in self._templates

    def get_source(self, name):
        return self._raw[name]

    def render(self, name, data, output, inner=None, embed_data=False):
        self._templates[name](self, data, output, inner, embed_data)

    def render_to_string(self, name, data):
        output = StringIO()
        self.render(name, data, output)
        return output.getvalue()
