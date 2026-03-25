#!/bin/bash

if [ -z "$1" ]; then
  python test_client.py 
else
  TEST_ID=$1
  python test_client.py --test $TEST_ID
fi