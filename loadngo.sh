#!/bin/sh

bin/tamsin compile $1 > foo.c && \
   gcc -g -Ic_src -Lc_src foo.c -o foo -ltamsin && \
   ./foo
R=$?
#rm -f foo.c foo
exit $R
