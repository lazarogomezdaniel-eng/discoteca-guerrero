#!/bin/bash
# Navegar a la carpeta del proyecto
cd "$(dirname "$0")"

echo "================================================"
echo "   🕺 INICIANDO LABORATORIO TECKTONIK 3D"
echo "================================================"

# Comprobar y limpiar procesos previos en el puerto 8080
OLD_PID=$(lsof -ti :8080)
if [ -n "$OLD_PID" ]; then
    echo "Liberando puerto 8080 (PID: $OLD_PID)..."
    kill -9 $OLD_PID 2>/dev/null
    sleep 1
fi

echo "Iniciando servidor web local..."
node server.js &
sleep 1

echo "Abriendo el Laboratorio Tecktonik en tu navegador..."
open "http://localhost:8080/laboratorio_baile.html"

echo "¡Listo! Puedes minimizar esta ventana."
