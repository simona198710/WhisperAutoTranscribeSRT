#!/bin/bash

. ${PYENV_ROOT}/versions/whisper/bin/activate

for (( c=1; c<=25; c++ ))
do
  python run.py
done
