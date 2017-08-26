from xml.dom import minidom
from collections import OrderedDict
import html5lib
import json
import io
import re

impl = minidom.getDOMImplementation()
document = impl.createDocument(None, "some_tag", None)


def write_node(node, out):
    walker = html5lib.getTreeWalker("dom")
    stream = walker(node)
    s = html5lib.serializer.HTMLSerializer()
    for txt in s.serialize(stream):
        out.write(txt)


class Template():
    def __init__(self, node, render):
        self.render = render
        self.node = node

    def write(self, data, out):
        embedded = {}
        root = self.render(data, embedded=embedded)
        write_node(root, out)
        template_tag = document.createElement('template')
        if embedded:
            for node in embedded.values():
                template_tag.appendChild(node)
            write_node(template_tag, out)

    def render_to_string(self, data):
        out = io.StringIO()
        self.write(data, out)
        result = out.getvalue() + "\n"
        out.close()
        return result


def to_string(x):
    if x is None:
        return ''
    elif type(x) == str or type(x) == unicode:
        return x
    elif type(x) == bool:
        return 'true' if x else 'false'
    elif type(x) == int or type(x) == float:
        return x.__str__()
    elif type(x) == list:
        return ','.join([to_string(y) for y in x]) if x else ''
    return '[object Object]'


def compile_lookup(path):
    path = path.strip()
    parts = re.split(r'\.', path)

    def render(data):
        for p in parts:
            if type(data) == dict:
                data = data.get(p)
            elif type(data) == list and p == 'length':
                data = len(data)
            else:
                return None
        return data

    return render


def compile_expand_vars(source):
    if not source:
        return None
    text = 1
    var = 2
    state = text
    parts = re.split(r'(\{\{|\}\})', source)
    results = []
    i = 0
    while i < len(parts):
        if state == text:
            if parts[i] == '{{':
                state = var
            elif parts[i] == '}}':
                raise Exception(
                    "Variable delimiter mismatch: unexpected '}}' in %s" %
                    source
                )
            elif parts[i]:
                results.append((lambda p: lambda _: p)(parts[i]))
        else:
            if parts[i] == '{{':
                raise Exception(
                    "Variable delimiter mismatch: unexpected '{{' in %s" %
                    source
                )
            elif parts[i] == '}}':
                results.append(compile_lookup(parts[i-1]))
                state = text
        i += 1

    if len(results) == 1:
        return results[0]

    def render(data):
        return "".join([to_string(f(data)) for f in results])

    return render


def compile_bool_test(source):
    expand = compile_expand_vars(source)

    def expand2(data):
        return is_truthy(expand(data))

    return expand2

def compile_node(node, templates):
    if node.nodeType == minidom.Node.TEXT_NODE:
        return compile_text(node.data)
    elif node.nodeType == minidom.Node.ELEMENT_NODE:
        if node.tagName == 'template-children':
            return expand_children
        return compile_element(node, templates)


def expand_children(data, parent, inner):
    if inner:
        inner(parent)


def compile_text(txt):
    expand = compile_expand_vars(txt)

    def render(data, parent, inner=None, embedded=None):
        node = document.createTextNode(to_string(expand(data)))
        parent.appendChild(node)
    return render


skipped_attrs = ('data-embed', 'data-each', 'data-if', 'data-unless')

# TODO: add remaining boolean attributes
boolean_attrs = ('selected')


def compile_element(node, templates):
    children = [compile_node(child, templates) for child in node.childNodes]
    tag = node.tagName
    attrs = OrderedDict()
    for k, v in node.attributes.items():
        if k == 'data-template':
            # replace data-template with data-bind to distinguish from
            # rendered template and template definition
            attrs[u'data-bind'] = compile_expand_vars(v)
        elif k in boolean_attrs:
            attrs[k] = compile_bool_test(v)
        elif k not in skipped_attrs:
            attrs[k] = compile_expand_vars(v)

    def render(data, parent=None, inner=None, embedded=None):
        if templates.get(tag):
            data2 = {}
            for k, v in attrs.items():
                data2[k] = compile_lookup(v(data))(data)

            def inner2(parent):
                for child in children:
                    child(data, parent, inner)
            return templates[tag].render(data2, parent, inner2, embedded)
        else:
            el = document.createElement(tag)
            for k, v in attrs.items():
                if k in boolean_attrs:
                    if v(data):
                        el.setAttribute(k, '')
                else:
                    el.setAttribute(k, to_string(v(data)))
            for child in children:
                child(data, el, inner)
            if parent:
                parent.appendChild(el)
            # if not parent or tag == 'body':
            return el

    if node.getAttribute('data-embed') == 'true':
        render = compile_embed(node, render)
    if node.hasAttribute('data-template'):
        templates[node.getAttribute('data-template')] = Template(node, render)
    if node.hasAttribute('data-unless'):
        render = compile_unless(node, render)
    if node.hasAttribute('data-if'):
        render = compile_if(node, render)
    if node.hasAttribute('data-each'):
        render = compile_each(node, render)
    return render


def compile_embed(node, render):
    def render2(data, parent=None, inner=None, embedded=None):
        el = render(data, parent, inner)
        el.setAttribute(
            u'data-context',
            json.dumps(data, separators=(',', ':'))
        )
        if embedded is not None:
            embedded[node.getAttribute('data-template')] = node
        return el
    return render2


def is_falsy(x):
    return (x is False or x is None or x == [] or x == 0 or x == '')


def is_truthy(x):
    return not is_falsy(x)


def compile_if(node, render):
    get_value = compile_lookup(node.getAttribute('data-if'))

    def render2(data, parent, inner=None, embedded=None):
        if is_truthy(get_value(data)):
            parent.appendChild(render(data, parent, inner, embedded))
    return render2


def compile_unless(node, render):
    get_value = compile_lookup(node.getAttribute('data-unless'))

    def render2(data, parent, inner=None, embedded=None):
        if is_falsy(get_value(data)):
            parent.appendChild(render(data, parent, inner, embedded))
    return render2


def compile_each(node, render):
    parts = node.getAttribute('data-each').split(' in ')
    if len(parts) != 2:
        raise Exception(
            'Badly formed data-each attribute: %s' %
            node.getAttribute('data-each'))
    name = parts[0]
    get_items = compile_lookup(parts[1])

    def render2(data, parent, inner=None, embedded=None):
        items = get_items(data)
        if type(items) != list or len(items) == 0:
            return
        for item in items:
            data[name] = item
            render(data, parent, inner, embedded)
    return render2


def compile_templates(filename, templates=None):
    # avoid mutation of default arguments across multiple invocations
    if templates is None:
        templates = {}
    with open(filename, 'rb') as f:
        ##### TODO: try non DOM element API to see if it handles <html></html> tags better
        tree = html5lib.parse(f, treebuilder='dom')
    for node in tree.childNodes:
        compile_node(node, templates)
    return templates
