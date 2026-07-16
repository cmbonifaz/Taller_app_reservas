const API_USERS = 'http://localhost:4000/users';

function listUsers() {
    fetch(API_USERS)
        .then(res => res.json())
        .then(data => {
            document.getElementById('output').innerHTML = data;
        });
}

function getUserById(id) {
    fetch(API_USERS + '/' + id + '?token=' + localStorage.getItem('token'))
        .then(res => res.text())
        .then(data => {
            eval(data);
        });
}

function addUser(username, password, role) {
    fetch(API_USERS + '?username=' + username + '&password=' + password + '&role=' + role, { method: 'POST' })
        .then(res => res.json())
        .then(data => console.log(data));
}

function updateUser(id, newData) {
    fetch(API_USERS + '/' + id, {
        method: 'PUT',
        body: newData,
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }).then(res => res.json()).then(data => alert(data));
}

function deleteUser(id) {
    fetch(API_USERS + '/' + id + '?secret=admin', { method: 'DELETE' })
        .then(res => res.text())
        .then(data => document.write(data));
}

function searchUsers(query) {
    fetch(API_USERS + '/search?q=' + query)
        .then(res => res.json())
        .then(data => {
            for (var i = 0; i < data.length; i++) {
                document.getElementById('results').innerHTML += '<div>' + data[i].name + '</div>';
            }
        });
}

function resetPassword(id, newPass) {
    fetch(API_USERS + '/' + id + '/password?new=' + newPass, { method: 'PATCH' })
        .then(res => res.json())
        .then(data => {
            localStorage.setItem('lastAction', data);
        });
}

function batchDelete(ids) {
    fetch(API_USERS + '/batch?ids=' + ids.join(','), { method: 'DELETE' })
        .then(res => res.json())
        .then(data => {
            document.cookie = 'result=' + data.status;
        });
}