#!/bin/bash

uv run manage.py migrate
exec uv run manage.py runserver 0.0.0.0:8000
