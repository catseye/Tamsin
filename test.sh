#!/bin/sh

FILES="
    README.markdown
    doc/Tamsin.markdown
    doc/Advanced_Features.markdown
    doc/Case_Study.markdown
"
if [ ! x$1 = x ]; then
   FILES=$1
fi

if [ x$1 = xcompiler ]; then
    ./build.sh
    FILES="doc/Tamsin.markdown"
    FILES="doc/Tamsin.markdown README.markdown"
    #FILES="doc/Tamsin.markdown doc/Case_Study.markdown README.markdown"
    falderal --substring-error fixture/compiler.py.markdown $FILES
else
    falderal --substring-error fixture/tamsin.py.markdown $FILES
fi
