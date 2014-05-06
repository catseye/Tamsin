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
   $0 compiledast &&
   $0 compileddesugarer &&
   echo "All tests passed!"
   exit $?
fi

if [ x$2 != x -a -e $2 ]; then
    echo "(Testing on file $2 only)"
    FILES=$2
fi

if [ x$1 = xcompiler ]; then
    echo "Testing compiler..."
    ./build.sh || exit 1
    falderal $VERBOSE --substring-error fixture/compiler.py.markdown $FILES
elif [ x$1 = xscanner ]; then
    echo "Testing scanner in Tamsin..."
    for EG in eg/*.tamsin; do
        echo $EG
        bin/tamsin scan <$EG > 1.txt || exit 1
        bin/tamsin eg/tamsin-scanner.tamsin <$EG > 2.txt || exit 1
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
        #cat 2.txt
    done
elif [ x$1 = xdesugarer ]; then
    echo "Testing desugarer in Tamsin..."
    for EG in eg/*.tamsin; do
        echo $EG
        bin/tamsin desugar $EG > 1.txt
        bin/tamsin eg/tamsin-desugarer.tamsin <$EG > 2.txt || exit 1
        diff -ru 1.txt 2.txt > ast.diff
        diff -ru 1.txt 2.txt || exit 1
    done
elif [ x$1 = xcompileddesugarer ]; then
    echo "Compiling desugarer in Tamsin and testing it..."
    ./build.sh
    bin/tamsin compile eg/tamsin-desugarer.tamsin > foo.c && \
       gcc -g -Ic_src -Lc_src foo.c -o tamsin-desugarer -ltamsin || exit 1
    for EG in eg/*.tamsin; do
        echo $EG
        bin/tamsin desugar $EG > 1.txt
        ./tamsin-desugarer <$EG > 2.txt || exit 1
        diff -ru 1.txt 2.txt > ast.diff
        diff -ru 1.txt 2.txt || exit 1
    done
elif [ x$1 = xmicro ]; then
    echo "Compiling Micro-Tamsin interpreter..."
    ./build.sh
    bin/tamsin compile eg/tamsin-micro-interpreter.tamsin > foo.c && \
       gcc -g -Ic_src -Lc_src foo.c -o micro-tamsin -ltamsin || exit 1
    echo "Testing Micro-Tamsin interpreter..."
    FILES="doc/Micro-Tamsin.markdown"
    falderal $VERBOSE --substring-error fixture/micro-tamsin.markdown $FILES
elif [ x$1 = xinterpreter ]; then
    echo "Testing Python interpreter..."
    falderal $VERBOSE --substring-error fixture/tamsin.py.markdown $FILES
fi
    