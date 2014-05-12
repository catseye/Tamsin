
    -> Functionality "Intepret Tamsin program" is implemented by
    -> shell command
    -> "bin/bootstrapped-compiler <%(test-body-file) >tmp/foo.c && gcc -Ic_src -Lc_src tmp/foo.c -o tmp/foo -ltamsin && tmp/foo <%(test-input-file)"

    -> Functionality "Intepret Tamsin program (pre- & post-processed)"
    -> is implemented by
    -> shell command "bin/bootstrapped-compiler <%(test-body-file) >tmp/foo.c && gcc -Ic_src -Lc_src tmp/foo.c -o tmp/foo -ltamsin && cat %(test-input-file) | bin/inhex | tmp/foo | bin/hexout"

