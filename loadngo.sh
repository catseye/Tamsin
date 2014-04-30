#!/bin/sh

bin/tamsin compile $1 > foo.c && \
   gcc foo.c -o foo && \
   ./foo "`cat $2`"
