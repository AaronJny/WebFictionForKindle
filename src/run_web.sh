#!/bin/bash
gunicorn -k gevent -c gunicorn_config.py --reload app:app