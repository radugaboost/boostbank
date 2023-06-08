#!/bin/bash
python3.10 manage.py runserver &
celery -A mysite worker -l info &
celery -A mysite beat -l info &