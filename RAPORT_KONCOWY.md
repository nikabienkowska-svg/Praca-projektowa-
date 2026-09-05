# Porównanie skuteczności modeli rekomendacyjnych literatury naukowej
## Raport końcowy projektu

**Temat 3:** Analiza preferencji użytkowników — tworzenie systemu rekomendacji literatury naukowej
**Zespół:** Weronika, Natalia
**Metoda:** Problem-Based Learning

---

## Streszczenie

Projekt porównuje dwie rodziny treściowych systemów rekomendacji artykułów naukowych — leksykalną
(TF-IDF, BM25) i semantyczną (`all-MiniLM-L6-v2`, SPECTER2) — na bibliotece 36 314 artykułów
z arXiv i 62 profilach czytelników, przy trafności zdefiniowanej niezależnie od obu podejść.

**Hipoteza główna została odrzucona.** Dostrojone TF-IDF osiąga NDCG@10 = 0,321 i bije oba modele
semantyczne istotnie statystycznie (p po korekcie Holma odpowiednio 0,018 i 0,030, wielkość efektu
0,35–0,37). Odrzucenie jest mocne, bo wykluczono trzy alternatywne wyjaśnienia: nieznajomość
dziedziny (SPECTER2 był trenowany na grafie cytowań prac naukowych), obcięcie wejścia (SPECTER2
widzi 100% abstraktu) i złą konstrukcję profilu (przetestowano dwie agregacje).

Dwa ustalenia poboczne okazały się ciekawsze od samego rankingu. Po pierwsze, **model dziedzinowy
nie różni się od ogólnego** (mediana różnicy 0,000, p = 0,60) — specjalizacja pomaga tylko wtedy,
gdy jej dziedzina pokrywa się z definicją trafności w zadaniu. Po drugie, **sposób budowania
profilu użytkownika ma efekt większy niż wybór modelu**: agregacja `max-sim` bije `mean`
z wielkością efektu 0,50, podczas gdy różnica między modelem ogólnym a dziedzinowym to 0,07.

Analiza błędów pokazuje, że podejścia są **komplementarne, a nie konkurencyjne** — wygrywają
u rozłącznych grup czytelników, co czyni rozwiązanie hybrydowe naturalnym kierunkiem dalszej pracy.

---

## 1. Problem i cel

Liczba publikacji naukowych rośnie szybciej, niż badacz zdąży je przeglądać. System rekomendacji
ma na podstawie kilku prac, które czytelnik już zna, wskazać kolejne relewantne. Otwarte pozostaje,
jaka reprezentacja tekstu jest do tego potrzebna: czy wystarczy dopasowanie słów, czy konieczne
jest uchwycenie znaczenia.

**Pytanie badawcze:** Czy semantyczna reprezentacja tekstu daje trafniejsze rekomendacje artykułów
naukowych niż klasyczna reprezentacja leksykalna, i jakim kosztem obliczeniowym?

**Cel:** zbudowanie odtwarzalnego stanowiska porównawczego i ilościowa ocena, która rodzina metod
daje wyższą trafność przy jakim koszcie. Projekt nie buduje systemu produkcyjnego — buduje
stanowisko pomiarowe.

### Hipotezy

| | hipoteza | weryfikacja |
|---|---|---|
| **H1** | Model semantyczny jest trafniejszy niż leksykalny | Wilcoxon parowany na NDCG@10 per czytelnik |
| **H2** | Podejście leksykalne jest istotnie tańsze obliczeniowo | pomiar czasu budowy indeksu i zapytań |
| **H3** | Oba podejścia biją rekomendację niespersonalizowaną | porównanie z Random i Popularity |

H1 rozbito na trzy pytania rozstrzygane osobno, bo w wersji ogólnej jest niefalsyfikowalna —
przegrana jednego modelu nie dowodzi niczego o całej klasie metod:

1. Czy model semantyczny **ogólnego przeznaczenia** bije dostrojony model leksykalny?
2. Czy zmienia to model **dziedzinowy**, trenowany na cytowaniach prac naukowych?
3. Ile z różnicy wynika ze sposobu **budowania profilu**, a nie z samego modelu?

---

## 2. Metodologia

### 2.1. Uczciwa definicja trafności

To jest podstawowa decyzja metodologiczna projektu. Najbardziej naturalna definicja trafności —
„artykuł podobny do tych, które czytelnik zna" — jest **błędnym kołem**: klucz odpowiedzi
powstałby tą samą metodą, którą się ocenia.

Przyjęto definicję opartą na **metadanych niezależnych od wszystkich modeli**. Zbiór relewantny
czytelnika to artykuły spełniające regułę współczłonkostwa kategorii arXiv
(`q-bio.NC AND drugie pole`), pomniejszone o artykuły startowe. Kategorie przypisują autorzy prac
przy zgłoszeniu; żaden z porównywanych silników ich nie widzi — wszystkie dostają wyłącznie tytuł
i abstrakt.

### 2.2. Dane

Korpus zbudowano z publicznego zrzutu metadanych arXiv (5,22 GB). Nadzbiór trzech kategorii
docelowych liczy 195 149 prac i jest tematycznie zbyt szeroki, więc zastosowano regułę zakresu:
cała kategoria `q-bio.NC` jako kręgosłup plus prace z `cs.AI`/`cs.NE` zaklasyfikowane skrośnie
do `q-bio*` albo pasujące do zestawu słów kluczowych z neuronauki.

| | |
|---|---|
| artykułów w korpusie | **36 314** |
| profili czytelników | **62**, po 8 artykułów startowych |
| różnych kategorii arXiv | 153 |
| braki danych | **0** we wszystkich czterech polach |
| duplikaty treści | 2 (0,006%) |

Rozkład kategorii docelowych: `cs.AI` — 22 403 (61,7%), `q-bio.NC` — 11 902 (32,8%), `cs.NE` —
5 666 (15,6%). **Nie jest to korpus „neurobiologiczny", tylko przekrój arXiv, w którym profile
czytelników są zakotwiczone w `q-bio.NC`** — i tak trzeba go opisywać.

### 2.3. Przygotowanie danych i reprezentacja

Zbiór jest w całości tekstowy, więc klasyczne kroki czyszczenia (uzupełnianie braków, standaryzacja
zmiennych) nie mają zastosowania. Zasadą nadrzędną było, żeby **oba porównywane podejścia dostały
dokładnie ten sam tekst wejściowy** — każde czyszczenie korzystne dla jednej rodziny metod
unieważniłoby porównanie. Stąd brak lematyzacji, brak usuwania notacji LaTeX, a usuwanie stop-słów
tylko wewnątrz metod leksykalnych, gdzie jest ich elementem.

Macierz TF-IDF: 50 000 cech, rzadkość 99,76%, średnio 118,7 niezerowych terminów na dokument.
Wiersze normalizowane L2 — to jest odpowiednik standaryzacji dla danych tekstowych.

**Redukcja wymiarów została wykonana, zmierzona i odrzucona.** Truncated SVD (PCA nie działa na
macierzy rzadkiej bez zamiany jej na gęstą) do 150 składowych wyjaśnia zaledwie **10,6%** wariancji,
a krzywa nie ma kolana. Sygnał rozróżniający artykuły jest rozproszony po tysiącach rzadkich
terminów specjalistycznych — dokładnie tych, które rozstrzygają o przynależności tematycznej.
Rzutowanie na 150 wymiarów uśredniłoby ten sygnał, żeby zaoszczędzić pamięć, której nie brakuje.
Redukcja wymiarów wraca do projektu w postaci uczonej: modele semantyczne to redukcja 50 000
wymiarów leksykalnych do 384 albo 768 wymiarów wyuczonych na danych.

### 2.4. Krytyczna poprawka pomiaru

Plik `users.json` przechowuje klucz odpowiedzi **obcięty do 60 pozycji** (`gt_cap`), podczas gdy
zbiory relewantne sięgają 1 918 artykułów.

| | |
|---|---|
| czytelnicy z obciętym kluczem | **36 z 62** |
| mediana wielkości klucza | 60 → **91** |
| maksimum wielkości klucza | 60 → **1 918** |

Dla najbardziej dotkniętego czytelnika model trafiający w relewantną pracę dostawał punkt
z prawdopodobieństwem około 3%; w 97% przypadków był karany za trafną rekomendację. Pierwsza
seria wyników projektu (TF-IDF NDCG@10 = 0,160) była z tego powodu nieważna dla wszystkich
silników.

Pełny zbiór relewantny jest odtwarzany z reguły `topic_rule` na całym korpusie, a rekonstrukcja
**weryfikowana asercją** względem pola `n_relevant_total` — zgadza się dla wszystkich 62
czytelników. Druga asercja sprawdza, że żaden artykuł startowy nie trafił do klucza.

### 2.5. Porównywane silniki

| silnik | typ | reprezentacja |
|---|---|---|
| Random | punkt odniesienia | brak |
| Popularity | niespersonalizowany | częstość kategorii (proxy centralności tematycznej) |
| BM25 | leksykalny | worek słów, `k1 = 1,5`, `b = 0,75`, implementacja macierzowa |
| TF-IDF | leksykalny | wektor rzadki 50 000 cech, podobieństwo kosinusowe |
| MiniLM-mean / -maxsim | semantyczny ogólny | `all-MiniLM-L6-v2`, 384 wymiary, limit 256 word-pieces |
| SPECTER2-mean / -maxsim | semantyczny dziedzinowy | `allenai/specter2_base` + adapter `proximity`, 768 wymiarów, limit 512 |

Dwie agregacje profilu z 8 artykułów startowych: **mean** (jeden uśredniony wektor) i **max-sim**
(najwyższe podobieństwo do któregokolwiek artykułu startowego). Rozróżnienie było konieczne, żeby
odróżnić słabość modelu od słabości sposobu budowania profilu.

Wszystkie silniki mają identyczną sygnaturę wywołania i przechodzą przez jedną pętlę ewaluacyjną —
to nie wygoda, tylko zabezpieczenie przed nierównymi warunkami.

### 2.6. Metryki

Precision@K, Recall@K, NDCG@K dla K ∈ {5, 10}, liczone **osobno dla każdego czytelnika** i dopiero
potem uśredniane.

Metryką wiodącą jest **NDCG@10**. Powód jest w danych: liczność kluczy odpowiedzi waha się od
12 do 1 918 (stosunek 160:1), więc Recall@10 jest dla największych ograniczony od góry przez
ok. 0,005 — nawet ranking idealny go nie osiągnie, a wyniki czytelników przestają być porównywalne.
NDCG normalizuje przez `min(|GT|, K)`, więc ranking idealny daje 1 niezależnie od wielkości klucza.

### 2.7. Ile tekstu widzi każdy model

| model | limit | mediana długości | % ponad limit | **% widzianego tekstu** |
|---|---|---|---|---|
| MiniLM | 256 word-pieces | 266 | 54,6% | **86,5%** |
| SPECTER2 | 512 word-pieces | 249 | 0,1% | **100,0%** |
| TF-IDF / BM25 | brak | — | 0% | 100% |

Ta diagnostyka przesądza, który model jest właściwym testem H1. Gdyby przegrał tylko MiniLM, wynik
można by zbyć argumentem o uciętym wejściu. SPECTER2 obcina 0,1% dokumentów i jest od tego zarzutu
wolny.

---

## 3. Wyniki

### 3.1. Trafność

| silnik | P@5 | P@10 | R@10 | NDCG@5 | **NDCG@10** |
|---|---|---|---|---|---|
| Random | 0,010 | 0,010 | 0,000 | 0,012 | 0,011 |
| Popularity | 0,071 | 0,068 | 0,001 | 0,073 | 0,070 |
| SPECTER2-mean | 0,145 | 0,144 | 0,018 | 0,148 | 0,146 |
| MiniLM-mean | 0,203 | 0,195 | 0,024 | 0,202 | 0,197 |
| MiniLM-maxsim | 0,271 | 0,231 | 0,037 | 0,286 | 0,253 |
| SPECTER2-maxsim | 0,297 | 0,224 | 0,036 | 0,318 | 0,259 |
| BM25 | 0,290 | 0,236 | 0,034 | 0,313 | 0,267 |
| **TF-IDF** | **0,339** | **0,277** | **0,039** | **0,375** | **0,321** |

### 3.2. Istotność statystyczna

Wilcoxon parowany na NDCG@10 per czytelnik, korekta Holma na rodzinę 8 porównań, wielkość efektu
`r = Z/√n` (0,1 mały · 0,3 średni · 0,5 duży).

| porównanie | mediana różnicy | p po Holmie | r | wniosek |
|---|---|---|---|---|
| TF-IDF vs Popularity | +0,252 | <0,001 | 0,71 | TF-IDF istotnie lepszy |
| BM25 vs Popularity | +0,187 | <0,001 | 0,68 | BM25 istotnie lepszy |
| SPECTER2-maxsim vs SPECTER2-mean | +0,116 | 0,001 | **0,50** | max-sim istotnie lepszy |
| TF-IDF vs BM25 | +0,071 | 0,009 | 0,43 | TF-IDF istotnie lepszy |
| MiniLM-maxsim vs TF-IDF | −0,068 | 0,018 | 0,37 | **TF-IDF istotnie lepszy** |
| SPECTER2-maxsim vs TF-IDF | −0,046 | 0,030 | 0,35 | **TF-IDF istotnie lepszy** |
| MiniLM-maxsim vs MiniLM-mean | +0,044 | 0,170 | 0,23 | brak istotnej różnicy |
| SPECTER2-maxsim vs MiniLM-maxsim | 0,000 | 0,602 | 0,07 | **brak istotnej różnicy** |

### 3.3. Koszt

| silnik | budowa indeksu | 62 zapytania | stosunek do TF-IDF |
|---|---|---|---|
| BM25 | 4,9 s | 0,36 s | 0,15× |
| TF-IDF | 33,2 s | 0,54 s | 1× |
| MiniLM | 31 min | 0,73 s | 55× |
| SPECTER2 | 3 h 26 min | 1,32 s | **372×** |

Pomiar na 2 rdzeniach CPU. Koszt semantyki jest **jednorazowy i ulokowany w budowie indeksu** —
przy gotowym indeksie oba podejścia odpowiadają w ułamku sekundy.

### 3.4. Analiza błędów

Materiał pochodzi z porównania per czytelnik, nie z wymyślonych przykładów.

**Gdzie SPECTER2 wygrywa z TF-IDF:**

| czytelnik | temat | TF-IDF | SPECTER2-maxsim |
|---|---|---|---|
| u012 | × Signal Processing | **0,000** | 0,315 |
| u022 | × cond-mat.soft | **0,000** | 0,305 |
| u002 | × math.IT | 0,284 | 0,564 |
| u026 | × cs.NA | **0,000** | 0,217 |

Wzorzec: pola, w których **pokrewieństwo tematyczne nie przekłada się na wspólne słownictwo** —
przetwarzanie sygnałów, teoria informacji, materia miękka, analiza numeryczna. W trzech
przypadkach TF-IDF nie trafia ani razu w pierwszą dziesiątkę, a SPECTER2 trafia.

**Gdzie TF-IDF wygrywa z SPECTER2:**

| czytelnik | temat | TF-IDF | SPECTER2-maxsim |
|---|---|---|---|
| u057 | × Language & NLP | 0,495 | **0,000** |
| u046 | × Neural & Evolutionary Computing | 0,852 | 0,381 |
| u037 | × Human-Computer Interaction | 0,690 | 0,269 |

Wzorzec odwrotny: **pola o silnym, charakterystycznym żargonie** (`language model`, `spiking`,
`neuromorphic`, `user study`). Dopasowanie po słowach rozstrzyga niemal bezbłędnie, a model
semantyczny rozmywa ten sygnał.

**Czytelnicy nieosiągalni dla żadnego modelu.** Czterech czytelników ma NDCG@10 = 0 we wszystkich
silnikach treściowych: `physics.app-ph`, `physics.comp-ph`, `stat.CO`, `math.NA` — kategorie
mówiące o *narzędziu*, a nie o *temacie* pracy. Narzędzie rzadko zostawia ślad w abstrakcie.
To ograniczenie klucza odpowiedzi, nie modeli.

**Całkowite porażki per silnik** (zero trafień w top-10):

| silnik | czytelników z zerem |
|---|---|
| TF-IDF · MiniLM-maxsim · SPECTER2-maxsim | 10 / 62 |
| BM25 | 12 / 62 |
| MiniLM-mean | 17 / 62 |
| **SPECTER2-mean** | **30 / 62** |

**Odporność na wielkość zbioru relewantnego** (korelacja Spearmana `|GT|` z NDCG@10):

| silnik | rho | p |
|---|---|---|
| BM25 | +0,273 | 0,032 |
| TF-IDF | +0,243 | 0,057 |
| MiniLM-maxsim | +0,223 | 0,081 |
| **SPECTER2-maxsim** | **+0,080** | **0,534** |

Silniki leksykalne wypadają tym lepiej, im większy zbiór relewantny. SPECTER2 jako jedyny nie
wykazuje tej zależności — przy rzadkich, wąskich zainteresowaniach zachowuje się lepiej, niż
wynikałoby ze średniej.

---

## 4. Weryfikacja hipotez

### H1 — odrzucona

Oba modele semantyczne przegrywają z dostrojonym TF-IDF istotnie statystycznie, z efektem średniej
wielkości. Odrzucenie jest mocne, bo wykluczono trzy alternatywne wyjaśnienia: nieznajomość
dziedziny, obcięcie wejścia i złą konstrukcję profilu.

**Pytanie 1 — czy model ogólny bije leksykę?** Nie: 0,253 vs 0,321, p = 0,018.

**Pytanie 2 — czy zmienia to model dziedzinowy?** Nie, i to jest najbardziej zaskakujący wynik
projektu. SPECTER2-maxsim (0,259) nie różni się od MiniLM-maxsim (0,253): mediana różnicy
**dokładnie 0,000**, p = 0,60. Interpretacja: SPECTER2 jest optymalizowany pod bliskość w grafie
cytowań, a my mierzymy współczłonkostwo kategorii — to dwie różne relacje. **Model dziedzinowy
pomaga tylko wtedy, gdy jego dziedzina zgadza się z definicją trafności w zadaniu.**

**Pytanie 3 — ile z różnicy to sposób budowania profilu?** Bardzo dużo. `max-sim` bije `mean`
z efektem `r = 0,50` — największym w całym badaniu, wobec `r = 0,07` dla różnicy między modelami.
SPECTER2-mean zawodzi całkowicie u 30 z 62 czytelników; ta sama reprezentacja z `max-sim` — u 10,
czyli tyle samo co TF-IDF.

### H2 — potwierdzona

SPECTER2 buduje indeks **372× dłużej** niż TF-IDF. Różnica nie znika na GPU, a sam wymóg
posiadania GPU jest kosztem. To jedyna hipoteza bez sporu o interpretację.

### H3 — potwierdzona

TF-IDF i BM25 biją Popularity z efektem dużym (`r` = 0,71 i 0,68, p < 0,001). Personalizacja wnosi
realną wartość. Zastrzeżenie: „Popularity" nie jest tu popularnością w sensie systemów
rekomendacyjnych, bo w danych nie ma interakcji — to proxy centralności tematycznej.

---

## 5. Ograniczenia

**Osłabiają wniosek o przewadze leksyki:**

1. **Klucz kategorialny strukturalnie sprzyja modelom leksykalnym** — kategorie arXiv korelują
   z żargonem. Potwierdzone empirycznie w analizie błędów.
2. **Warunki nie są symetryczne** — TF-IDF jest dostrojony, oba modele semantyczne działają bez
   dostrajania.
3. **Cztery zbiory relewantne są nieosiągalne dla jakiegokolwiek modelu tekstowego** — oparte na
   kategoriach metodologicznych.

**Wzmacniają wniosek:**

4. MiniLM widzi 86,5% tekstu, **SPECTER2 — 100%**; obcięcie wejścia wykluczone jako przyczyna.
5. Przetestowano **dwa modele i dwie agregacje** — przegrana nie jest artefaktem jednej konfiguracji.

**Ograniczają zakres wniosków w ogóle:**

6. Czytelnicy są **syntetyczni** — w danych nie ma ani jednej rzeczywistej interakcji użytkownika.
7. **Brak filtracji kolaboracyjnej** — nie z wyboru, tylko dlatego, że metadane arXiv nie zawierają
   interakcji.
8. Jedna dziedzina, jeden korpus.

---

## 6. Wnioski

1. **Dla zadania rekomendacji artykułów naukowych z trafnością zdefiniowaną kategorialnie
   dostrojone TF-IDF jest rozwiązaniem najlepszym** — najwyższa trafność, koszt 372× niższy,
   pełna interpretowalność. H1 odrzucona, H2 i H3 potwierdzone.
2. **Specjalizacja dziedzinowa modelu nie jest sama w sobie zaletą.** Liczy się zgodność dziedziny
   modelu z definicją trafności w zadaniu.
3. **Sposób budowania profilu użytkownika okazał się ważniejszy niż wybór modelu** (`r = 0,50`
   wobec `r = 0,07`). To najbardziej przenośny wniosek praktyczny z całego projektu.
4. **Metody są komplementarne, nie konkurencyjne** — wygrywają u rozłącznych grup czytelników.
5. **Najważniejsza lekcja dotyczy nie modeli, lecz pomiaru.** Obcięcie klucza odpowiedzi zaniżało
   wyniki wszystkich silników o połowę i unieważniło pierwszą serię pomiarów. Błąd był widoczny
   w pliku danych od początku. Kontrola poprawności danych musi poprzedzać pomiar — i żadna liczba
   w raporcie nie powinna powstać inaczej niż przez wygenerowanie skryptem.

**Czego z tych wyników nie wolno wywnioskować:** że modele semantyczne są gorsze w rekomendacji
literatury naukowej. Poprawny wniosek jest zawężony do definicji trafności użytej w tym badaniu —
a zawężenie ma uzasadnienie empiryczne, nie tylko ostrożnościowe.

---

## 7. Propozycje dalszej pracy

1. **Hybryda leksykalno-semantyczna** — fuzja rang (Reciprocal Rank Fusion) z rankingów TF-IDF
   i SPECTER2-maxsim. Nie wymaga trenowania, mierzy się tym samym protokołem, a największy zysk
   daje tam, gdzie TF-IDF ma zero.
2. **Rezygnacja z agregacji `mean`** w każdym przyszłym systemie; zamiast niej klasteryzacja
   zainteresowań czytelnika (kilka centroidów zamiast jednego).
3. **Drugi klucz odpowiedzi oparty na cytowaniach** — jedyne ulepszenie, które może odwrócić
   wniosek H1, i dlatego najważniejsze.
4. **Dostrojenie modeli semantycznych**, żeby wyrównać asymetrię warunków.
5. **Weryfikacja na rzeczywistych czytelnikach.**
6. **Rozszerzenie o sygnał grafowy** jako trzecią rodzinę metod.

---

## 8. Odtwarzalność

Cały pipeline jest odtwarzalny i uruchamialny na dwa sposoby: notebookiem w Google Colab
(ok. 6 minut na GPU T4) albo skryptem `run_pipeline.py` bez notebooka i bez internetu.
Ziarno losowe jest ustalone (`SEED = 42`), zanurzenia buforowane, a wszystkie liczby w raportach
pochodzą z wygenerowanych plików CSV — żadna nie jest przepisana ręcznie.

Leksykalna część pipeline'u została uruchomiona niezależnie, w osobnym środowisku, na tych samych
danych. Wyniki zgadzają się co do czwartego miejsca po przecinku.

| plik | zawartość |
|---|---|
| `results_summary.csv` | średnie metryki per silnik |
| `results_per_reader.csv` | metryki per czytelnik (496 wierszy) |
| `results_significance.csv` | testy Wilcoxona z korektą Holma |
| `results_cost.csv` | czasy budowy indeksu i zapytań |
| `results_truncation.csv` | ile tekstu widzi każdy model |
| `analiza_bledow.csv` | porównanie per czytelnik do analizy błędów |
| `eda_report.json` | pełna eksploracja i kontrola jakości danych |
| `fig_*.png` | wykresy |
