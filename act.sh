#!/bin/bash
    # Detiene el script inmediatamente si un comando falla
    set -e

    # Asegura que el script tenga acceso a las carpetas donde vive git
    export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"

    echo "Sincronizando cambios con GitHub..."
    git add .
    git commit -m "ACTUALIZACION"
    git push origin main

    echo "¡Proceso finalizado con éxito!"

