#!/usr/bin/env python3

from flask import Flask, request, redirect
import json
import magery


#### Data store #####

# keep data in memory for this demo
data = {
    'comments': [
        {'id': 0, 'text': 'Example one'},
        {'id': 1, 'text': 'Example two'}
    ]
}

# auto-incrementing id counter
next_id = 2


def add_comment(text):
    global next_id
    comment = {'id': next_id, 'text': text}
    data['comments'].append(comment)
    next_id += 1
    return comment


def remove_comment(id):
    data['comments'] = [c for c in data['comments'] if c['id'] != id]


#### Web server ####

# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='/static')

# load template
templates = magery.compile_templates('templates/example.html')
print(templates)

@app.route("/")
def index():
    if request.accept_mimetypes.best == 'application/json':
        return json.dumps(data)
    else:
        return templates['page'].render_to_string(data)

@app.route("/create", methods=['POST'])
def create():
    comment = add_comment(request.form['text'])
    if request.accept_mimetypes.best == 'application/json':
        return json.dumps({'id': comment['id']})
    else:
        return redirect('/')

@app.route("/remove/<path:id>", methods=['POST'])
def remove(id):
    remove_comment(int(id))
    if request.accept_mimetypes.best == 'application/json':
        return json.dumps({'ok': True})
    else:
        return redirect('/')


if __name__ == "__main__":
    app.debug = True
    app.run()
