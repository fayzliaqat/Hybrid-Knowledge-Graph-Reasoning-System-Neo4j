% -------------------------------------------------------------------------
% EXHAUSTIVE GRAPH REASONING ENGINE CORE — CLEAN DIRECT BLOOD PERMUTATIONS
% -------------------------------------------------------------------------

% --- LAYER 1: SIBLING TRANSITIVITY PROPAGATION ---
extended_sibling(X, Y) :- sibling(X, Y).
extended_sibling(X, Y) :- sibling(X, Z), sibling(Z, Y).

% --- LAYER 2: BASE DECOUPLING PROPAGATION ---
actual_parent(X, Y) :- parent(X, Y).
actual_parent(X, Y) :- extended_sibling(Y, Z), parent(X, Z).

% --- LAYER 3: CORE DIRECT LINEAGE ---
father(X, Y) :- actual_parent(X, Y), male(X).
mother(X, Y) :- actual_parent(X, Y), female(X).
child(X, Y)  :- actual_parent(Y, X).
son(X, Y)    :- actual_parent(Y, X), male(X).
daughter(X, Y) :- actual_parent(Y, X), female(X).

husband(X, Y) :- married(X, Y), male(X).
wife(X, Y)    :- married(X, Y), female(X).
spouse(X, Y)  :- married(X, Y).

brother(X, Y) :- extended_sibling(X, Y), male(X).
sister(X, Y)  :- extended_sibling(X, Y), female(X).

% --- LAYER 4: ROBUST GENERATIONAL MULTI-HOPS ---
grandfather(X, Y) :- actual_parent(X, Z), actual_parent(Z, Y), male(X).
grandmother(X, Y) :- actual_parent(X, Z), actual_parent(Z, Y), female(X).

dada(X, Y) :- grandfather(X, Y), father(Z, Y), actual_parent(X, Z).
dadi(X, Y) :- grandmother(X, Y), father(Z, Y), actual_parent(X, Z).
nana(X, Y) :- grandfather(X, Y), mother(Z, Y), actual_parent(X, Z).
nani(X, Y) :- grandmother(X, Y), mother(Z, Y), actual_parent(X, Z).

grandparent(X, Y) :- grandfather(X, Y).
grandparent(X, Y) :- grandmother(X, Y).

great_grandfather(X, Y) :- actual_parent(X, A), actual_parent(A, B), actual_parent(B, Y), male(X).
great_grandmother(X, Y) :- actual_parent(X, A), actual_parent(A, B), actual_parent(B, Y), female(X).

grandchild(X, Y)     :- grandparent(Y, X).
grandson(X, Y)       :- grandfather(Y, X), male(X).
grandson(X, Y)       :- grandmother(Y, X), male(X).
granddaughter(X, Y) :- grandfather(Y, X), female(X).
granddaughter(X, Y) :- grandmother(Y, X), female(X).

% --- LAYER 5: EXTENDED PATERNAL / MATERNAL BRANCHES ---
chacha(X, Y) :- father(F, Y), brother(X, F).
taya(X, Y)   :- father(F, Y), brother(X, F).
phupho(X, Y) :- father(F, Y), sister(X, F).
mama(X, Y)   :- mother(M, Y), brother(X, M).
maamu(X, Y)  :- mother(M, Y), brother(X, M).
khala(X, Y)  :- mother(M, Y), sister(X, M).

% --- LAYER 6: AFFINAL RELATIONS (MARRIAGE BOUNDS) ---
chachi(X, Y) :- chacha(U, Y), wife(X, U).
tai(X, Y)    :- taya(U, Y), wife(X, U).
phupha(X, Y) :- phupho(A, Y), husband(X, A).
mami(X, Y)   :- mama(U, Y), wife(X, U).
khalu(X, Y)  :- khala(A, Y), husband(X, A).

sasur(X, Y) :- married(Y, Z), father(X, Z).
saas(X, Y)  :- married(Y, Z), mother(X, Z).
bhabhi(X, Y) :- brother(B, Y), wife(X, B).
bahnoi(X, Y) :- sister(S, Y), husband(X, S).
bahu(X, Y)   :- son(S, Y), wife(X, S).
damad(X, Y)  :- daughter(D, Y), husband(X, D).

% --- LAYER 7: DESCENDANT COLLATERAL OFFSETS ---
bhatija(X, Y) :- brother(B, Y), son(X, B).
bhatiji(X, Y) :- brother(B, Y), daughter(X, B).
bhanja(X, Y)  :- sister(S, Y), son(X, S).
bhanji(X, Y)  :- sister(S, Y), daughter(X, S).

nephew(X, Y) :- bhatija(X, Y).
nephew(X, Y) :- bhanja(X, Y).
niece(X, Y)  :- bhatiji(X, Y).
niece(X, Y)  :- bhanji(X, Y).

cousin(X, Y) :- actual_parent(A, X), actual_parent(B, Y), extended_sibling(A, B).

great_uncle(X, Y) :- grandparent(G, Y), brother(X, G).
great_aunt(X, Y)  :- grandparent(G, Y), sister(X, G).

cousin_once_removed(X, Y) :- cousin(C, Y), actual_parent(C, X).

ancestor(X, Y) :- actual_parent(X, Y).
ancestor(X, Y) :- actual_parent(X, Z), actual_parent(Z, Y).
descendant(X, Y) :- ancestor(Y, X).

related(X, Y) :- ancestor(X, Y).
related(X, Y) :- ancestor(Y, X).
related(X, Y) :- cousin(X, Y).