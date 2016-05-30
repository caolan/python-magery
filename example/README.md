# Python Magery Example

This demo is a small [Flask][flask] server that keeps a list of comments in
memory. The comments are rendered using the [Magery][magery] template
`static/template.html`, and can be updated via a form.

On the client-side, JavaScript event handlers are added in
`static/client.js` and used to make updates via AJAX instead. The page is
then dynamically updated using the same template as the server.

The application works with or without JavaScript.

To run the example `server.py`, you'll need to install [Flask][flask]:

    pip install Flask


[flask]: http://flask.pocoo.org/
[magery]: https://github.com/caolan/magery/
