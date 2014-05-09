#!/bin/sh

FILES="
    doc/Tamsin.markdown
    doc/Tested_Examples.markdown
"
if [ x$1 = x ]; then
   $0 interpreter &&
   $0 compiler &&
   $0 parser &&
   $0 desugarer &&
   $0 analyzer &&
   $0 micro &&
   echo "All tests passed!"
   exit $?
fi

if [ x$1 = xtamsin ]; then
   echo "Testing things written in Tamsin only."
   $0 parser &&
   $0 desugarer &&
   $0 analyzer &&
   $0 micro &&
   echo "All tests passed!"
   exit $?
fi

if [ x$1 = xthorough ]; then
   echo "Testing EVERYTHING.  Will likely take more than 5 minutes."
   $0 interpreter &&
   $0 compiler &&
   $0 grammar &&
   $0 scanner &&
   $0 interpretedparser &&
   $0 parser &&
   $0 desugarer &&
   $0 analyzer &&
   $0 micro &&
   echo "All tests passed!"
   exit $?
fi

if [ x$2 != x -a -e $2 ]; then
    echo "(Testing on file $2 only)"
    FILES=$2
fi

test_compiled() {
    SRC=$1
    LIBS=$2
    CMD=$3
    BIN=$4

    echo "*** Compiling $SRC (with $LIBS)"
    echo "*** and testing it against '$CMD'..."
    ./build.sh
    bin/tamsin compile $LIBS $SRC > foo.c && \
       gcc -g -Ic_src -Lc_src foo.c -o $BIN -ltamsin || exit 1
    for EG in eg/*.tamsin; do
        echo $EG
        $CMD $EG > 1.txt
        ./$BIN <$EG > 2.txt || exit 1
        diff -ru 1.txt 2.txt > ast.diff
        diff -ru 1.txt 2.txt || exit 1
    done
    echo "Passed."
    exit 0
}

test_interpreted() {
    SRC=$1
    LIBS=$2
    CMD=$3

    echo "*** Interpreting $SRC (with $LIBS)"
    echo "*** and testing it against '$CMD'..."
    for EG in eg/*.tamsin; do
        echo $EG
        $CMD $EG > 1.txt
        bin/tamsin $LIBS $SRC <$EG > 2.txt || exit 1
        diff -ru 1.txt 2.txt > ast.diff
        diff -ru 1.txt 2.txt || exit 1
    done
    echo "Passed."
    exit 0
}

if [ x$1 = xcompiler ]; then
    echo "*** Testing compiler..."
    ./build.sh || exit 1
    falderal $VERBOSE --substring-error fixture/compiler.py.markdown $FILES
elif [ x$1 = xinterpreter -o x$1 = xi ]; then
    echo "*** Testing Python interpreter..."
    falderal $VERBOSE --substring-error fixture/tamsin.py.markdown $FILES
elif [ x$1 = xgrammar ]; then
    echo "*** Testing interpreted Tamsin-grammar-in-Tamsin..."
    for EG in eg/*.tamsin; do
        echo $EG
        bin/tamsin lib/tamsin_scanner.tamsin \
                   mains/tamsin-grammar.tamsin <$EG || exit 1
    done
elif [ x$1 = xscanner ]; then
    test_interpreted "mains/scanner.tamsin" \
                     "lib/tamsin_scanner.tamsin" \
                     "./bin/tamsin scan"
elif [ x$1 = xinterpretedparser ]; then
    test_interpreted "mains/parser.tamsin" \
                     "lib/tamsin_scanner.tamsin lib/tamsin_parser.tamsin" \
                     "./bin/tamsin parse"
elif [ x$1 = xparser ]; then
    test_compiled "mains/parser.tamsin" \
                  "lib/tamsin_scanner.tamsin lib/tamsin_parser.tamsin" \
                  "./bin/tamsin parse" \
                  "tamsin-parser"
elif [ x$1 = xdesugarer ]; then
    test_compiled "mains/desugarer.tamsin" \
                  "lib/tamsin_scanner.tamsin lib/tamsin_parser.tamsin lib/tamsin_analyzer.tamsin" \
                  "./bin/tamsin desugar" \
                  "tamsin-desugarer"
elif [ x$1 = xanalyzer ]; then
    test_compiled "mains/analyzer.tamsin" \
                  "lib/tamsin_scanner.tamsin lib/tamsin_parser.tamsin lib/tamsin_analyzer.tamsin" \
                  "./bin/tamsin analyze" \
                  "tamsin-analyzer"
elif [ x$1 = xmicro ]; then
    echo "*** Compiling Micro-Tamsin interpreter..."
    ./build.sh
    bin/tamsin compile lib/tamsin_scanner.tamsin \
                       lib/tamsin_parser.tamsin \
                       mains/micro-tamsin.tamsin > foo.c && \
       gcc -g -ansi -Werror \
           -Ic_src -Lc_src foo.c -o micro-tamsin -ltamsin || exit 1
    echo "*** Testing Micro-Tamsin interpreter..."
    FILES="doc/Micro-Tamsin.markdown"
    falderal $VERBOSE --substring-error fixture/micro-tamsin.markdown $FILES
else
    echo "Unknown test '$1'."
    exit 1
fi
