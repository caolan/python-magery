document.body.onload = function () {
    var templates = Magery.compileTemplates();
    
    templates['main'].bindAll({
        updateInput: function (event) {
            this.data.input = event.target.value;
        },
        submitComment: function (event) {
            event.preventDefault();
            var self = this;
            var init = {
                method: 'POST',
                headers: {'Accept': 'application/json'},
                body: new FormData(event.target)
            };
            fetch('/create', init).then(function (response) {
                return response.json();
            }).then(function (data) {
                self.trigger('addComment', data.id, data.text);
            });
            this.data.formDisabled = true;
        },
        addComment: function (id, text) {
            this.data.comments.push({id: id, text: text});
            this.data.input = '';
            this.data.formDisabled = false;
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
                    self.trigger('removeComment', id);
                }
            });
        },
        removeComment: function (id) {
            this.data.comments = this.data.comments.filter(
                function (comment) {
                    return comment.id !== id;
                }
            );
        }
    });
};
