#!/bin/bash
python init_app.py
gunicorn -k gevent -c gunicorn_config.py --reload app:app