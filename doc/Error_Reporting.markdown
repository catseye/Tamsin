Error Reporting
---------------

For now, only the Tamsin interpreter is expected to pass these tests.

    -> Tests for functionality "Intepret Tamsin program"

When a scanning error occurs in a Tamsin source, the filename, line number,
and column number are reported.

    | hello = "h".
    |     %
    ? expected identifiable character at line 2, column 5 in `filename`

When a parsing error occurs in a Tamsin source, the filename, line number,
and column number are reported.

    | slough = "h" & ("o" | "p").
    | maidenhead = "h" & ("o" | "p").
    | reading = "h" ("o" | "p").
    ? expected '.' at line 3, column 14 in `filename`

When a scanning error occurs in the input to a Tamsin program, the filename,
line number, and column number are reported.

    | main = "h" & "o" & "x".
    + hop
    ? expected 'x' found 'p' at line 1, column 3 in `filename`

    | main = "h" & "o" & {"\n"} & "0" & "x".
    + ho
    + 
    + 0p
    ? expected 'x' found 'p' at line 3, column 2 in `filename`
