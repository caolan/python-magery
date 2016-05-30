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

### load(source)

Parses templates from the string `source`, returns a dictionary of
templates (each an individual #define block).

```python
templates = magery.load('{{#define app}} Hello, {{name}}! {{/define}}')
```

### loadFile(filename)

Read file as utf-8 and return parsed templates.

```python
templates = magery.loadFile('./template.html')
```

### render\_to\_string(templates, name, data)

Render the named template in the `templates` dictionary using `data` and
return the output as a string.

```python
html = magery.render_to_string(templates, 'app', {'name': 'world'})
```

### render\_to\_stream(templates, name, data, output):

Render the named template in the `templates` dictionary using `data` and
write the result to the `output` IO stream.

```python
outfile = open('output.html', 'w', encoding='utf-8')
magery.render_to_stream(templates, 'app', {'name': 'world'}, outfile)
outfile.close()
```

[magery]: https://github.com/caolan/magery/
[flask]: http://flask.pocoo.org/
