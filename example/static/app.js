var templates = Magery.compile('.magery-templates');
var target = document.querySelector('[data-bind="main"]');
var data = JSON.parse(target.dataset.context);

function render() {
    Magery.patch(templates, 'main', data, target);
}

data.submitDisabled = !data.input;
data.formDisabled = false;

var handlers = {
    // init: function () {
    //     data.submitDisabled = !data.input;
    //     data.formDisabled = false;
    // },
    updateInput: function (event) {
        data.input = event.target.value;
        data.submitDisabled = !data.input;
        render();
    },
    submitComment: function (event) {
        event.preventDefault();
        if (data.submitDisabled) {
            return;
        }
        var self = this;
        var init = {
            method: 'POST',
            headers: {'Accept': 'application/json'},
            body: new FormData(event.target)
        };
        fetch('/create', init).then(function (response) {
            return response.json();
        }).then(function (data) {
            handlers.addComment(data.id, data.text);
        });
        data.formDisabled = true;
        render();
    },
    addComment: function (id, text) {
        data.comments.push({id: id, text: text});
        data.input = '';
        data.submitDisabled = true;
        data.formDisabled = false;
        render();
    },
    submitRemoveComment: function (event, id) {
        event.preventDefault();
        var self = this;
        var url = '/remove/' + encodeURIComponent(id);
        var init = {
            method: 'POST',
            headers: {'Accept': 'application/json'}
        };
        fetch(url, init).then(function (response) {
            return response.json();
        }).then(function (data) {
            if (data.ok) {
                handlers.removeComment(id);
            }
        });
        render();
    },
    removeComment: function (id) {
        data.comments = data.comments.filter(
            function (comment) {
                return comment.id !== id;
            }
        );
        render();
    }
};

templates['main'].bind(handlers);
render();
