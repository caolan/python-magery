import json
import cgi
import sys


def html_escape(value):
    return cgi.escape(value, quote=True)


def lookup(data, path):
    for prop in path:
        if prop == "length" and type(data) == list:
            data = len(data)
        elif type(data) == dict and prop in data:
            data = data[prop]
        else:
            return None
    return data


def to_string(value):
    if value is None:
        return ""
    elif value is True:
        return "true"
    elif value is False:
        return "false"
    elif type(value) == dict:
        return "[object Object]"
    elif type(value) == list:
        return ",".join(map(to_string, value))
    return "%s" % value


def each(data, name, path, fn):
    data = data.copy()
    iterable = lookup(data, path)
    if type(iterable) == list:
        for item in iterable:
            data[name] = item
            fn(data)


def render(templates, name, data, output, inner, embed_data=False):
    if templates.has(name):
        templates.render(name, data, output, inner, embed_data)


def encode_json(data):
    return json.dumps(data, separators=(',', ':'))


def source(templates, name):
    if templates.has(name):
        return templates.get_source(name)
    return ''
