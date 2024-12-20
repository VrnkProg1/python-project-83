#!/usr/bin/env bash

# Установка зависимостей
make install && psql -a -d $DATABASE_URL -f database.sql
