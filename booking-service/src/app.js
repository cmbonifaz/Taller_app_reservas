require('dotenv').config();
const express = require('express');
const cors = require('cors');
const mongoose = require('mongoose');
const bookingRoutes = require('./routes/booking.routes');

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

app.use('/', bookingRoutes)

mongoose
    .connect(process.env.MONGO_URI)
    .then(() => {
        console.log('🚀 Conectado a MongoDB (Booking Service)');
        app.listen(PORT, () => console.log(`✅ Booking service corriendo en puerto ${PORT}`));
    })
    .catch(err => console.error('❌ Error al conectar a MongoDB:', err));
