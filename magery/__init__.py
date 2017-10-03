import collections
import html5lib
import cgi
import io
from StringIO import StringIO
from .AST import *


def html_escape(value):
    return cgi.escape(value, quote=True)

class TemplateSet(object):
    def __init__(self):
        self._templates = {}

    def add(self, name, render):
        print "TemplateSet.add: %s" % name
        self._templates[name] = render

    def render(self, name, data, output, inner=None):
        self._templates[name](self, data, output, inner)

    def render_to_string(self, name, data):
        output = StringIO()
        self.render(name, data, output)
        return output.getvalue()

        
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


def compile_element(node, queue, result, is_root):
    if not is_root and is_template_node(node):
        queue.append(node)
        return
    
    tag = node.tagName.lower()
    
    result.append(AST.Raw("<%s" % tag))
    for name, value in node.attributes.items():
        if name == 'data-template':
            name = 'data-bind'
        result.append(Raw(' %s="%s"' % (html_escape(name), html_escape(value))))
    result.append(AST.Raw(">"))
    
    for child in node.childNodes:
        compile_node(child, queue, result, False)
        
    result.append(AST.Raw("</%s>" % tag))

    
def compile_text(node, result):
    result.append(AST.Raw(node.nodeValue))

    
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
    ignored = AST.Collection()
    result = AST.Collection()
    compile_node(tree, queue, ignored, False)
    while len(queue) > 0:
        node = queue.popleft()
        template = AST.Template(template_name(node))
        compile_node(node, queue, template, True)
        result.append(template)
    result.collapse()
    print result
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
    print "------------------------"
    print src
    print "------------------------"
    exec src in {'templates': templates}
    return templates
