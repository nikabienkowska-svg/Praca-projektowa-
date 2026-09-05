# Raport 6 — Implementacja modeli
**Etap:** zajęcia 10–12

---

## 1. Cel etapu

Zaimplementowanie wybranych w Raporcie 5 modeli w jednym, odtwarzalnym pipelinie oraz
przygotowanie ich do ewaluacji. Efektem mają być wytrenowane (zbudowane) modele gotowe do oceny.

## 2. Wykonane działania

- Implementacja ośmiu silników rekomendacji w jednym notebooku, z jednym wspólnym interfejsem
  wywołania.
- Implementacja rekonstrukcji pełnego klucza odpowiedzi z asercjami kontrolnymi.
- Implementacja metryk Precision@K, Recall@K, NDCG@K liczonych per czytelnik.
- Pomiar czasu budowy indeksu i czasu obsługi zapytań.
- Diagnostyka obcinania wejścia — sprawdzenie, ile tekstu każdy model faktycznie widzi.
- Buforowanie zanurzeń na dysku, żeby powtórne uruchomienie nie wymagało GPU.

## 3. Uzyskane rezultaty

### 3.1. Wspólny interfejs

Każdy silnik to funkcja o identycznej sygnaturze:

```python
recommend(profile: set[int], k: int, exclude: set[int]) -> list[int]
```

Dzięki temu pętla ewaluacyjna jest jedna dla wszystkich ośmiu silników i **nie ma możliwości, żeby
któryś dostał inne warunki** — to nie jest wygoda, tylko zabezpieczenie metodologiczne.

Wspólna funkcja rankingowa wyklucza artykuły startowe przez ustawienie ich wyniku na `-∞`, a nie
przez filtrowanie listy po posortowaniu — dzięki temu wykluczenie jest zawsze kompletne,
niezależnie od silnika:

```python
def _rank(scores, k, exclude):
    s = np.asarray(scores, dtype=np.float64).ravel().copy()
    s[list(exclude)] = -np.inf
    top = np.argpartition(-s, k)[:k]      # częściowe sortowanie: O(N) zamiast O(N log N)
    return top[np.argsort(-s[top])]
```

### 3.2. Zaimplementowane silniki

| # | silnik | reprezentacja | agregacja profilu |
|---|---|---|---|
| 1 | Random | brak | — |
| 2 | Popularity | częstość kategorii | — (niespersonalizowany) |
| 3 | BM25 | worek słów, 25 663 terminy | suma binarna terminów z 8 artykułów startowych |
| 4 | TF-IDF | wektor rzadki, 50 000 cech | średni wektor |
| 5 | MiniLM-mean | 384 wymiary | średni wektor |
| 6 | MiniLM-maxsim | 384 wymiary | maksimum podobieństwa |
| 7 | SPECTER2-mean | 768 wymiarów | średni wektor |
| 8 | SPECTER2-maxsim | 768 wymiarów | maksimum podobieństwa |

**TF-IDF.** `TfidfVectorizer(stop_words="english", min_df=3, max_df=0.5, ngram_range=(1,2),
max_features=50000, sublinear_tf=True)`. Wiersze normalizowane L2, więc iloczyn skalarny jest
kosinusem. Profil to średni wektor 8 artykułów startowych.

**BM25** (`k1 = 1.5`, `b = 0.75`) zaimplementowany **macierzowo**, a nie iteracyjnie: wagi
`idf · tf · (k1+1) / (tf + k1·(1 − b + b·dl/avgdl))` liczone są raz dla całej macierzy zliczeń
i zapisane jako macierz rzadka. Zapytanie sprowadza się wtedy do jednego mnożenia macierzy rzadkiej
przez wektor binarny. Bez tego zabiegu 62 zapytania po 36 314 dokumentów trwałyby minuty zamiast
ułamka sekundy.

**MiniLM** — `all-MiniLM-L6-v2`, 6 warstw, 384 wymiary, agregacja przez uśrednienie stanów
ukrytych z maską uwagi, następnie normalizacja L2.

**SPECTER2** — `allenai/specter2_base` z doładowanym adapterem `proximity` przez bibliotekę
`adapters`; reprezentacją dokumentu jest token `CLS`, zgodnie z procedurą autorów modelu,
następnie normalizacja L2.

**Popularity** — ranking po sumie częstości kategorii artykułu w korpusie. **Nazwa jest myląca
i trzeba to powiedzieć wprost:** w danych nie ma żadnych interakcji użytkowników, więc nie jest to
popularność w sensie systemów rekomendacyjnych, tylko **proxy centralności tematycznej**.

### 3.3. Rekonstrukcja klucza odpowiedzi

Zaimplementowana z dwiema asercjami kontrolnymi — kod przerywa działanie, jeśli rekonstrukcja
się nie zgadza:

```python
for u in users:
    rule = [p.strip() for p in u["topic_rule"].split(" AND ")]
    rel  = {i for i in range(N) if all(p in cats[i] for p in rule)}
    assert len(rel) == u["n_relevant_total"]        # zgodność z metadanymi generatora
    u["_profile"] = {pos[p] for p in u["profile_ids"] if p in pos}
    u["_gt"]      = rel - u["_profile"]
    assert not (u["_profile"] & u["_gt"])           # artykuł startowy nie może być w kluczu
```

Rekonstrukcja zgadza się dla **wszystkich 62 czytelników**.

### 3.4. Metryki

```python
def ndcg(hits, k, n_gt):
    dcg  = sum(1 / math.log2(i + 2) for i, h in enumerate(hits[:k]) if h)
    idcg = sum(1 / math.log2(i + 2) for i in range(min(n_gt, k))) or 1.0
    return dcg / idcg
```

Kluczowy szczegół: `IDCG` normalizuje przez `min(|GT|, K)`, a nie przez `|GT|`. Dzięki temu ranking
idealny daje NDCG = 1 **niezależnie od wielkości zbioru relewantnego** — co jest konieczne przy
nierównowadze 96:1 stwierdzonej w Raporcie 3. Bez tego czytelnicy o dużych zbiorach relewantnych
mieliby sztucznie zaniżone wyniki i średnia byłaby bez sensu.

Metryki liczone są **osobno dla każdego czytelnika** i dopiero potem uśredniane. Rozkład
per czytelnik jest zachowywany, bo jest potrzebny do testu parowanego (Raport 7).

### 3.5. Diagnostyka obcinania wejścia

Modele semantyczne mają twardy limit długości wejścia. Sprawdzono na losowej próbie 2 000
dokumentów, ile tekstu faktycznie do nich dociera:

| model | limit [word-pieces] | mediana długości | 90. percentyl | % ponad limit | **% widzianego tekstu** |
|---|---|---|---|---|---|
| MiniLM | 256 | 266 | 363 | **54,6%** | **86,5%** |
| SPECTER2 | 512 | 249 | 340 | 0,1% | 100,0% |

Silniki leksykalne czytają **100%** tekstu — nie mają limitu długości.

**To jest istotne dla interpretacji wyniku.** Ponad połowa abstraktów przekracza limit MiniLM,
przez co model widzi 86,5% treści korpusu. Jeżeli MiniLM przegra, część różnicy może wynikać
z obcięcia wejścia, a nie z jakości reprezentacji. SPECTER2 tego problemu nie ma — obcina
0,1% dokumentów — więc **porównanie SPECTER2 z TF-IDF jest wolne od tego zarzutu** i to on jest
właściwym testem hipotezy H1.

### 3.6. Pomiar kosztu i buforowanie

Czas budowy indeksu mierzony jest wewnątrz pipeline'u dla każdego silnika osobno. Zanurzenia
zapisywane są do plików `.npy`; przy ponownym uruchomieniu pipeline wczytuje cache zamiast
kodować od nowa. W tabeli kosztu wartość 0 s oznacza **wczytanie z cache'u, a nie pomiar** —
jest to jawnie oznaczone w wynikach i na wykresie kosztu, żeby nie sugerować, że model semantyczny
buduje indeks w zerowym czasie.

### 3.7. Środowisko i odtwarzalność

- `SEED = 42` we wszystkich elementach zawierających losowość.
- Pipeline pobiera dane samodzielnie i nie zakłada niczego o stanie katalogu roboczego.
- `requirements.txt` z wersjami zależności.
- Notebook uruchamialny jednym kliknięciem w Google Colab (T4).

**Kontrola odtwarzalności:** leksykalna część pipeline'u została uruchomiona niezależnie,
w osobnym środowisku, na tych samych danych. Wyniki zgadzają się co do czwartego miejsca po
przecinku (patrz Raport 7).

## 4. Problemy i sposoby ich rozwiązania

**Problem: BM25 liczony naiwnie jest zbyt wolny.** Iteracyjne przechodzenie po dokumentach dla
każdego zapytania oznacza 62 × 36 314 obliczeń wagi.
**Rozwiązanie:** przeliczenie wag BM25 raz, dla całej macierzy, i zapisanie jako macierz rzadka.
Zapytanie to jedno mnożenie. Czas budowy indeksu: ok. 5 s, czas 62 zapytań: poniżej sekundy.

**Problem: kodowanie 36 314 abstraktów na CPU trwa godzinami.**
**Rozwiązanie:** buforowanie zanurzeń do `.npy` + uruchamianie na GPU (Colab T4: MiniLM ok. 2 min,
SPECTER2 ok. 4 min). Cache w repozytorium sprawia, że powtórzenie eksperymentu nie wymaga GPU.

**Problem: `argsort` po całej macierzy podobieństw jest marnotrawstwem** przy potrzebie 10
najlepszych pozycji z 36 314.
**Rozwiązanie:** `np.argpartition` — częściowe sortowanie w czasie liniowym, a pełne sortowanie
tylko na wybranych k pozycjach.

**Problem: wykluczanie artykułów startowych po posortowaniu jest podatne na błąd.** Łatwo zwrócić
k pozycji, z których część zostanie potem odfiltrowana, i skończyć z listą krótszą niż k.
**Rozwiązanie:** ustawianie wyniku wykluczonych na `-∞` **przed** rankingiem, w jednej wspólnej
funkcji dla wszystkich silników.

**Problem: ostrzeżenia biblioteki `transformers` o tekstach dłuższych niż limit zaśmiecały
wyjście** i sprawiały wrażenie błędu.
**Rozwiązanie:** wyciszenie ostrzeżeń **i jednoczesne zmierzenie skali obcięcia** (punkt 3.5).
Ostrzeżenie nie było błędem, ale wskazywało na realny problem, który wymagał zaraportowania,
a nie tylko uciszenia.

## 5. Plan działań na kolejny etap

1. Uruchomienie pełnej ewaluacji ośmiu silników.
2. Test istotności statystycznej z korektą na porównania wielokrotne.
3. Wykresy wyników i analiza błędów na konkretnych czytelnikach — do Raportu 7.
