const mongoose = require('mongoose');

const bookingSchema = new mongoose.Schema({
    userId: { type: String, required: true },
    fecha: { type: Date, required: true },
    servicio: { type: String, required: true },
    canceladaEn: {
        type: Date,
        default: null
    },
    estado: {
        type: String,
        enum: ['activo', 'cancelada'],
        default: 'activo'
    }
}, { timestamps: true });

module.exports = mongoose.model('Booking', bookingSchema);
