Tests that used to be in Tamsin's README
========================================

    -> Tests for functionality "Intepret Tamsin program"

Hello, world!

    | main = 'Hello, world!'.
    = Hello, world!

Make a story more exciting!

    | main = ("." & '!' | "?" & '?!' | any)/''.
    + Chapter 1
    + ---------
    + It was raining.  She knocked on the door.  She heard
    + footsteps inside.  The door opened.  The butler peered
    + out.  "Hello," she said.  "May I come in?"
    = Chapter 1
    = ---------
    = It was raining!  She knocked on the door!  She heard
    = footsteps inside!  The door opened!  The butler peered
    = out!  "Hello," she said!  "May I come in?!"

Parse an algebraic expression for syntactic correctness.

    | main = (expr0 & eof & 'ok').
    | expr0 = expr1 & {"+" & expr1}.
    | expr1 = term & {"*" & term}.
    | term = "x" | "y" | "z" | "(" & expr0 & ")".
    + x+y*(z+x+y)
    = ok

Parse an algebraic expression to a syntax tree.

    | main = expr0.
    | expr0 = expr1 → E1 & {"+" & expr1 → E2 & E1 ← add(E1,E2)} & E1.
    | expr1 = term → E1 & {"*" & term → E2 & E1 ← mul(E1,E2)} & E1.
    | term = "x" | "y" | "z" | "(" & expr0 → E & ")" & E.
    + x+y*(z+x+y)
    = add(x, mul(y, add(add(z, x), y)))

Translate an algebraic expression to RPN (Reverse Polish Notation).

    | main = expr0 → E & walk(E).
    | expr0 = expr1 → E1 & {"+" & expr1 → E2 & E1 ← add(E1,E2)} & E1.
    | expr1 = term → E1 & {"*" & term → E2 & E1 ← mul(E1,E2)} & E1.
    | term = "x" | "y" | "z" | "(" & expr0 → E & ")" & E.
    | walk(add(L,R)) = walk(L) → LS & walk(R) → RS & return LS+RS+' +'.
    | walk(mul(L,R)) = walk(L) → LS & walk(R) → RS & return LS+RS+' *'.
    | walk(X) = return ' '+X.
    + x+y*(z+x+y)
    =  x y z x + y + * +

Reverse a list.

    | main = reverse(pair(a, pair(b, pair(c, nil))), nil).
    | reverse(pair(H, T), A) = reverse(T, pair(H, A)).
    | reverse(nil, A) = A.
    = pair(c, pair(b, pair(a, nil)))

Parse and evaluate a Boolean expression.

    | main = expr0 → E using scanner & eval(E).
    | expr0 = expr1 → E1 & {"or" & expr1 → E2 & E1 ← or(E1,E2)} & E1.
    | expr1 = term → E1 & {"and" & term → E2 & E1 ← and(E1,E2)} & E1.
    | term = "true" | "false" | "(" & expr0 → E & ")" & E.
    | eval(and(A, B)) = eval(A) → EA & eval(B) → EB & and(EA, EB).
    | eval(or(A, B)) = eval(A) → EA & eval(B) → EB & or(EA, EB).
    | eval(X) = X.
    | and(true, true) = 'true'.
    | and(A, B) = 'false'.
    | or(false, false) = 'false'.
    | or(A, B) = 'true'.
    | scanner = scan using $:utf8.
    | scan = {" "} & ("(" | ")" | token).
    | token = "f" & "a" & "l" & "s" & "e" & 'false'
    |       | "t" & "r" & "u" & "e" & 'true'
    |       | "o" & "r" & 'or'
    |       | "a" & "n" & "d" & 'and'.
    + (falseortrue)andtrue
    = true

Parse a CSV file and write out the 2nd-last field of each record.  Handles
commas and double-quotes inside quotes.

    | main = line → L & L ← lines(nil, L) &
    |        {"\n" & line → M & L ← lines(L, M)} & extract(L) & ''.
    | line = field → F & {"," & field → G & F ← fields(G, F)} & F.
    | field = strings | bare.
    | strings = string → T & {string → S & T ← T + '"' + S} & T.
    | string = "\"" & T ← '' & {!"\"" & any → S & T ← T + S} & "\"" & T.
    | bare = T ← '' & {!(","|"\n") & any → S & T ← T + S} & T.
    | extract(lines(Lines, Line)) = extract(Lines) & extract_field(Line).
    | extract(L) = L.
    | extract_field(fields(Last, fields(This, X))) = print This.
    | extract_field(X) = return X.
    + Harold,1850,"21 Baxter Street",burgundy
    + Smythe,1833,"31 Little Street, St. James",mauve
    + Jones,1791,"41 ""The Gardens""",crimson
    = 21 Baxter Street
    = 31 Little Street, St. James
    = 41 "The Gardens"

Evaluate a trivial S-expression-based language.

    | main = sexp → S using scanner & reverse(S, nil) → SR & eval(SR).
    | scanner = scan using $:utf8.
    | scan = {" "} & ("(" | ")" | (T ← '' & {$:alnum → S & T ← T + S} & return T)).
    | sexp = $:alnum | list.
    | list = "(" & listtail(nil).
    | listtail(L) = sexp → S & listtail(pair(S, L)) | ")" & L.
    | head(pair(A, B)) = return A.
    | tail(pair(A, B)) = return B.
    | cons(A, B) = return pair(A, B).
    | eval(pair(head, pair(X, nil))) = eval(X) → R & head(R).
    | eval(pair(tail, pair(X, nil))) = eval(X) → R & tail(R).
    | eval(pair(cons, pair(A, pair(B, nil)))) =
    |    eval(A) → AE & eval(B) → BE & return pair(AE, BE).
    | eval(X) = X.
    | reverse(pair(H, T), A) = reverse(H, nil) → HR & reverse(T, pair(HR, A)).
    | reverse(nil, A) = A.
    | reverse(X, A) = X.
    + (head (tail (cons (cons a nil) (cons b nil))))
    = b
