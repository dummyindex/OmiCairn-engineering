const listenedEventsMap = new Map();
listenedEventsMap.set('resize', true);

class WindowListener {
    private eventMap: Map<string, Map<string, Function>>;
    constructor() {
        this.eventMap = new Map();
        for (const [eventName, _] of listenedEventsMap) {
            this.eventMap.set(eventName, new Map());
            window.addEventListener(eventName, (e) => {
                const eventMap = this.eventMap.get(eventName);
                if (eventMap) {
                    for (const [key, callback] of eventMap) {
                        callback(e);
                    }
                }
            });
        }
    }

    register(eventName: string, key: string, callback: Function) {
        const eventMap = this.eventMap.get(eventName);
        if (eventMap) {
            eventMap.set(key, callback);
        }
    }

    unregister(eventName: string, key: string) {
        const eventMap = this.eventMap.get(eventName);
        if (eventMap) {
            eventMap.delete(key);
        }
    }

}

const windowListener = new WindowListener();
export default windowListener;