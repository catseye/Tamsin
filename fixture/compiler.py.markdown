
    -> Functionality "Intepret Tamsin program" is implemented by
    -> shell command
    -> "./bin/tamsin loadngo %(test-body-file) < %(test-input-file)"

    -> Functionality "Intepret Tamsin program (pre- & post-processed)"
    -> is implemented by
    -> shell command "cat %(test-input-file) | bin/inhex | bin/tamsin loadngo %(test-body-file) | bin/hexout"
