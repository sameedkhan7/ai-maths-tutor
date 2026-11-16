const fs = require('fs');
const vm = require('vm');

console.log("Starting comprehensive Frontend Interaction Simulation...");

function makeElement(id, tagName = 'div') {
    const listeners = {};
    const el = {
        id,
        tagName: tagName.toUpperCase(),
        style: {
            setProperty: () => {},
            removeProperty: () => {},
            display: 'block'
        },
        classList: {
            classes: new Set(),
            add: function(...cls) { cls.forEach(c => this.classes.add(c)); },
            remove: function(...cls) { cls.forEach(c => this.classes.delete(c)); },
            toggle: function(c) { if (this.classes.has(c)) this.classes.delete(c); else this.classes.add(c); },
            contains: function(c) { return this.classes.has(c); }
        },
        listeners,
        addEventListener: function(event, handler) {
            if (!listeners[event]) listeners[event] = [];
            listeners[event].push(handler);
        },
        click: function() {
            if (listeners['click']) {
                listeners['click'].forEach(h => h({ preventDefault: () => {}, stopPropagation: () => {}, target: el, currentTarget: el }));
            }
        },
        dispatchEvent: function(event) {
            if (listeners[event.type]) {
                listeners[event.type].forEach(h => h(event));
            }
        },
        querySelectorAll: () => [makeElement('sub-item', 'div')],
        querySelector: () => makeElement('sub-item', 'div'),
        appendChild: () => {},
        removeChild: () => {},
        setAttribute: () => {},
        getAttribute: () => '',
        removeAttribute: () => {},
        focus: () => {},
        blur: () => {},
        innerText: '',
        innerHTML: '',
        value: '',
        dataset: {}
    };
    return el;
}

const elementsById = {};
function getOrCreateElement(id) {
    if (!elementsById[id]) {
        elementsById[id] = makeElement(id);
    }
    return elementsById[id];
}

const domMock = {
    document: {
        getElementById: (id) => getOrCreateElement(id),
        querySelector: (sel) => makeElement(sel.replace(/[^a-zA-Z0-9_-]/g, '_')),
        querySelectorAll: () => [makeElement('el1'), makeElement('el2')],
        addEventListener: (event, handler) => {
            if (event === 'DOMContentLoaded') {
                setTimeout(handler, 10);
            }
        },
        readyState: 'complete',
        createElement: (tag) => makeElement(tag, tag),
        body: makeElement('body', 'body'),
        documentElement: makeElement('documentElement', 'html')
    },
    window: {
        location: { href: 'http://localhost:5500/maths.html', protocol: 'http:', search: '' },
        history: { replaceState: () => {} },
        addEventListener: () => {},
        localStorage: {
            _data: {},
            getItem: function(k) { return this._data[k] || null; },
            setItem: function(k, v) { this._data[k] = String(v); },
            removeItem: function(k) { delete this._data[k]; }
        }
    },
    localStorage: {
        _data: {},
        getItem: function(k) { return this._data[k] || null; },
        setItem: function(k, v) { this._data[k] = String(v); },
        removeItem: function(k) { delete this._data[k]; }
    },
    URLSearchParams: URLSearchParams,
    console: console,
    setTimeout: (fn, ms) => { fn(); return 1; },
    setInterval: () => 1,
    clearTimeout: () => {},
    clearInterval: () => {},
    fetch: () => Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ success: true, chats: [], response: "Math solution" }),
        text: () => Promise.resolve("OK")
    })
};

domMock.window.document = domMock.document;

try {
    const code = fs.readFileSync('script.js', 'utf8');
    const script = new vm.Script(code);
    const context = vm.createContext(domMock);
    script.runInContext(context);
    console.log(">> script.js evaluated successfully without syntax or immediate execution error.");

    // Test essential button clicks and interactions
    const testIds = [
        'new-chat-btn',
        'dev-admin-btn',
        'model-pill-btn',
        'class-selector',
        'maths-input-submit',
        'settings-btn'
    ];

    let clicked = 0;
    testIds.forEach(id => {
        const el = elementsById[id];
        if (el && el.listeners['click'] && el.listeners['click'].length > 0) {
            try {
                el.click();
                clicked++;
                console.log(`  [CLICK OK] Element #${id} triggered ${el.listeners['click'].length} handler(s) cleanly.`);
            } catch (clickErr) {
                console.error(`  [CLICK FAIL] Element #${id} threw an error:`, clickErr);
            }
        }
    });

    console.log(`>> Finished testing. ${clicked} active UI elements clicked without throwing any runtime error!`);

} catch (err) {
    console.error("FATAL RUNTIME ERROR IN script.js:", err);
    process.exit(1);
}
