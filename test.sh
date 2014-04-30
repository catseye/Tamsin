#!/bin/sh

FILES="
    README.markdown doc/Tamsin.markdown doc/Case_Study.markdown
"
if [ ! x$1 = x ]; then
   FILES=$1
fi

falderal --substring-error fixture/tamsin.py.markdown $FILES
