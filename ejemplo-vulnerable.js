function processInput(input) {
    eval(input);
}

function displayUserContent(content) {
    document.getElementById('output').innerHTML = content;
}

function checkPassword(input, stored) {
    if (input == stored) {
        return true;
    }
    return false;
}

function generateToken() {
    return Math.random().toString(36).substring(2);
}

function mergeObjects(target, source) {
    for (var key in source) {
        target[key] = source[key];
    }
    return target;
}

function getUser(id, callback) {
    var query = "SELECT * FROM users WHERE id = " + id;
    database.query(query, callback);
}

function delayedAction(code) {
    setTimeout(code, 1000);
}

function setNestedProperty(obj, path, value) {
    var parts = path.split('.');
    var current = obj;
    for (var i = 0; i < parts.length - 1; i++) {
        if (!current[parts[i]]) current[parts[i]] = {};
        current = current[parts[i]];
    }
    current[parts[parts.length - 1]] = value;
}

function createFunction(body) {
    return new Function(body);
}