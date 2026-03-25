#!/bin/bash

if [ -z "$1" ]; then
  python test_server.py
elif [ "$1" = "all" ]; then
  shift
  python test_server.py --all "$@"
elif [[ "$1" == --* ]]; then
  python test_server.py "$@"
else
  TEST_ID=$1
  shift
  python test_server.py --test "$TEST_ID" "$@"
fi
