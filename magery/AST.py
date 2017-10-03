from . import utils


class Raw(object):
    def __init__(self, value):
        self.value = value

    def __add__(self, other):
        return Raw(self.value + other.value)

    def __repr__(self):
        return "<Raw %s>" % repr(self.value)

    def to_python(self, result):
        result.writelines(["output.write(%s)\n" % repr(self.value)])


class Collection(object):
    def __init__(self, children=None):
        self.children = children or []

    def append(self, x):
        self.children.append(x)

    def collapse(self):
        collapsed = []
        for child in self.children:
            if collapsed:
                if isinstance(child, Raw) and isinstance(collapsed[-1], Raw):
                    collapsed[-1] += child
                    continue
            if isinstance(child, Collection):
                child.collapse()
                collapsed.append(child)
            else:
                collapsed.append(child)
        self.children = collapsed

    def __repr__(self):
        return "<Collection %s>" % repr(self.children)

    def to_python(self, result):
        for child in self.children:
            child.to_python(result)


class Template(Collection):
    def __init__(self, name, children=None):
        super(Template, self).__init__(children)
        self.name = name

    def __repr__(self):
        return "<Template %s %s>" % (self.name, repr(self.children))

    def to_python(self, result):
        result.writelines(['def fn(templates, data, output, inner):\n'])
        block = utils.IndentedIO(result)
        for child in self.children:
            child.to_python(block)
        result.writelines(['templates.add(%s, fn)\n' % repr(self.name), '\n'])
