#!/bin/bash

if [ -z "$1" ]; then
  python test_client.py
elif [ "$1" = "all" ]; then
  shift
  python test_client.py --all "$@"
elif [[ "$1" == --* ]]; then
  python test_client.py "$@"
else
  TEST_ID=$1
  shift
  python test_client.py --test "$TEST_ID" "$@"
fi
