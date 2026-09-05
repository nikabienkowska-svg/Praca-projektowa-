# Raport 2 — Pozyskanie danych
**Etap:** zajęcia 3–4

> **Uwaga do wersji.** Ten raport zastępuje wcześniejszą wersję, w której podano liczebności
> `total = 34 512`, `q-bio.NC = 12 405`, `cs.AI = 15 120`, `cs.NE = 6 987`. Liczby te nie zgadzają
> się z faktycznie zbudowanym korpusem i zostały zastąpione wartościami wyliczonymi z pliku
> danych. Wszystkie liczby poniżej pochodzą z `corpus_meta.json` i z bezpośredniego przeliczenia
> `corpus.jsonl.gz`.

---

## 1. Cel etapu

Pozyskanie i opisanie zbioru danych: źródło, sposób pozyskania, liczba obserwacji, struktura
rekordu oraz potencjalne problemy jakościowe. Efektem ma być gotowy, udokumentowany zbiór do
dalszej analizy.

## 2. Wykonane działania

- **Wybór źródła.** Zdecydowano się na publiczny zrzut metadanych arXiv (`arxiv-metadata-oai-snapshot`,
  5,22 GB), a nie na odpytywanie API. Powód: zrzut jest wersjonowany i daje ten sam wynik przy
  każdym uruchomieniu, natomiast API zwraca dane zmieniające się w czasie, co uniemożliwiłoby
  odtworzenie eksperymentu.
- **Zdefiniowanie reguły zakresu.** Pełny nadzbiór trzech kategorii docelowych to **195 149**
  unikalnych prac (`q-bio.NC` — 11 902, `cs.AI` — 172 726, `cs.NE` — 17 475). Jest to zbiór
  zdominowany przez ogólną sztuczną inteligencję i tematycznie zbyt szeroki dla czytelnika
  zakotwiczonego w neuronauce.
  Zastosowano regułę: **cała kategoria `q-bio.NC` jako kręgosłup + te prace z `cs.AI`/`cs.NE`,
  które są skrośnie zaklasyfikowane do `q-bio*` albo których tytuł/abstrakt pasuje do zestawu
  słów kluczowych z neuronauki i kognitywistyki.**
- **Budowa korpusu** skryptem `build_corpus.py`, zapis do `corpus.jsonl.gz`.
- **Wygenerowanie profili czytelników** skryptem `make_users.py`, zapis do `users.json`.
- **Kontrola liczebności i kompletności** — przeliczenie wszystkich raportowanych liczb
  bezpośrednio z pliku danych.

## 3. Uzyskane rezultaty

### Źródło danych

| | |
|---|---|
| Zbiór | `arxiv-metadata-oai-snapshot-001.json` — pełny zrzut metadanych arXiv |
| Rozmiar źródła | 5,22 GB |
| Data budowy korpusu | 16.07.2026 |
| Licencja | metadane arXiv udostępniane publicznie (CC0 dla zrzutu metadanych) |
| Plik wynikowy | `corpus.jsonl.gz` (16,5 MB skompresowane) |

### Liczba obserwacji

| poziom | liczba prac |
|---|---|
| pełny nadzbiór trzech kategorii | 195 149 |
| **korpus po zawężeniu tematycznym** | **36 314** |
| profile czytelników | 62 |

Rozkład kategorii docelowych w korpusie (**liczby trafień, nie sumują się do 36 314** — praca może
nieść więcej niż jedną kategorię):

| kategoria | liczba prac | udział w korpusie |
|---|---|---|
| `cs.AI` | 22 403 | 61,7% |
| `q-bio.NC` | 11 902 | 32,8% |
| `cs.NE` | 5 666 | 15,6% |

**To jest istotne dla opisu projektu.** Korpus nie jest zbiorem „z dziedziny neurobiologii" —
dominuje w nim sztuczna inteligencja. Poprawny opis brzmi: *przekrój arXiv obejmujący `q-bio.NC`,
`cs.AI` i `cs.NE`, w którym profile czytelników są zakotwiczone w `q-bio.NC`*.

W korpusie występują łącznie **153 różne kategorie arXiv**; mediana liczby kategorii na pracę
wynosi 2 (średnia 2,49, maksimum 9). Pięć najczęstszych poza kategoriami docelowymi:
`cs.LG` (11 381), `cs.CV` (6 923), `cs.CL` (4 789), `cs.HC` (1 949), `q-bio.QM` (1 763).

### Struktura zbioru

Format: **JSON Lines, skompresowany gzipem** — po jednym rekordzie na linię, co pozwala czytać plik
strumieniowo bez wczytywania całości do pamięci.

```json
{
  "id":         "2104.01234",              // identyfikator arXiv, klucz główny
  "title":      "…",                       // tytuł pracy
  "abstract":   "…",                       // abstrakt
  "categories": "q-bio.NC cs.AI cs.LG"     // kategorie rozdzielone spacją
}
```

Plik `users.json` — 62 profile syntetycznych czytelników:

```json
{
  "seed": 42, "profile_size": 8, "gt_cap": 60,
  "ground_truth_signal": "arXiv category co-membership (q-bio.NC AND a second field)",
  "users": [{
     "user_id":          "u001",
     "topic_rule":       "q-bio.NC AND physics.optics",   // reguła generująca zbiór relewantny
     "topic_label":      "Neurons & Cognition × physics.optics",
     "n_relevant_total": 30,                              // pełna liczność zbioru relewantnego
     "profile_ids":      ["…"],                           // 8 artykułów startowych
     "ground_truth_ids": ["…"],                           // klucz odpowiedzi — OBCIĘTY do gt_cap
     "n_ground_truth":   22
  }]
}
```

### Sposób pozyskania

1. Pobranie zrzutu metadanych arXiv (5,22 GB, format JSON).
2. Strumieniowe przejście przez zrzut z filtrem reguły zakresu — bez wczytywania całości do pamięci.
3. Zachowanie czterech pól na rekord (id, tytuł, abstrakt, kategorie); reszta metadanych odrzucona
   jako nieużywana przez żaden z porównywanych modeli.
4. Zapis do `corpus.jsonl.gz`.
5. Wygenerowanie profili czytelników: losowanie reguł `q-bio.NC AND drugie pole`, następnie
   wybór 8 artykułów startowych na profil przy ustalonym ziarnie `SEED = 42`.

### Kontrola kompletności

Przeliczenie bezpośrednio z pliku danych:

| kontrola | wynik |
|---|---|
| liczba rekordów | 36 314 |
| unikalnych identyfikatorów | 36 314 — **brak duplikatów klucza** |
| braki w polu `title` | 0 |
| braki w polu `abstract` | 0 |
| braki w polu `categories` | 0 |

Zbiór jest kompletny — nie ma braków danych w żadnym z czterech pól.

## 4. Problemy i sposoby ich rozwiązania

**Problem: rozmiar źródła.** Zrzut ma 5,22 GB i nie mieści się wygodnie w pamięci ani
w repozytorium.
**Rozwiązanie:** przetwarzanie strumieniowe linia po linii; do repozytorium trafia wyłącznie
zawężony korpus (16,5 MB). Skrypt budujący jest wersjonowany, więc korpus da się odtworzyć,
mając zrzut.

**Problem: nadzbiór jest tematycznie zbyt szeroki.** `cs.AI` liczy 172 726 prac i zdominowałby
bibliotekę, w której czytelnicy są zakotwiczeni w neuronauce.
**Rozwiązanie:** reguła zakresu z kręgosłupem `q-bio.NC` i filtrem skrośnym/słownikowym dla
`cs.AI`/`cs.NE`. Reguła jest zapisana w `corpus_meta.json`, a nie tylko w kodzie.

**Problem: rozbieżność liczb w pierwszej wersji raportu.** Podano `cs.AI = 15 120` przy realnych
172 726 w nadzbiorze i 22 403 w korpusie — różnica rzędu wielkości.
**Rozwiązanie:** wszystkie liczebności przeliczane skryptem z pliku danych i zapisywane do
`corpus_meta.json`. **W raportach nie umieszcza się liczb przepisywanych ręcznie** — to jest zasada
przyjęta na resztę projektu i główna lekcja z tego etapu.

**Problem: obcięcie klucza odpowiedzi.** Generator profili zapisuje `ground_truth_ids` obcięte do
`gt_cap = 60` pozycji, mimo że pole `n_relevant_total` przechowuje pełną liczność. Na tym etapie
uznano to za szczegół techniczny.
**Rozwiązanie:** **problem nie został tu rozwiązany** — jego konsekwencje ujawniły się dopiero
przy ewaluacji i są opisane w Raporcie 4 i Raporcie 7. Zapis pola `n_relevant_total` okazał się
kluczowy, bo umożliwił późniejszą rekonstrukcję pełnego klucza i jej weryfikację.

## 5. Plan działań na kolejny etap

1. Wczytanie korpusu i eksploracja: rozkłady długości tekstów, rozkład kategorii, liczba kategorii
   na pracę.
2. Kontrola jakości: duplikaty treści, teksty skrajnie krótkie i skrajnie długie.
3. Podstawowa analiza statystyczna zbioru — do Raportu 3.
