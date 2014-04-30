Case Study: Parsing and Evaluating S-Expressions in Tamsin
==========================================================

    -> Tests for functionality "Intepret Tamsin program"

We now have enough tools at our disposal to parse and evaluate simple
S-expressions (from Lisp or Scheme).

We can write such a parser with `{}`, but the result is a bit messy.

    | main = sexp using $.tamsin.
    | sexp = symbol | list.
    | list = "(" &
    |        set L = nil &
    |        {sexp → S & set L = pair(S, L)} &
    |        ")" &
    |        return L.
    | symbol = "cons" | "head" | "tail" | "nil" | "a" | "b" | "c".
    + (cons (a (cons b nil)))
    = pair(pair(pair(nil, pair(b, pair(cons, nil))), pair(a, nil)), pair(cons, nil))

So let's write it in the less intuitive, recursive way:

    | main = sexp using $.tamsin.
    | 
    | sexp = symbol | list.
    | list = "(" & listtail(nil).
    | listtail(L) = sexp → S & listtail(pair(S, L))
    |             | ")" & return L.
    | symbol = "cons" | "head" | "tail" | "nil" | "a" | "b" | "c".
    + (a b)
    = pair(b, pair(a, nil))

Nice.  But it returns a term that's backwards.  So we need to write a
reverser.  In Erlang, this would be

    reverse([H|T], A) -> reverse(T, [H|A]).
    reverse([], A) -> A.

In Tamsin, it's:

    | main = sexp → S using $.tamsin & reverse(S, nil) → SR & return SR.
    | 
    | sexp = symbol | list.
    | list = "(" & listtail(nil).
    | listtail(L) = sexp → S & listtail(pair(S, L))
    |             | ")" & return L.
    | symbol = "cons" | "head" | "tail" | "nil" | "a" | "b" | "c".
    | 
    | reverse(pair(H, T), A) =
    |   reverse(T, pair(H, A)) → TR &
    |   return TR.
    | reverse(nil, A) =
    |   return A.
    + (a b)
    = pair(a, pair(b, nil))

But it's not deep.  It only reverses the top-level list.

    | main = sexp → S using $.tamsin & reverse(S, nil) → SR & return SR.
    | 
    | sexp = symbol | list.
    | list = "(" & listtail(nil).
    | listtail(L) = sexp → S & listtail(pair(S, L))
    |             | ")" & return L.
    | symbol = "cons" | "head" | "tail" | "nil" | "a" | "b" | "c".
    | 
    | reverse(pair(H, T), A) =
    |   reverse(T, pair(H, A)) → TR &
    |   return TR.
    | reverse(nil, A) =
    |   return A.
    + (a (c b) b)
    = pair(a, pair(pair(b, pair(c, nil)), pair(b, nil)))

So here's a deep reverser.

    | main = sexp → S using $.tamsin & reverse(S, nil) → SR & return SR.
    | 
    | sexp = symbol | list.
    | list = "(" & listtail(nil).
    | listtail(L) = sexp → S & listtail(pair(S, L))
    |             | ")" & return L.
    | symbol = "cons" | "head" | "tail" | "nil" | "a" | "b" | "c".
    | 
    | reverse(pair(H, T), A) =
    |   reverse(H, nil) → HR &
    |   reverse(T, pair(HR, A)) → TR &
    |   return TR.
    | reverse(nil, A) =
    |   return A.
    | reverse(X, A) =
    |   return X.
    + (a (c b) b)
    = pair(a, pair(pair(c, pair(b, nil)), pair(b, nil)))

Finally, a little sexpr evaluator.

    | main = sexp → S using $.tamsin & reverse(S, nil) → SR & eval(SR).
    | 
    | sexp = symbol | list.
    | list = "(" & listtail(nil).
    | listtail(L) = sexp → S & listtail(pair(S, L))
    |             | ")" & return L.
    | symbol = "cons" | "head" | "tail" | "nil" | "a" | "b" | "c".
    | 
    | head(pair(A, B)) = return A.
    | tail(pair(A, B)) = return B.
    | cons(A, B) = return pair(A, B).
    | 
    | eval(pair(head, pair(X, nil))) = eval(X) → R & head(R) → P & return P.
    | eval(pair(tail, pair(X, nil))) = eval(X) → R & tail(R) → P & return P.
    | eval(pair(cons, pair(A, pair(B, nil)))) =
    |    eval(A) → AE & eval(B) → BE & return pair(AE, BE).
    | eval(X) = return X.
    | 
    | reverse(pair(H, T), A) =
    |   reverse(H, nil) → HR &
    |   reverse(T, pair(HR, A)) → TR &
    |   return TR.
    | reverse(nil, A) =
    |   return A.
    | reverse(X, A) =
    |   return X.
    + (cons a b)
    = pair(a, b)

    | main = sexp → S using $.tamsin & reverse(S, nil) → SR & eval(SR).
    | 
    | sexp = symbol | list.
    | list = "(" & listtail(nil).
    | listtail(L) = sexp → S & listtail(pair(S, L))
    |             | ")" & return L.
    | symbol = "cons" | "head" | "tail" | "nil" | "a" | "b" | "c".
    | 
    | head(pair(A, B)) = return A.
    | tail(pair(A, B)) = return B.
    | cons(A, B) = return pair(A, B).
    | 
    | eval(pair(head, pair(X, nil))) = eval(X) → R & head(R) → P & return P.
    | eval(pair(tail, pair(X, nil))) = eval(X) → R & tail(R) → P & return P.
    | eval(pair(cons, pair(A, pair(B, nil)))) =
    |    eval(A) → AE & eval(B) → BE & return pair(AE, BE).
    | eval(X) = return X.
    | 
    | reverse(pair(H, T), A) =
    |   reverse(H, nil) → HR &
    |   reverse(T, pair(HR, A)) → TR &
    |   return TR.
    | reverse(nil, A) =
    |   return A.
    | reverse(X, A) =
    |   return X.
    + (head (cons b a))
    = b

    | main = sexp → S using $.tamsin & reverse(S, nil) → SR & eval(SR).
    | 
    | sexp = symbol | list.
    | list = "(" & listtail(nil).
    | listtail(L) = sexp → S & listtail(pair(S, L))
    |             | ")" & return L.
    | symbol = "cons" | "head" | "tail" | "nil" | "a" | "b" | "c".
    | 
    | head(pair(A, B)) = return A.
    | tail(pair(A, B)) = return B.
    | cons(A, B) = return pair(A, B).
    | 
    | eval(pair(head, pair(X, nil))) = eval(X) → R & head(R) → P & return P.
    | eval(pair(tail, pair(X, nil))) = eval(X) → R & tail(R) → P & return P.
    | eval(pair(cons, pair(A, pair(B, nil)))) =
    |    eval(A) → AE & eval(B) → BE & return pair(AE, BE).
    | eval(X) = return X.
    | 
    | reverse(pair(H, T), A) =
    |   reverse(H, nil) → HR &
    |   reverse(T, pair(HR, A)) → TR &
    |   return TR.
    | reverse(nil, A) =
    |   return A.
    | reverse(X, A) =
    |   return X.
    + (tail (tail (cons b (cons b a))))
    = a

In this one, we make the evaluator print out some of the steps it takes.

    | main = sexp → S using $.tamsin & reverse(S, nil) → SR & eval(SR).
    | 
    | sexp = symbol | list.
    | list = "(" & listtail(nil).
    | listtail(L) = sexp → S & listtail(pair(S, L))
    |             | ")" & return L.
    | symbol = "cons" | "head" | "tail" | "nil" | "a" | "b" | "c".
    | 
    | head(pair(A, B)) = return A.
    | tail(pair(A, B)) = return B.
    | cons(A, B) = return pair(A, B).
    | 
    | eval(pair(head, pair(X, nil))) = eval(X) → R & head(R) → P & return P.
    | eval(pair(tail, pair(X, nil))) = eval(X) → R & tail(R) → P & return P.
    | eval(pair(cons, pair(A, pair(B, nil)))) =
    |    eval(A) → AE & eval(B) → BE &
    |    $.print(y(AE, BE)) & cons(AE, BE) → C & return C.
    | eval(X) = return X.
    | 
    | reverse(pair(H, T), A) =
    |   reverse(H, nil) → HR &
    |   reverse(T, pair(HR, A)) → TR &
    |   return TR.
    | reverse(nil, A) =
    |   return A.
    | reverse(X, A) =
    |   return X.
    + (cons (tail (cons b a)) (head (cons b a)))
    = y(b, a)
    = y(b, a)
    = y(a, b)
    = pair(a, b)
