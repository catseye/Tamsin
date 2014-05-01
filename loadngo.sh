#!/bin/sh

INPUT=`cat`
bin/tamsin compile $1 > foo.c && \
   gcc foo.c -o foo && \
   ./foo "$INPUT"
