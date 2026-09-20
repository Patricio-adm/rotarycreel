#!/bin/bash
echo "Sincronizando cambios con GitHub..."
git add .
git commit -m "ACTUALIZACION"
git push origin main
echo "¡Proceso finalizado con éxito!"
