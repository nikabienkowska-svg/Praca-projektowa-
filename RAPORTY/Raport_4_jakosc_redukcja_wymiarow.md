# Raport 4 — Jakość danych, redukcja wymiarów, kluczowe cechy, wizualizacje
**Etap:** zajęcia 5–7

---

## 1. Cel etapu

Identyfikacja problemów jakości danych, zbudowanie reprezentacji wektorowej, zastosowanie metody
redukcji wymiarów, wskazanie kluczowych cech oraz przygotowanie wizualizacji. Efektem mają być
dane gotowe do modelowania.

## 2. Wykonane działania

- Zbudowanie macierzy TF-IDF dla całego korpusu i pomiar jej charakterystyki.
- Redukcja wymiarów metodą **Truncated SVD** (odpowiednik PCA dla macierzy rzadkich — patrz punkt 4)
  do 150 składowych, z pomiarem skumulowanej wyjaśnionej wariancji.
- Identyfikacja kluczowych terminów: globalnie (masa TF-IDF) oraz w pięciu pierwszych składowych
  ukrytych.
- Audyt jakości danych pod kątem wpływu na wynik pomiaru, nie tylko na poprawność zapisu.
- Wykonanie czterech wizualizacji do raportu.

## 3. Uzyskane rezultaty

### Reprezentacja TF-IDF

| parametr | wartość |
|---|---|
| słownik przed filtrowaniem | 71 216 terminów |
| `min_df = 3`, `max_df = 0.5`, bigramy, `max_features = 50 000` | |
| **wymiar końcowy** | **50 000 cech** |
| niezerowych elementów | 4 309 012 |
| **rzadkość macierzy** | **99,76%** |
| średnio niezerowych terminów na dokument | 118,7 |

Macierz 36 314 × 50 000 zawiera 1,8 mld komórek, z czego wypełnione jest 4,3 mln — stąd
przechowywanie w formacie rzadkim (CSR) jest tu koniecznością, a nie optymalizacją. Wiersze są
normalizowane do długości jednostkowej (L2), dzięki czemu iloczyn skalarny jest podobieństwem
kosinusowym. **To jest odpowiednik standaryzacji dla danych tekstowych** — bez niego dłuższe
abstrakty dominowałyby ranking samą swoją długością.

### Redukcja wymiarów — Truncated SVD

| liczba składowych | skumulowana wyjaśniona wariancja |
|---|---|
| 10 | 2,22% |
| 50 | 5,78% |
| 100 | 8,51% |
| 150 | 10,56% |

Wykres: `fig_svd.png`.

**Wynik jest negatywny i to jest jego wartość informacyjna.** 150 składowych — trzysta razy mniej
niż wymiar wyjściowy — wyjaśnia zaledwie **10,6%** wariancji, a krzywa nie ma kolana. Nie istnieje
niskowymiarowa podprzestrzeń, do której dałoby się rzutować ten korpus bez istotnej straty
informacji.

**Konsekwencja dla projektu: rezygnujemy z redukcji wymiarów w pipelinie rekomendacji.**
Uzasadnienie:

1. Sygnał rozróżniający artykuły jest w tym korpusie **rozproszony po tysiącach rzadkich,
   specjalistycznych terminów**, a nie skoncentrowany w kilkudziesięciu kierunkach głównych.
   Właśnie te rzadkie terminy (`fMRI`, `spiking`, `neuromorphic`) rozstrzygają o przynależności
   tematycznej — czyli o tym, co mierzymy.
2. Rzutowanie na 150 wymiarów uśredniłoby dokładnie ten sygnał i obniżyło trafność, żeby
   zaoszczędzić pamięć, której nie brakuje (macierz rzadka waży kilkadziesiąt MB).
3. Redukcja wymiarów **nie jest w tym projekcie porzucona** — została zastąpiona przez podejście
   uczone. Modele semantyczne to nic innego jak redukcja 50 000 wymiarów leksykalnych do
   384 (MiniLM) albo 768 (SPECTER2) wymiarów **wyuczonych na danych**, zamiast wyznaczonych
   liniowo. Porównanie TF-IDF z modelami semantycznymi jest więc jednocześnie porównaniem
   reprezentacji rzadkiej pełnowymiarowej z gęstą zredukowaną.

Ten punkt warto wypowiedzieć wprost przy obronie: SVD nie zostało pominięte, tylko **wykonane,
zmierzone i odrzucone na podstawie pomiaru**.

### Kluczowe cechy

**Terminy o największej masie TF-IDF w całym korpusie** (25 pierwszych):

> model · learning · models · neural · based · data · networks · network · brain · using · human ·
> recognition · performance · language · information · results · time · systems · framework ·
> large · methods · approach · tasks · paper · training

Zwraca uwagę obecność słów proceduralnych (`based`, `using`, `results`, `paper`, `approach`) —
to szum retoryczny wspólny wszystkim pracom naukowym, który nie rozróżnia tematów. Filtr
`max_df = 0.5` usuwa terminy występujące w ponad połowie dokumentów, ale te mieszczą się poniżej
progu.

**Pięć pierwszych składowych SVD** — interpretacja osi tematycznych korpusu:

| składowa | dominujące terminy | interpretacja |
|---|---|---|
| C1 | learning, models, model, neural, based, data | oś ogólna — „praca o uczeniu maszynowym", niesie wspólne tło |
| C2 | neural, networks, neurons, spiking, dynamics, brain, spike | **neuronauka obliczeniowa** |
| C3 | recognition, training, deep, classification, speech, image, accuracy | **uczenie nadzorowane i percepcja** |
| C4 | spiking, snns, neuromorphic, snn, energy, hardware | **sprzęt neuromorficzny** |
| C5 | ai, intelligence, artificial, machine learning, research | **prace przeglądowe i pozycyjne o AI** |

Struktura tematyczna korpusu jest więc czytelna i zgodna z regułą zakresu z Raportu 2: kręgosłup
neuronaukowy (C2, C4) plus przylegająca sztuczna inteligencja (C1, C3, C5). To jest kontrola
poprawności budowy korpusu — gdyby składowe wskazywały na tematy spoza zakresu, oznaczałoby to
błąd filtra.

### Audyt jakości danych pod kątem wpływu na pomiar

Poza kontrolą kompletności z Raportu 3 wykryto **jeden problem jakościowy o krytycznych
konsekwencjach**, dotyczący nie korpusu, lecz klucza odpowiedzi.

**Klucz odpowiedzi w `users.json` jest obcięty do 60 pozycji** (`gt_cap = 60`), podczas gdy pole
`n_relevant_total` przechowuje pełną liczność zbioru relewantnego, sięgającą **1 926** artykułów.

Skala problemu, przeliczona z danych:

| | |
|---|---|
| czytelnicy z obciętym kluczem | **36 z 62** |
| mediana liczności klucza | 60 → **91** po rekonstrukcji |
| maksimum liczności klucza | 60 → **1 918** po rekonstrukcji |

Dla najbardziej dotkniętego czytelnika w kluczu znajdowało się 60 z 1 918 faktycznie relewantnych
artykułów — czyli **model trafiający w relewantną pracę dostawał punkt z prawdopodobieństwem
około 3%, a w 97% przypadków był karany za trafną rekomendację.**

**Rozwiązanie:** pełny zbiór relewantny jest odtwarzany z reguły `topic_rule` na całym korpusie,
a rekonstrukcja jest **weryfikowana asercją** względem pola `n_relevant_total` — zgadza się dla
wszystkich 62 czytelników. Dodatkowa asercja sprawdza, że żaden artykuł startowy nie trafił do
klucza. Bez pola `n_relevant_total` zapisanego na etapie generowania (Raport 2) rekonstrukcji nie
dałoby się zweryfikować.

**To jest najważniejsze pojedyncze ustalenie całego projektu.** Wpływ na wyniki jest opisany
w Raporcie 7.

### Wizualizacje

| plik | zawartość |
|---|---|
| `fig_dlugosc_abstraktow.png` | rozkład długości abstraktów z zaznaczoną medianą |
| `fig_kategorie.png` | 15 najczęstszych kategorii arXiv |
| `fig_svd.png` | skumulowana wyjaśniona wariancja SVD — uzasadnienie rezygnacji z redukcji |
| `fig_zbior_relewantny.png` | rozkład liczności zbiorów relewantnych z progiem `gt_cap = 60` |

## 4. Problemy i sposoby ich rozwiązania

**Problem: PCA nie działa na macierzy rzadkiej.** Klasyczne PCA wymaga wycentrowania danych, co
zamieniłoby macierz rzadką (4,3 mln niezer) na gęstą (1,8 mld komórek) — kilkanaście gigabajtów
pamięci.
**Rozwiązanie:** **Truncated SVD**, czyli rozkład według wartości osobliwych bez centrowania.
Na danych tekstowych jest to standard (metoda znana jako Latent Semantic Analysis) i daje ten
sam typ informacji o kierunkach największej wariancji.

**Problem: redukcja wymiarów nie przynosi oczekiwanego efektu.** 10,6% wariancji przy 150
składowych to wynik, którego nie da się użyć zgodnie z pierwotnym planem.
**Rozwiązanie:** potraktowanie wyniku jako rezultatu, a nie porażki. Pomiar uzasadnia decyzję
projektową (pozostajemy przy reprezentacji rzadkiej) i wprowadza właściwe ramy dla modeli
semantycznych — jako alternatywnej, uczonej redukcji wymiarów.

**Problem: obcięty klucz odpowiedzi.** Wykryty dopiero na tym etapie, mimo że powstał na etapie
generowania danych.
**Rozwiązanie:** rekonstrukcja z reguły + podwójna asercja. Lekcja procesowa: **wszystko, co
w pliku danych jest zapisane „na skróty", trzeba sprawdzić przed pomiarem, a nie po** — obcięcie
było widoczne w `users.json` od początku, tylko nikt nie sprawdził, do czego prowadzi.

## 5. Plan działań na kolejny etap

1. Systematyczny przegląd podejść: klasyczne metody rekomendacji treściowej wobec metod ML/AI.
2. Porównanie obu rodzin wg siedmiu kryteriów podanych przez prowadzącego.
3. Wybór konkretnych modeli do implementacji — do Raportu 5.
