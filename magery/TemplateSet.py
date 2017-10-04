import sys
if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO


class TemplateSet(object):
    def __init__(self):
        self._templates = {}

    def add(self, name, render):
        self._templates[name] = render

    def has(self, name):
        return name in self._templates

    def render(self, name, data, output, inner=None):
        self._templates[name](self, data, output, inner)

    def render_to_string(self, name, data):
        output = StringIO()
        self.render(name, data, output)
        return output.getvalue()
