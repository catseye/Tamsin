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
    #FILES="doc/Tamsin.markdown README.markdown"
    #FILES="doc/Tamsin.markdown doc/Case_Study.markdown README.markdown"
    falderal --substring-error fixture/compiler.py.markdown $FILES
elif [ x$1 = xscanner ]; then
    for EG in eg/*.tamsin; do
        bin/tamsin scan <$EG > 1.txt
        bin/tamsin eg/tamsin-scanner.tamsin <$EG > 2.txt
        diff -ru 1.txt 2.txt || exit 1
    done
elif [ x$1 = xparser ]; then
    for EG in eg/*.tamsin; do
        #bin/tamsin scan <$EG > 1.txt
        echo $EG
        bin/tamsin eg/tamsin-parser.tamsin <$EG || exit 1
        #diff -ru 1.txt 2.txt || exit 1
    done
else
    falderal --substring-error fixture/tamsin.py.markdown $FILES
fi
