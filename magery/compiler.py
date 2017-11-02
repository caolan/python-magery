import re
import collections
import html5lib
from xml.dom import minidom
from . import runtime
from .TemplateSet import TemplateSet
from .AST import Collection, Template, Raw, Variable, If, Each, Unless, \
    TemplateCall, TemplateChildren, EmbeddedData, TemplateEmbed, ConditionalDataEmbed

import sys
if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO


ELEMENT_NODE = 1
TEXT_NODE = 3
COMMENT_NODE = 8
DOCUMENT_NODE = 9
DOCUMENT_TYPE_NODE = 10

impl = minidom.getDOMImplementation()
document = impl.createDocument(None, "some_tag", None)


def write_node(node, out):
    walker = html5lib.getTreeWalker("dom")
    stream = walker(node)
    s = html5lib.serializer.HTMLSerializer(
        quote_attr_values='always',
        minimize_boolean_attributes=False,
        use_best_quote_char=True,
        omit_optional_tags=False
    )
    for txt in s.serialize(stream):
        out.write(txt)


def outer_html(node):
    result = StringIO()
    write_node(node, result)
    return result.getvalue()


def compile_variables(value, result):
    parts = re.split(r"(\{\{|\}\})", value)
    text = True
    for part in parts:
        if part:
            if text:
                if part == "{{":
                    text = False
                else:
                    result.append(Raw(runtime.html_escape(part)))
            else:
                if part == "}}":
                    text = True
                else:
                    result.append(Variable(part.strip().split(".")))


SKIPPED_ATTRIBUTES = (
    "data-tagname",
    "data-each",
    "data-if",
    "data-unless",
    "data-key"
)

BOOLEAN_ATTRIBUTES = (
    "allowfullscreen", "async", "autofocus",
    "autoplay", "capture", "checked", "controls", "default", "defer",
    "disabled", "formnovalidate", "hidden", "itemscope", "loop",
    "multiple", "muted", "novalidate", "open", "readonly", "required",
    "reversed", "selected",
)

SELF_CLOSING_TAGS = [
    "area", "base", "br", "col", "embed", "hr",
    "img", "input", "keygen", "link", "menuitem", "meta", "param",
    "source", "track", "wbr",
]


def compile_element(node, queue, result, is_root):
    is_component = False
    tag = node.tagName.lower()

    if tag == 'template':
        if not is_root:
            queue.append(node)
            return
        is_component = True
        tag = node.getAttribute('data-tagname').lower()

    if tag == 'template-children':
        result.append(TemplateChildren())
        return
    elif tag == 'template-embed':
        result.append(TemplateEmbed(node.getAttribute('template')))
        return

    if node.getAttribute('data-each'):
        value = node.getAttribute('data-each')
        parts = value.split(" in ")
        name = parts[0].strip()
        path = parts[1].strip().split(".")
        block = Each(name, path)
        result.append(block)
        result = block

    if node.getAttribute('data-if'):
        value = node.getAttribute('data-if')
        path = value.strip().split(".")
        block = If(path)
        result.append(block)
        result = block

    if node.getAttribute('data-unless'):
        value = node.getAttribute('data-unless')
        path = value.strip().split(".")
        block = Unless(path)
        result.append(block)
        result = block

    if '-' in node.tagName:
        context = {}
        for name, value in node.attributes.items():
            if name in SKIPPED_ATTRIBUTES \
               or name.startswith('on') \
               or name == 'data-embed':
                continue
            context[name] = []
            compile_variables(value, context[name])
        tmpl_name = [Raw(node.tagName.lower())]
        if tag == 'template-call':
            tmpl_raw = node.getAttribute('template')
            tmpl_name = []
            compile_variables(tmpl_raw, tmpl_name)
        embed_data = node.getAttribute('data-embed') == 'true'
        block = TemplateCall(tmpl_name, context, embed_data)
        result.append(block)
        for child in node.childNodes:
            compile_node(child, queue, block, False)
        return

    result.append(Raw("<%s" % tag))
    for name, value in node.attributes.items():
        if name in SKIPPED_ATTRIBUTES or name.startswith('on'):
            continue
        elif name in BOOLEAN_ATTRIBUTES:
            if value.startswith('{{') and value.endswith('}}'):
                raw_path = value[2:-2].strip()
                if raw_path:
                    path = raw_path.split(".")
                    block = If(path)
                    block.append(Raw(' %s' % runtime.html_escape(name)))
                    result.append(block)
                    continue
            # if it's an interpolated string or empty, boolean
            # property is always True
            result.append(Raw(' %s' % runtime.html_escape(name)))
        elif name == 'data-embed':
            if value == 'true':
                result.append(Raw(' data-context="'))
                result.append(EmbeddedData())
                result.append(Raw('"'))
        else:
            if name == 'data-template':
                name = 'data-bind'
            result.append(Raw(' %s="' % runtime.html_escape(name)))
            compile_variables(value, result)
            result.append(Raw('"'))
    if is_component and node.getAttribute('data-embed') != 'true':
        result.append(ConditionalDataEmbed())
    result.append(Raw(">"))

    for child in node.childNodes:
        compile_node(child, queue, result, False)

    if tag not in SELF_CLOSING_TAGS:
        result.append(Raw("</%s>" % tag))


def compile_text(node, result):
    compile_variables(node.nodeValue, result)


def compile_node(node, queue, result, is_root):
    if node.nodeType == ELEMENT_NODE:
        compile_element(node, queue, result, is_root)
    elif node.nodeType == TEXT_NODE:
        compile_text(node, result)
    elif node.nodeType == DOCUMENT_NODE:
        for child in node.childNodes:
            compile_node(child, queue, result, is_root)
    elif node.nodeType in (DOCUMENT_TYPE_NODE, COMMENT_NODE):
        return
    else:
        raise Exception("Unknown nodeType: %s" % node.nodeType)


def compile_tree(tree, output):
    queue = collections.deque()
    ignored = Collection()
    result = Collection()
    compile_node(tree, queue, ignored, False)
    while len(queue) > 0:
        node = queue.popleft()
        template = Template(
            node.getAttribute('data-tagname'),
            outer_html(node)
        )
        compile_node(node, queue, template, True)
        result.append(template)
    result.collapse()
    result.to_python(output)


def compile_file(filename, output):
    with open(filename, 'rb') as f:
        tree = html5lib.parse(f, treebuilder='dom')
    compile_tree(tree, output)


def compile_to_string(filename):
    result = StringIO()
    compile_file(filename, result)
    return result.getvalue()


def compile_templates(filename, templates=None):
    templates = templates or TemplateSet()
    src = compile_to_string(filename)
    exec(src, {'templates': templates, 'runtime': runtime})
    return templates
