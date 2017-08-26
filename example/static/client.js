var templates = Magery.compileTemplates();

// when a template renders another template, that also needs to be bound?
// NOTE: only embedded templates will be able to call bindAll()
templates['page'].bindAll({
    // what if each elemnent has it's own this.data but all events are
    // 'global' and can be bound by any template/widget? adding
    // foo.bar style namespacing support might make this easier to
    // handle - e.g. page: {removeComment: ...}, global: {foo: ...}
    page: {
        removeComment: function (id) {
            this.data.comments = this.data.comments.filter(function (comment) {
                return comment.id !== id;
            });
        },
        submitComment: function (txt) {
            this.data.comments.push({id: Math.random(), text: txt});
        },
        updateInput: function (event) {
            this.data.input = event.target.value;
        }
    },
    
    // BUT what to do about things like widget.clearInput() which
    // might clear all widgets, do we need to differentiate between
    // global and local events afterall?
    global: {
    },
    clearInput: function () {
    }

    // see: https://www.npmjs.com/package/@polymer/iron-signals
    // To receive a signal, listen for iron-signal-<name> event on a iron-signals element.
    
    // and: https://www.polymer-project.org/1.0/docs/devguide/events
    // can event bubbling help with shared events?

    // DON'T NEED TO SOLVE THESE RIGHT NOW
    
});
