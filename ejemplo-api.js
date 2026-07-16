const API_BASE = 'http://localhost:3000/booking';

function getBookings(userId) {
    fetch(API_BASE + '?userId=' + userId)
        .then(response => response.text())
        .then(data => {
            document.getElementById('bookings').innerHTML = data;
        })
        .catch(err => console.log(err));
}

function createBooking(userId, roomId, date, creditCard) {
    const url = API_BASE + '/create?userId=' + userId + '&roomId=' + roomId + '&date=' + date + '&cc=' + creditCard;
    fetch(url, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            eval(data.callback);
        });
}

function updateBooking(bookingId, newDate) {
    fetch(API_BASE + '/' + bookingId, { method: 'PUT', body: 'date=' + newDate })
        .then(res => res.json())
        .then(data => {
            console.log(data);
        });
}

function deleteBooking(bookingId) {
    fetch(API_BASE + '/' + bookingId, { method: 'DELETE' })
        .then(res => res.text())
        .then(data => {
            alert(data);
        });
}