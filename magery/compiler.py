import re
import collections
import html5lib
from . import runtime
from .TemplateSet import TemplateSet
from .AST import Collection, Template, Raw, Variable, If, Each, Unless, \
    TemplateCall, TemplateChildren, EmbeddedData

import sys
if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO


def is_element(node):
    return node.nodeType == 1


def is_text(node):
    return node.nodeType == 3


def is_document(node):
    return node.nodeType == 9


def is_template_node(node):
    return is_element(node) and template_name(node)


def template_name(node):
    return node.getAttribute('data-template')


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
    "data-each",
    "data-if",
    "data-unless",
)

BOOLEAN_ATTRIBUTES = (
    "allowfullscreen", "async", "autofocus",
    "autoplay", "capture", "checked", "controls", "default", "defer",
    "disabled", "formnovalidate", "hidden", "itemscope", "loop",
    "multiple", "muted", "novalidate", "open", "readonly", "required",
    "reversed", "selected",
)

HTML_TAGS = [
    "a", "abbr", "acronym", "address", "applet", "area",
    "article", "aside", "audio", "b", "base", "basefont", "bdi",
    "bdo", "bgsound", "big", "blink", "blockquote", "body", "br",
    "button", "canvas", "caption", "center", "cite", "code", "col",
    "colgroup", "command", "content", "data", "datalist", "dd", "del",
    "details", "dfn", "dialog", "dir", "div", "dl", "dt", "element",
    "em", "embed", "fieldset", "figcaption", "figure", "font",
    "footer", "form", "frame", "frameset", "h1", "h2", "h3", "h4",
    "h5", "h6", "head", "header", "hgroup", "hr", "html", "i",
    "iframe", "image", "img", "input", "ins", "isindex", "kbd",
    "keygen", "label", "legend", "li", "link", "listing", "main",
    "map", "mark", "marquee", "menu", "menuitem", "meta", "meter",
    "multicol", "nav", "nobr", "noembed", "noframes", "noscript",
    "object", "ol", "optgroup", "option", "output", "p", "param",
    "picture", "plaintext", "pre", "progress", "q", "rp", "rt", "rtc",
    "ruby", "s", "samp", "script", "section", "select", "shadow",
    "slot", "small", "source", "spacer", "span", "strike", "strong",
    "style", "sub", "summary", "sup", "table", "tbody", "td",
    "template", "textarea", "tfoot", "th", "thead", "time", "title",
    "tr", "track", "tt", "u", "ul", "var", "video", "wbr", "xmp"
]

SELF_CLOSING_TAGS = [
    "area", "base", "br", "col", "embed", "hr",
    "img", "input", "keygen", "link", "menuitem", "meta", "param",
    "source", "track", "wbr",
]


def compile_element(node, queue, result, is_root):
    if not is_root and is_template_node(node):
        result.append(TemplateCall(template_name(node), None))
        queue.append(node)
        return

    tag = node.tagName.lower()

    if tag == 'template-children':
        result.append(TemplateChildren())

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

    if node.tagName not in HTML_TAGS:
        context = {}
        for name, value in node.attributes.items():
            if name not in SKIPPED_ATTRIBUTES:
                context[name] = []
                compile_variables(value, context[name])
        block = TemplateCall(node.tagName.lower(), context)
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
            result.append(Raw(' data-context="'))
            result.append(EmbeddedData())
            result.append(Raw('"'))
        else:
            if name == 'data-template':
                name = 'data-bind'
            result.append(Raw(' %s="' % runtime.html_escape(name)))
            compile_variables(value, result)
            result.append(Raw('"'))
    result.append(Raw(">"))

    for child in node.childNodes:
        compile_node(child, queue, result, False)

    if tag not in SELF_CLOSING_TAGS:
        result.append(Raw("</%s>" % tag))


def compile_text(node, result):
    compile_variables(node.nodeValue, result)


def compile_node(node, queue, result, is_root):
    if is_element(node):
        compile_element(node, queue, result, is_root)
    elif is_text(node):
        compile_text(node, result)
    elif is_document(node):
        for child in node.childNodes:
            compile_node(child, queue, result, is_root)
    else:
        raise Exception("Unknown nodeType: %s" % node.nodeType)


def compile_tree(tree, output):
    queue = collections.deque()
    ignored = Collection()
    result = Collection()
    compile_node(tree, queue, ignored, False)
    while len(queue) > 0:
        node = queue.popleft()
        template = Template(template_name(node))
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
