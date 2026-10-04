web: cd backend && gunicorn -k uvicorn.workers.UvicornWorker -w 2 --timeout 120 --graceful-timeout 30 -b 0.0.0.0:$PORT app.main:app
