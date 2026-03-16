require("dotenv").config();
const express = require("express");
const axios = require("axios");
const cors = require("cors");

const app = express();
app.use(cors());
app.use(express.json());

const PORT = 3000;

app.get("/api/mapa", async (req, res) => {
  const direccion = req.query.direccion;

  if (!direccion) {
    return res.status(400).json({ error: "Debe enviar una dirección" });
  }

  try {
    const response = await axios.get(
      "https://maps.googleapis.com/maps/api/geocode/json",
      {
        params: {
          address: direccion,
          key: process.env.GOOGLE_MAPS_API_KEY,
        },
        timeout: 5000,
      }
    );

    res.json(response.data);

  } catch (error) {
    res.status(500).json({ error: "Error al consultar la API" });
  }
});

app.listen(PORT, () => {
  console.log(`Servidor corriendo en http://localhost:${PORT}`);
});