#!/bin/sh

bin/tamsin compile $1 > foo.c && \
   gcc -Ic_src -Lc_src foo.c -o foo -ltamsin && \
   ./foo `cat`
R=$?
rm -f foo.c foo
exit $R
