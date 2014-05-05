#!/bin/sh

FILES="
    doc/Tamsin.markdown
    doc/Tested_Examples.markdown
"
if [ x$1 = x ]; then
   $0 interpreter &&
   $0 compiler &&
   $0 scanner &&
   $0 parser &&
   $0 ast &&
   echo "All tests passed!"
   exit $?
fi

if [ x$1 = xcompiler ]; then
    echo "Testing compiler..."
    ./build.sh || exit 1
    falderal $VERBOSE --substring-error fixture/compiler.py.markdown $FILES
elif [ x$1 = xscanner ]; then
    echo "Testing scanner in Tamsin..."
    for EG in eg/*.tamsin; do
        echo $EG
        bin/tamsin scan <$EG > 1.txt
        bin/tamsin eg/tamsin-scanner.tamsin <$EG > 2.txt
        diff -ru 1.txt 2.txt || exit 1
    done
elif [ x$1 = xparser ]; then   # just check that tamsin-parser accepts it
    echo "Testing parser (for syntax) in Tamsin..."
    for EG in eg/*.tamsin; do
        echo $EG
        bin/tamsin eg/tamsin-parser.tamsin <$EG || exit 1
    done
elif [ x$1 = xast ]; then   # check that tamsin-ast output looks like bin/tamsin parse
    echo "Testing parser (for AST) in Tamsin..."
    for EG in eg/*.tamsin; do
        echo $EG
        bin/tamsin parse $EG > 1.txt
        bin/tamsin eg/tamsin-ast.tamsin <$EG > 2.txt || exit 1
        diff -ru 1.txt 2.txt > ast.diff
        diff -ru 1.txt 2.txt || exit 1
    done
elif [ x$1 = xcompiledast ]; then   # check that tamsin-ast output looks like bin/tamsin parse
    echo "Compiling parser (for AST) in Tamsin and testing it..."
    ./build.sh
    bin/tamsin compile eg/tamsin-ast.tamsin > foo.c && \
       gcc -g -Ic_src -Lc_src foo.c -o tamsin-ast -ltamsin || exit 1
    for EG in eg/*.tamsin; do
        echo $EG
        bin/tamsin parse $EG > 1.txt
        ./tamsin-ast <$EG > 2.txt || exit 1
        diff -ru 1.txt 2.txt > ast.diff
        diff -ru 1.txt 2.txt || exit 1
    done
elif [ x$1 = xinterpreter ]; then
    echo "Testing Python interpreter..."
    falderal $VERBOSE --substring-error fixture/tamsin.py.markdown $FILES
elif [ -e $1 ]; then
    echo "Testing file with interpreter..."
    falderal $VERBOSE --substring-error fixture/tamsin.py.markdown $1
fi
