
    -> Functionality "Intepret Tamsin program" is implemented by
    -> shell command
    -> "bin/tamsin-compiler <%(test-body-file) >tmp/foo.c && gcc -Werror -Ic_src -Lc_src tmp/foo.c -o tmp/foo -ltamsin && tmp/foo <%(test-input-file)"

