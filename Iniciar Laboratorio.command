#!/bin/bash
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
cd "$(dirname "$0")"

clear
echo "=================================================="
echo "   🕺 LABORATORIO PROCEDURAL TECKTONIK 3D"
echo "=================================================="

# Limpiar procesos previos en el puerto 8080 si existen
OLD_PID=$(lsof -ti :8080 2>/dev/null)
if [ -n "$OLD_PID" ]; then
    echo "Reiniciando servidor anterior en puerto 8080 (PID: $OLD_PID)..."
    kill -9 $OLD_PID 2>/dev/null
    sleep 1
fi

echo "Iniciando servidor Node.js..."
node server.js &
SERVER_PID=$!
sleep 1

# Comprobar que sigue vivo
if kill -0 $SERVER_PID 2>/dev/null; then
    echo "✅ Servidor activo correctamente (PID: $SERVER_PID)"
else
    echo "❌ Error al iniciar server.js. Asegúrate de tener Node.js instalado."
    exit 1
fi

echo ""
echo "Abriendo el Laboratorio Tecktonik en tu navegador..."
open "http://localhost:8080/laboratorio_baile.html"

echo ""
echo "=================================================="
echo "   Páginas disponibles:"
echo "   1. Lab Tecktonik:      http://localhost:8080/laboratorio_baile.html"
echo "   2. Modo Baile Electro: http://localhost:8080/baile.html"
echo "   3. Estudio Principal:  http://localhost:8080/index.html"
echo "=================================================="
echo "💡 Mantén esta ventana abierta mientras utilices el laboratorio."
echo "Para cerrar el servidor, simplemente cierra esta ventana."
echo ""

wait $SERVER_PID
