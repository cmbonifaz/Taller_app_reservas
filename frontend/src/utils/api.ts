const AUTH_URL = process.env.NEXT_PUBLIC_API_URL;
const USER_URL = process.env.NEXT_PUBLIC_USER_URL;
const BOOKING_URL = process.env.NEXT_PUBLIC_BOOKING_URL;

export const registerUser = async (data: { name: string; email: string; password: string }) => {
    const res = await fetch(`${AUTH_URL}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });

    return res.json();
};

export const loginUser = async (data: { email: string; password: string }) => {
    const res = await fetch(`${AUTH_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });

    return res.json();
};

export const getMe = async (token: string) => {
    const res = await fetch(`${USER_URL}/me`, {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });

    return res.json();
};

export const getBookings = async (token: string) => {
    const res = await fetch(`${BOOKING_URL}/bookings`, {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });

    return res.json();
};

