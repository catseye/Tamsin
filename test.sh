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
    falderal --substring-error fixture/compiler.py.markdown doc/Tamsin.markdown
else
    falderal --substring-error fixture/tamsin.py.markdown $FILES
fi
