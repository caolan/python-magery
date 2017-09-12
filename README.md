# Python Magery

A server-side implementation of the [Magery][magery] templating library for
Python 2 and 3. See the Magery [README][magery] for template syntax.

In the [example](example) directory is a [Flask][flask] app demonstrating
server and client code sharing templates.

## Installation

```no-highlight
pip install magery
```

## API

```python
import magery
```

### compile_templates(filename, templates=None)

Parses templates from `filename`, returns a dictionary of templates.
If `templates` is not `None` it will extend the existing templates
dictionary instead of returning a new one.

```python
templates = magery.compile_templates('./template.html')
```

### Template.render\_to\_string(data)

Render a compiled template using `data`, and return the output as a
string.

```python
templates = magery.compile_templates('./template.html')

data = {'name': 'world'}
templates['app'].render_to_string(data);
```

### Template.write(data, out)

Render a compile template using `data`, and write the result to the IO
stream `out`.

```python
templates = magery.compile_templates('./template.html')

with open('output.html', 'w', encoding='utf-8') as f:
    data = {'name': 'world'}
    templates['app'].write(data, f);
```

[magery]: https://github.com/caolan/magery/
[flask]: http://flask.pocoo.org/
