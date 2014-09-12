Error Reporting
---------------

For now, only the Tamsin interpreter is expected to pass these tests.

Also, these tests expose some details about how Falderal creates temp files.
Boo!

    -> Tests for functionality "Intepret Tamsin program"

When a scanning error occurs in a Tamsin source, the filename, line number,
and column number are reported.

    | hello = "h".
    |     %
    ? expected 'identifiable character' but found '%' at line 2, column 5 in '/tmp/tmp

When a parsing error occurs in a Tamsin source, the filename, line number,
and column number are reported.

    | slough = "h" & ("o" | "p").
    | maidenhead = "h" & ("o" | "p").
    | reading = "h" ("o" | "p").
    ? expected ''.'' but found '(' at line 3, column 16 in '/tmp/tmp

When a scanning error occurs in the input to a Tamsin program, the filename,
line number, and column number are reported.

    | main = "h" & "o" & "x".
    + hop
    ? expected 'x' found 'p' at line 1, column 3 in '<stdin>'

    | main = "h" & "o" & {"\n"} & "0" & "x".
    + ho
    + 
    + 0p
    ? expected 'x' found 'p' at line 3, column 2 in '<stdin>'
