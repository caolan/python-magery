import funcparserlib.parser as p
from codecs import open
from functools import *
import re
import io

try:
    # Python 3
    from html import escape
except ImportError:
    # Python 2
    from cgi import escape


def whitespace_only(string):
    return re.match(r'^\s*$', string)

class BlockTag(object):
    def __init__(self, xs):
        name, params, children, closing = xs
        if closing != name:
            raise Exception(
                "Mismatched template tags: {{#%s}} and {{/%s}}" %
                (name, closing))
        self.name = name
        self.args = group_positional_parameters(params)
        self.kwargs = group_keyword_parameters(params)
        # remove first child if it's whitespace only
        if len(children) > 1 and \
           type(children[0]) == str and \
           whitespace_only(children[0]):
            children[0] = None
        self.children = [x for x in children if x != None]

    def __repr__(self):
        return "<magery.BlockTag #%s>" % self.name

def self_closed_block_tag(xs):
    return BlockTag(xs + ([], xs[0]))

class Parameter(object):
    def __init__(self, xs):
        self.value = xs

class KeywordParameter(object):
    def __init__(self, xs):
        self.key = xs[0]
        self.value = xs[1]

class ElseTag(object):
    pass

class ExpandTag(object):
    pass

class EscapedTag(object):
    def __init__(self, value):
        self.value = value

class RawTag(object):
    def __init__(self, value):
        self.value = value

class Property(object):
    def __init__(self, xs):
        self.value = xs

class Text(object):
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return "<magery.Text %s>" % repr(self.value)

def group_positional_parameters(params):
    return [x for x in params if type(x) == Parameter]

def group_keyword_parameters(params):
    return {x.key: x.value for x in params if type(x) == KeywordParameter}

def tokenize(string):
    tokens = []
    parts = re.split('({{[{#/]?|[}/]}}?)', string)
    for i in range(0, len(parts)):
        if i % 2 == 0:
            # split strings into separate chars
            tokens += parts[i]
        else:
            # keep {{#, {{/, }} etc. tokens without splitting
            tokens.append(parts[i])
    return tokens

def replace(v):
    return lambda x: v

def string(v):
    return reduce(lambda a, b: a + b, [p.a(c) for c in v]) >> replace(v)

def flatten_string(xs):
    if hasattr(xs, '__iter__') and type(xs) != str:
        return "".join(map(flatten_string, xs))
    return xs

def flatten_results(xs):
    results = []
    for x in xs:
        if type(x) == list or type(x) == tuple:
            results += flatten_results(x)
        elif x != None:
            results.append(x)
    return results

def enclosed_by(start, x, end):
    return p.skip(p.a(start)) + x + p.skip(p.a(end))

def regex(pattern):
    return p.some(lambda x: re.match(pattern, x))

anychar = p.some(lambda x: len(x) == 1)
anychars = p.oneplus(anychar) >> flatten_string
letter = regex(r'[A-Za-z]')
whitespace = regex(r'\s')
skip_whitespaces = p.skip(p.many(whitespace))

prop_char = regex(r'[^\s"\.=}/]')
prop = p.oneplus(
        (p.skip(p.a('.')) | regex(r'[A-Za-z]')) +
        p.many(prop_char) >> flatten_string) >> Property

value = prop
keyword = letter + p.many(regex(r'[A-Za-z0-9_]')) >> flatten_string
keyword_parameter = keyword + p.skip(p.a('=')) + value >> KeywordParameter
parameter = value >> Parameter

tag_name = p.oneplus(regex(r'[A-Za-z-:_]')) >> flatten_string
tag_parameter = keyword_parameter | parameter
tag_parameters = p.many(p.skip(p.oneplus(whitespace)) + tag_parameter)

block = p.forward_decl()

tag_self_close = enclosed_by('{{#', tag_name + tag_parameters + skip_whitespaces, '/}}')
tag_open = enclosed_by('{{#', tag_name + tag_parameters, '}}')
tag_close = enclosed_by('{{/', tag_name, '}}')

self_close_block = tag_self_close >> self_closed_block_tag
full_block = tag_open + p.many(block) + tag_close >> BlockTag
block_tag = self_close_block | full_block

else_tag = enclosed_by('{{', string('else'), '}}') >> replace(ElseTag())
expand_tag = enclosed_by('{{', string('...'), '}}') >> replace(ExpandTag())
raw_var_tag = enclosed_by(
    '{{{', skip_whitespaces + prop + skip_whitespaces, '}}}') >> RawTag
escaped_var_tag = enclosed_by(
    '{{', skip_whitespaces + prop + skip_whitespaces, '}}') >> EscapedTag

text = anychars >> flatten_string >> Text

block.define(
    else_tag |
    expand_tag |
    block_tag |
    raw_var_tag |
    escaped_var_tag |
    text
)

define_blocks = p.many(skip_whitespaces + block)
templates = define_blocks + skip_whitespaces + p.finished >> flatten_results

def walk_nodes(nodes):
    for node in nodes:
        yield node
        if type(node) == BlockTag:
            for child in walk_nodes(node.children):
                yield child

def find_lines(nodes):
    line = []
    for node in walk_nodes(nodes):
        line.append(node)
        if type(node) == Text and '\n' in node.value:
            yield line
            line = [node]

# lines which only contain template tags and whitespace should be removed
# NOTE: this function mutates the underlying nodes
def clean_line(line):
    remove_text = True
    first = line[0]
    last = line[len(line) - 1]
    # test if this line consists of only template tags and/or whitespace
    for node in line:
        # first item in line
        if type(node) == Text:
            if node == first:
                if not re.search(r'\n?[\t ]*$', node.value):
                    remove_text = False
            # last item in line
            elif node == last:
                if not re.search(r'^[\t ]*\n', node.value):
                    remove_text = False
            else:
                if re.search(r'\S', node.value):
                    # text node has non-whitespace chars
                    remove_text = False
        elif type(node) != BlockTag and \
             type(node) != ElseTag and \
             type(node) != ExpandTag:
            remove_text = False
    # if only template tags and whitespace
    # remove all whitespace from current line
    if remove_text:
        for node in line:
            if type(node) == Text:
                if node == first:
                    node.value = re.sub(r'\n[\t ]*$', '\n', node.value)
                    node.value = re.sub(r'[\t ]*$', '', node.value)
                elif node == last:
                    node.value = re.sub(r'^[\t ]*\n', '', node.value)
                else:
                    node.value = ''

def parse(source):
    nodes = templates.parse(tokenize(source))
    for line in find_lines(nodes):
        clean_line(line)
    return nodes

def load(source):
    blocks = parse(source)
    return {'.'.join(b.args[0].value.value): b.children for b in blocks}

def loadFile(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return load(f.read())

class MageryError(Exception):
    pass

def lookup(data, path):
    for prop in path:
        if prop != '':
            if prop == 'length' and type(data) == list:
                data = len(data)
            else:
                data = data and data.get(prop)
    return data

def to_string(data):
    if type(data) == list:
        return u",".join(data)
    elif type(data) == bool:
        if data == True:
            return u"true"
        else:
            return u"false"
    elif type(data) == dict:
        if data:
            return u"[object Object]"
        else:
            return u""
    elif data == None:
        return u""
    else:
        return u"%s" % data

def render_each_block(templates, block, data, inners, output):
    data = lookup(data, block.args[0].value.value)
    if data:
        for x in data:
            render_consequent(templates, block.children, x, inners, output)
    else:
        render_alternative(templates, block.children, data, inners, output)

def render_with_block(templates, block, data, inners, output):
    data = lookup(data, block.args[0].value.value)
    for child in block.children:
        render_block(templates, child, data, inners, output)

def render_consequent(templates, children, data, inners, output):
    # render up until else tag
    for child in children:
        if type(child) == ElseTag:
            return
        render_block(templates, child, data, inners, output)

def render_alternative(templates, children, data, inners, output):
    # search for else tag, render anything after
    alternative = False
    for child in children:
        if alternative:
            render_block(templates, child, data, inners, output)
        if type(child) == ElseTag:
            alternative = True

def conditional_block_renderer(f):
    def render(templates, block, data, inners, output):
        x = lookup(data, block.args[0].value.value)
        if f(x):
            render_consequent(templates, block.children, data, inners, output)
        else:
            render_alternative(templates, block.children, data, inners, output)
    return render

def render_call_block(templates, block, data, inners, output):
    name = lookup(data, block.args[0].value.value)
    if len(block.args) > 1:
        data = lookup(data, block.args[1].value.value)
    inners = inners + [block.children]
    render_template(templates, name, data, inners, output)


builtins = {
    'each': render_each_block,
    'if': conditional_block_renderer(lambda x: x),
    'unless': conditional_block_renderer(lambda x: not x),
    'with': render_with_block,
    'call': render_call_block
}

def render_block(templates, block, data, inners, output):
    t = type(block)
    if t == Text:
        output.write(block.value)
    elif t == EscapedTag:
        output.write(escape(
            to_string(lookup(data, block.value.value)), True))
    elif t == RawTag:
        output.write(to_string(lookup(data, block.value.value)))
    elif t == ExpandTag:
        if len(inners) > 0:
            inner = inners[-1]
            for child in inners[-1]:
                render_block(templates, child, data, inners[:-1], output)
    elif t == BlockTag:
        builtin = builtins.get(block.name)
        if builtin:
            builtin(templates, block, data, inners, output)
        else:
            if len(block.args) > 0:
                data = lookup(data, block.args[0].value.value)
            inners = inners + [block.children]
            render_template(templates, block.name, data, inners, output)

def render_template(templates, name, data, inners, output):
    tmpl = templates.get(name)
    if not tmpl:
        raise MageryError("Unrecognized template tag: {{#%s..." % name)
    for block in tmpl:
        render_block(templates, block, data, inners, output)

def render_to_stream(templates, name, data, output):
    render_template(templates, name, data, [], output)

def render_to_string(templates, name, data):
    output = io.StringIO()
    render_to_stream(templates, name, data, output)
    result = output.getvalue()
    output.close()
    return result
