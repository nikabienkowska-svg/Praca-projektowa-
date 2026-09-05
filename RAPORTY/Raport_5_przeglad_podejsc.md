# Raport 5 — Przegląd i analiza podejść: klasyczne vs ML/AI
**Etap:** zajęcia 8–9

Raport odpowiada na siedem kryteriów porównania podanych przez prowadzącego w Planie zajęć.

---

## 1. Cel etapu

Systematyczne porównanie klasycznych metod rozwiązania problemu z metodami opartymi na uczeniu
maszynowym i sieciach neuronowych, wykonane **przed** implementacją, żeby wybór modeli był
uzasadniony, a nie przypadkowy.

## 2. Wykonane działania

- Przegląd rodzin metod rekomendacji i odrzucenie tych, których dane nie pozwalają zastosować.
- Zestawienie podejścia leksykalnego i semantycznego wg siedmiu kryteriów z Planu zajęć.
- Wybór konkretnych modeli do implementacji wraz z uzasadnieniem każdego wyboru.
- Zaprojektowanie protokołu ewaluacji zapewniającego, że porównanie jest uczciwe.

## 3. Uzyskane rezultaty

### 3.1. Rodziny metod i decyzja o zakresie

| rodzina | zasada działania | zastosowalność w projekcie |
|---|---|---|
| **Filtracja kolaboracyjna** (user-based, item-based, faktoryzacja macierzy) | „użytkownicy podobni do ciebie czytali też…" | **wykluczona** — wymaga macierzy interakcji użytkownik–pozycja, a w metadanych arXiv nie ma ani jednej interakcji |
| **Rekomendacja treściowa leksykalna** (TF-IDF, BM25) | dopasowanie na poziomie słów, wektory rzadkie | **wybrana** |
| **Rekomendacja treściowa semantyczna** (zanurzenia zdaniowe) | dopasowanie na poziomie znaczenia, wektory gęste | **wybrana** |
| **Metody grafowe** (sieć cytowań, PageRank) | struktura powiązań między pracami | **wykluczona** — zrzut metadanych nie zawiera krawędzi cytowań. Wchodzi pośrednio, przez SPECTER2, który był *trenowany* na grafie cytowań |
| **Podejścia hybrydowe** | łączenie sygnałów | poza zakresem czasowym projektu; wskazane we wnioskach jako kierunek rozwoju |

Wykluczenie filtracji kolaboracyjnej **nie jest ograniczeniem projektu, tylko warunkiem
brzegowym danych** i musi być tak nazwane. Problem zimnego startu — brak historii interakcji —
jest w naszym przypadku permanentny, a nie przejściowy.

### 3.2. Porównanie wg siedmiu kryteriów prowadzącego

#### Kryterium 1 — Wymagania dotyczące danych

| | leksykalne (TF-IDF, BM25) | semantyczne (MiniLM, SPECTER2) |
|---|---|---|
| minimalna liczba próbek | działa od pierwszego dokumentu; statystyka `idf` stabilizuje się przy setkach dokumentów | **zero** — model jest wytrenowany wcześniej, korpus służy tylko do zakodowania |
| wrażliwość na brak równowagi klas | niska — nie ma klas, jest ranking podobieństwa | niska, z tego samego powodu |
| konieczność anotacji | **żadna** | **żadna** przy inferencji; ogromna przy trenowaniu modelu (SPECTER2: miliony par cytowań) |
| jakość i czystość danych | wrażliwe — literówki i warianty odmiany to osobne cechy | odporniejsze — tokenizacja word-piece radzi sobie z wariantami |

**Wniosek:** żadne z podejść nie wymaga anotowanego zbioru treningowego, bo oba działają
bez nadzoru. Różnica jest w tym, **gdzie ulokowany jest koszt anotacji**: w podejściu semantycznym
został poniesiony przez twórców modelu i jest dla nas darmowy — ale też niekontrolowalny.

#### Kryterium 2 — Zakres preprocessingu

| | leksykalne | semantyczne |
|---|---|---|
| ekstrakcja cech | **ręczna** — decyzje o stop-słowach, `min_df`, `max_df`, n-gramach, `sublinear_tf` | **automatyczna** — reprezentacja jest wyuczona |
| złożoność przygotowania danych | wyższa: kilka parametrów, każdy wpływa na wynik | niższa: tekst wchodzi surowy |
| czas budowy pipeline'u | godziny (dobór parametrów) | minuty (wywołanie modelu) |

To jest **klasyczny kompromis inżynierii cech kontra uczenia reprezentacji** i najczystszy przykład
różnicy między dwoma podejściami w tym projekcie.

#### Kryterium 3 — Stopień udziału człowieka

| | leksykalne | semantyczne |
|---|---|---|
| inżynieria cech | konieczna | brak |
| liczba decyzji projektowych | wysoka: 5 parametrów wektoryzatora + 2 parametry BM25 (`k1`, `b`) | niska: wybór modelu i sposób agregacji profilu |
| wiedza dziedzinowa | pomocna przy doborze stop-słów i progów | pomocna przy wyborze modelu dziedzinowego |

**To jest źródło asymetrii, którą trzeba zaraportować.** TF-IDF w tym projekcie jest dostrojony,
oba modele semantyczne działają w konfiguracji domyślnej. Porównanie jest więc **na niekorzyść
modeli semantycznych** i wniosek musi to uwzględniać.

#### Kryterium 4 — Złożoność obliczeniowa

| | leksykalne | semantyczne |
|---|---|---|
| sprzęt | CPU wystarcza | GPU praktycznie konieczne |
| budowa indeksu (36 314 dokumentów) | BM25 ok. 5 s, TF-IDF ok. 30 s | minuty na GPU, **godziny na CPU** |
| obsługa zapytania | jedno mnożenie macierzy rzadkiej — poniżej sekundy dla 62 zapytań | mnożenie macierzy gęstej — również szybkie, bo indeks jest już policzony |
| pamięć indeksu | macierz rzadka, dziesiątki MB | 36 314 × 768 float32 ≈ 106 MB (SPECTER2) |
| działanie w czasie rzeczywistym | tak | tak przy gotowym indeksie; zakodowanie nowego dokumentu wymaga przebiegu modelu |

Koszt w podejściu semantycznym jest **jednorazowy i przesunięty na budowę indeksu**, nie na
zapytanie — to istotne rozróżnienie przy ocenie przydatności produkcyjnej.

#### Kryterium 5 — Koszt czasowy implementacji

| | leksykalne | semantyczne |
|---|---|---|
| czas implementacji | niski — kilkanaście linii z `scikit-learn`; BM25 wymaga implementacji macierzowej | niski dla MiniLM; **wyższy dla SPECTER2** — wymaga biblioteki `adapters` i ręcznego doładowania adaptera `proximity` |
| liczba iteracji eksperymentalnych | wysoka — każdy parametr trzeba sprawdzić | niska — nie ma czego stroić |
| łatwość debugowania | **wysoka** — można obejrzeć, które terminy zadecydowały o dopasowaniu | **niska** — 768 liczb bez interpretacji |

#### Kryterium 6 — Interpretowalność

| | leksykalne | semantyczne |
|---|---|---|
| przejrzystość decyzji | pełna — wkład każdego terminu w wynik jest wyliczalny | brak — podobieństwo kosinusowe wektorów bez znaczenia poszczególnych wymiarów |
| wyjaśnienie predykcji użytkownikowi | „polecono, bo obie prace mówią o *spiking neural networks*" | „polecono, bo wektory są blisko siebie" |

**Przewaga metod klasycznych jest tu jednoznaczna i niezależna od wyniku pomiaru trafności.**
W systemie rekomendacji literatury naukowej ma to wagę praktyczną: badacz, który rozumie, dlaczego
dostał daną propozycję, może skorygować zapytanie.

#### Kryterium 7 — Skalowalność

| | leksykalne | semantyczne |
|---|---|---|
| wzrost liczby dokumentów | słownik rośnie, macierz pozostaje rzadka — skalowanie dobre | wymiar wektora stały, koszt kodowania liniowy — skalowanie dobre, ale drogie |
| nowy dokument w indeksie | dopisanie wiersza; okresowo trzeba przeliczyć `idf` | jeden przebieg modelu |
| **transfer learning** | **niemożliwy** — brak modelu do przeniesienia | **naturalny** — to jest cała idea SPECTER2: wiedza z grafu cytowań przeniesiona na nasze zadanie |
| zmiana dziedziny korpusu | wymaga ponownego doboru parametrów | model dziedzinowy może przestać pasować, model ogólny działa dalej |

### 3.3. Podsumowanie porównania

| kryterium | wygrywa |
|---|---|
| 1. wymagania danych | remis |
| 2. zakres preprocessingu | **semantyczne** |
| 3. udział człowieka | **semantyczne** |
| 4. złożoność obliczeniowa | **klasyczne** |
| 5. koszt implementacji | **klasyczne** |
| 6. interpretowalność | **klasyczne** |
| 7. skalowalność | **semantyczne** (transfer learning) |

Podział przebiega czytelnie: **metody klasyczne wygrywają kosztem i przejrzystością, metody
semantyczne — brakiem inżynierii cech i zdolnością do transferu wiedzy.** O tym, czy przewaga
semantyki w trafności jest realna, rozstrzyga pomiar, a nie ta tabela — i to jest właśnie treść
hipotezy H1.

### 3.4. Wybrane modele i uzasadnienie

| silnik | rola | dlaczego akurat ten |
|---|---|---|
| **Random** | dolny punkt odniesienia | wartość, poniżej której wynik jest bezwartościowy |
| **Popularity** | punkt odniesienia niespersonalizowany | jeśli model spersonalizowany nie bije listy „to samo wszystkim", personalizacja nic nie wnosi |
| **TF-IDF** | klasyk leksykalny | metoda referencyjna dla rekomendacji treściowej |
| **BM25** | **mocny** klasyk leksykalny | Random i Popularity leżą zbyt nisko, żeby ich pobicie coś dowodziło; BM25 to standard wyszukiwania pełnotekstowego i właściwy rywal dla semantyki |
| **MiniLM** (`all-MiniLM-L6-v2`) | semantyczny **ogólny** | model powszechnie używany do zanurzeń zdaniowych, punkt odniesienia dla „semantyki z półki" |
| **SPECTER2** (`allenai/specter2_base` + adapter `proximity`) | semantyczny **dziedzinowy** | trenowany na grafie cytowań prac naukowych — czyli na dokładnie tej relacji, którą modelujemy. Bez niego wniosek dotyczyłby jednego modelu ogólnego, a brzmiałby jak teza o semantyce w ogóle |

Dodatkowo **dwie agregacje profilu** dla obu modeli semantycznych:

- **mean** — jeden uśredniony wektor z 8 artykułów startowych. W przestrzeni anizotropowej
  centroid ośmiu różnych prac może wylądować w punkcie nieodpowiadającym żadnej z nich.
- **max-sim** — dokument dostaje najwyższe podobieństwo do któregokolwiek artykułu startowego.
  Nie wymaga, żeby zainteresowania czytelnika były jednorodne.

Rozróżnienie jest konieczne, żeby odróżnić **słabość modelu od słabości sposobu budowania profilu** —
bez niego przegrana modelu semantycznego byłaby niediagnostyczna.

### 3.5. Protokół uczciwego porównania

Cztery warunki, przyjęte przed implementacją:

1. **Identyczne wejście** — każdy silnik dostaje ten sam ciąg `"tytuł. abstrakt"`. Żaden nie widzi
   kategorii.
2. **Identyczny klucz odpowiedzi** — oparty na metadanych kategorialnych, niezależny od wszystkich
   modeli.
3. **Identyczny protokół** — 8 artykułów startowych wykluczonych z rankingu, te same metryki, te
   same progi K.
4. **Ustalone ziarno losowe** (`SEED = 42`) w każdym elemencie zawierającym losowość.

## 4. Problemy i sposoby ich rozwiązania

**Problem: baseline'y są zbyt słabe.** Random i Popularity dają wyniki bliskie zeru, więc pobicie
ich nie dowodzi wartości metody.
**Rozwiązanie:** dodanie **BM25** jako mocnego punktu odniesienia. Teza „semantyka jest lepsza od
leksyki" wymaga pokonania najlepszej dostępnej leksyki, a nie najgorszej.

**Problem: jeden model semantyczny nie wystarcza do rozstrzygnięcia H1.** Przegrana MiniLM mogłaby
wynikać z tego, że jest to model ogólny, nietrenowany na tekstach naukowych.
**Rozwiązanie:** dodanie **SPECTER2** — modelu dziedzinowego. Dopiero para modeli pozwala oddzielić
„semantyka nie działa" od „ten konkretny model nie pasuje do dziedziny".

**Problem: agregacja profilu jest ukrytym parametrem.** Uśrednianie 8 wektorów to decyzja
projektowa, która może zaważyć na wyniku bardziej niż wybór modelu.
**Rozwiązanie:** obie agregacje uruchamiane równolegle i raportowane osobno; różnica między nimi
jest osobnym wynikiem.

**Problem: TF-IDF jest dostrojony, modele semantyczne nie.**
**Rozwiązanie:** **nie wyrównujemy warunków, tylko je raportujemy.** Dostrajanie modeli
semantycznych wykracza poza zakres czasowy projektu; asymetria trafia do ograniczeń i działa
na niekorzyść tezy o przewadze semantyki, co czyni ewentualną wygraną semantyki mocniejszą.

## 5. Plan działań na kolejny etap

1. Implementacja ośmiu silników w jednym pipelinie.
2. Implementacja metryk (Precision@K, Recall@K, NDCG@K) liczonych per czytelnik.
3. Pomiar czasu budowy indeksu i czasu obsługi zapytań (H2).
4. Diagnostyka: ile tekstu każdy model faktycznie widzi — do Raportu 6.
