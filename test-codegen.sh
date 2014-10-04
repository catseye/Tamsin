#!/bin/sh

YES="
eg/hello-world.tamsin eg/bits.tamsin eg/bitpair.tamsin
eg/exciting-long.tamsin eg/list-of-chars.tamsin
eg/modules.tamsin
"

FILES="eg/reverse.tamsin"

NO="eg/eval-bool-expr.tamsin"

for FILE in $FILES; do
  tamsin codegen $FILE || exit 1
done
