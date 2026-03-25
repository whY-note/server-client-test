#!/bin/bash

if [ -z "$1" ]; then
  python test_server.py
else
  TEST_ID=$1
  python test_server.py --test $TEST_ID
fi