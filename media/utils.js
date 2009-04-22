//Cross-browser function to add an event-listener
function addEvent(instance, eventName, listener) {
    var listenerFn = listener;
    if (instance.addEventListener) {
        instance.addEventListener(eventName, listenerFn, false);
    } else if (instance.attachEvent) {
        listenerFn = function() {
            listener(window.event);
        }
        instance.attachEvent("on" + eventName, listenerFn);
    } else {
        throw new Error("Event registration not supported");
    }
    return {
        instance: instance,
        name: eventName,
        listener: listenerFn
    };
}
