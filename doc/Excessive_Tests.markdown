    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = {" "} & (
    |            "c" & "a" & "t" & return meow | "d" & "o" & "g" & return woof
    |        ).
    | program = "woof".
    + dog
    = woof

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = {" "} & (
    |            "c" & "a" & "t" & return meow | "d" & "o" & "g" & return woof
    |        ).
    | program = "meow" | "woof".
    + cat
    = meow

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = {" "} & (
    |            "c" & "a" & "t" & return meow | "d" & "o" & "g" & return woof
    |        ).
    | program = "meow" | "woof".
    + dog
    = woof

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = (
    |            "c" & "a" & "t" & return meow | "d" & "o" & "g" & return woof
    |        ).
    | program = "meow" & "woof".
    + catdog
    = woof

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & "dog".
    + catdog
    = dog

    | main = program using scanner.
    | scanner = scan using $.char.
    | print(X) = $.print(X).
    | scan = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & print(1) &
    |           ("cat" & print(2) | "dog" & print(3)) &
    |           "dog" & print(4) & return ok.
    + catcatdog
    = 1
    = 2
    = 4
    = ok


    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = animal → A & " " & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & print 1 &
    |           ("cat" & print 2 | "dog" & print 3) &
    |           "dog" & print 4 & return ok.
    + cat dog dog 
    = 1
    = 3
    = 4
    = ok

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = animal → A & "," & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & print 1 &
    |           ("cat" & print 2 | "dog" & print 3) &
    |           "dog" & print 4 & return ok.
    + cat,dog,dog,
    = 1
    = 3
    = 4
    = ok

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = animal → A & "-" & ">" & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & print 1 &
    |           ("cat" & print 2 | "dog" & print 3) &
    |           "dog" & print 4 & return ok.
    + cat->dog->dog->
    = 1
    = 3
    = 4
    = ok

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = "X" & (
    |          "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & "dog".
    + XcatXdog
    = dog

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = " " & (
    |          "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & "dog".
    +  cat dog
    = dog

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = " " & animal.
    | animal = (
    |          "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & "dog".
    +  cat dog
    = dog

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = "(" & animal.
    | animal = (
    |          "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & "dog".
    + (cat(dog
    = dog

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = "(" & animal → A & ")" & return A.
    | animal = (
    |          "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & "dog".
    + (cat)(dog)
    = dog

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = " " & animal → A & ")" & return A.
    | animal = (
    |          "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & "dog".
    +  cat) dog)
    = dog

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = " " & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & "dog".
    +  cat dog
    = dog

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = " " & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & ("dog" | "cat").
    +  cat dog
    = dog

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = " " & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & ("dog" | "cat").
    +  cat cat
    = cat

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = " " & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & ("cat" | "dog") & "dog".
    +  cat cat dog
    = dog

    | main = program using scanner.
    | scanner = (scan | return unknown) using $.char.
    | scan = " " & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & ("cat" | "dog") & "dog".
    +  cat dog dog
    = dog

    | main = program using scanner.
    | scanner = (scan | return unknown) using $.char.
    | scan = " " & animal → A & return A.
    | animal = "c" & "a" & "t" & return cat
    |        | "d" & "o" & "g" & return dog
    |        | return unknown.
    | program = "cat" & ("cat" | "dog") & "dog".
    +  cat dog dog
    = dog

    | main = program using scanner.
    | scanner = (scan | return unknown) using $.char.
    | scan = " " & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |            | "."
    |          ).
    | program = "cat" & ("cat" | "dog") & "dog" & ".".
    +  cat dog dog .
    = .

    | main = program using scanner.
    | scanner = (scan | return unknown) using $.char.
    | scan = " " & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & ("dog" | "cat") & "dog".
    +  cat cat dog
    = dog

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = " " & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & ("dog" | "cat") & "dog".
    +  cat dog dog
    = dog

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = " " & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & print 1 &
    |           ("cat" & print 2 | "dog" & print 3) &
    |           "dog" & print 4 & return ok.
    +  cat dog dog
    = 1
    = 3
    = 4
    = ok

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = "X" & animal → A & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & print 1 &
    |           ("cat" & print 2 | "dog" & print 3) &
    |           "dog" & print 4 & return ok.
    + XcatXdogXdog
    = 1
    = 3
    = 4
    = ok

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = "(" & animal → A & ")" & return A.
    | animal = (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |          ).
    | program = "cat" & print 1 &
    |           ("cat" & print 2 | "dog" & print 3) &
    |           "dog" & print 4 & return ok.
    + (cat)(dog)(dog)
    = 1
    = 3
    = 4
    = ok

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = {" "} & (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & "dog".
    + cat dog
    = dog

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = {" "} & (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & print 1 &
    |           ("cat" & print 2 | "dog" & print 3) &
    |           "dog" & print 4 & return ok.
    + cat cat dog
    = 1
    = 2
    = 4
    = ok
    
    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = {" "} & (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & print 1 &
    |           ("cat" & print 2 | "dog" & print 3) &
    |           "dog" & print 4 & return ok.
    + cat dog dog
    = 1
    = 3
    = 4
    = ok

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = {" "} & (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & ("cat" | "dog") & "dog".
    + cat cat cat
    ? expected 'dog' found 'cat'

    | main = program using scanner.
    | scanner = scan using $.char.
    | scan = {" "} & (
    |            "c" & "a" & "t" & return cat | "d" & "o" & "g" & return dog
    |        ).
    | program = "cat" & ("cat" | "dog") & "dog".
    + dog dog dog
    ? expected 'cat' found 'dog'
