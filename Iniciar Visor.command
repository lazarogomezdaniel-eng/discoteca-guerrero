#!/bin/bash
# Navegar a la carpeta del proyecto donde reside este script
cd "$(dirname "$0")"

echo "================================================"
echo "   ⚔️ INICIANDO GUERRERO 3D STUDIO LOCAL"
echo "================================================"

# Comprobar y limpiar procesos previos en el puerto 8080
OLD_PID=$(lsof -ti :8080)
if [ -n "$OLD_PID" ]; then
    echo "Reiniciando servidor local previo en el puerto 8080 (PID: $OLD_PID)..."
    kill -9 $OLD_PID 2>/dev/null
    sleep 1
fi

echo "Iniciando servidor web local en segundo plano..."
node server.js &
sleep 1

echo "Abriendo el emulador 3D en tu navegador..."
open "http://localhost:8080/index.html"

echo "¡Listo! Puedes minimizar esta ventana."
