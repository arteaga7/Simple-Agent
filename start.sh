#!/usr/bin/env bash

# 1. Arrancar Uvicorn en segundo plano (puerto 8000 interno)
uvicorn main:app --host 0.0.0.0 --port 8000 &

# 2. Esperar un par de segundos a que la API levante
sleep 3

# 3. Arrancar Streamlit en primer plano usando el puerto oficial de Render ($PORT)
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0