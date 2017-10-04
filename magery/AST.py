import io


class IndentedIO(io.IOBase):
    def __init__(self, wrapped):
        self.wrapped = wrapped

    def writelines(self, lines):
        self.wrapped.writelines(["    " + line for line in lines])


class Raw(object):
    def __init__(self, value):
        self.value = value

    def __add__(self, other):
        # do not co-erce any other type (including subclasses) to Raw
        assert(type(other) == Raw)
        return Raw(self.value + other.value)

    def __repr__(self):
        return "<Raw %s>" % repr(self.value)

    def to_python(self, result):
        if self.value:
            result.writelines([
                "output.write(%s)\n" % repr(self.value)
            ])


class Variable(object):
    def __init__(self, path):
        self.path = path

    def __repr__(self):
        return "<Variable %s>" % self.path

    def to_python(self, result):
        result.writelines([
            "output.write(runtime.html_escape(runtime.to_string(runtime.lookup(data, %s))))\n"
            % repr(self.path)
        ])


class Collection(object):
    def __init__(self):
        self.children = []

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
    def __init__(self, name):
        super(Template, self).__init__()
        self.name = name

    def __repr__(self):
        return "<Template %s %s>" % (self.name, repr(self.children))

    def to_python(self, result):
        result.writelines(['def fn(templates, data, output, inner):\n'])
        block = IndentedIO(result)
        for child in self.children:
            child.to_python(block)
        result.writelines(['templates.add(%s, fn)\n' % repr(self.name), '\n'])


class If(Collection):
    def __init__(self, path):
        super(If, self).__init__()
        self.path = path

    def __repr__(self):
        return "<If %s %s>" % (self.path, repr(self.children))

    def to_python(self, result):
        result.writelines([
            'if runtime.lookup(data, %s):\n' % repr(self.path)
        ])
        block = IndentedIO(result)
        for child in self.children:
            child.to_python(block)


class Unless(Collection):
    def __init__(self, path):
        super(Unless, self).__init__()
        self.path = path

    def __repr__(self):
        return "<Unless %s %s>" % (self.path, repr(self.children))

    def to_python(self, result):
        result.writelines([
            'if not runtime.lookup(data, %s):\n' % repr(self.path)
        ])
        block = IndentedIO(result)
        for child in self.children:
            child.to_python(block)


class Each(Collection):
    def __init__(self, name, path):
        super(Each, self).__init__()
        self.name = name
        self.path = path

    def __repr__(self):
        return "<Each %s in %s %s>" % (
            self.name, self.path, repr(self.children))

    def to_python(self, result):
        # create a named function in place of a multi-line lambda,
        # this is to work around Python's unintuitive scoping of
        # for-loops
        result.writelines(['def fn(data):\n'])
        block = IndentedIO(result)
        for child in self.children:
            child.to_python(block)
        # call named function for each iteration
        result.writelines([
            'runtime.each(data, %s, %s, fn)\n' %
            (repr(self.name), repr(self.path))
        ])


class TemplateCall(Collection):
    def __init__(self, name, context):
        super(TemplateCall, self).__init__()
        self.name = name
        self.context = context

    def __repr__(self):
        return "<TemplateCall %s %s>" % (repr(self.name), repr(self.context))

    def to_python(self, result):
        def attr_value_to_python(value):
            if len(value) == 1:
                if type(value[0]) == Variable:
                    return "runtime.lookup(data, %s)" % repr(value[0].path)
                else:
                    return repr(value[0].value)

            parts = []
            for part in value:
                if type(part) == Variable:
                    parts.append(
                        "runtime.to_string(runtime.lookup(data, %s))" %
                        repr(part.path)
                    )
                else:
                    parts.append(repr(part.value))
            return " + ".join(parts)

        if self.children:
            result.writelines(['def fn():\n'])
            block = IndentedIO(result)
            block = super(TemplateCall, self).to_python(block)

        if self.context:
            result.writelines([
                'runtime.render(templates, %s, {\n' % repr(self.name)
            ])
            block = IndentedIO(result)
            block.writelines([
                "%s: %s,\n" % (repr(k), attr_value_to_python(v))
                for k, v in self.context.items()
            ])

            if self.children:
                result.writelines(['}, output, fn)\n'])
            else:
                result.writelines(['}, output, inner)\n'])
        else:
            if self.children:
                result.writelines([
                    'runtime.render(templates, %s, data, output, fn)\n' %
                    repr(self.name)
                ])
            else:
                result.writelines([
                    'runtime.render(templates, %s, data, output, inner)\n' %
                    repr(self.name)
                ])

class TemplateChildren(object):
    def to_python(self, result):
        result.writelines(['if inner is not None:\n'])
        block = IndentedIO(result)
        block.writelines(['inner()\n'])


class EmbeddedData(object):
    def to_python(self, result):
        result.writelines([
            'output.write(runtime.html_escape(runtime.encode_json(data)))\n'
        ])
