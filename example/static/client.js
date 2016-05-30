// The application can be whatever structure you like,
// I've tried to demonstrate with something fairly generic.

function init(source, data) {

    var templates = Magery.loadTemplates(source);
    var container = document.getElementById('container');
    var state = data;

    // add a comment to the page
    function add(id, text) {
        state.comments.push({id: id, text: text});
    }

    // remove a comment from the page
    function remove(id) {
        state.comments = state.comments.filter(function (c) {
            return c.id !== id;
        });
    }

    // patch the page with the latest state
    function update() {
        Magery.patch(templates, 'main', container, state);
    }

    container.dispatch = function (name, event, context, path) {
        switch (name) {
            case 'submitComment':
                event.preventDefault();
                var value = state.input;
                if (value) {
                    request.post(
                        {uri: '/create', form: {text: value}, json: true},
                        function (err, res, body) {
                            add(body.id, value);
                            state.input = '';
                            update();
                        });
                }
                break;
            case 'updateInput':
                state.input = event.target.value;
                update();
                break;
            case 'removeComment':
                event.preventDefault();
                request.post(
                    {uri: '/remove/' + context.id, json: true},
                    function (err, res, body) {
                        remove(context.id);
                        update();
                    });
                break;
            default:
                console.warn('Unhandled event: ' + name);
        }
    };

    // patch using initial data
    update();
}


// fetch templates
request.get('/static/template.html', function (err, res, template) {
    // get JSON data for the page
    request.get({uri: '/', json: true}, function (err, res, data) {
        // initialize application
        init(template, data);
    });
});
