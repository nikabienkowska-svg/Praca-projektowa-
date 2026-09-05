# Raport 7 — Wyniki, metryki i analiza błędów
**Etap:** zajęcia 12–13

> **Uwaga do wersji.** Ten raport zastępuje wcześniejszą wersję, w której podano NDCG@10 = 0,160
> dla TF-IDF i 0,082 dla MiniLM. Tamte liczby powstały przy kluczu odpowiedzi obciętym do
> 60 pozycji (patrz Raport 4) i były zaniżone dla wszystkich silników. Wszystkie liczby poniżej
> pochodzą z plików `results_summary.csv`, `results_per_reader.csv`, `results_significance.csv`
> i `results_cost.csv` wygenerowanych przez pipeline.

---

## 1. Cel etapu

Ocena jakości modeli, wykresy wyników, analiza błędów oraz analiza jakości danych w kontekście
uzyskanych wyników. Efektem ma być wybór najlepszego modelu wraz z uzasadnieniem.

## 2. Wykonane działania

- Pełna ewaluacja ośmiu silników na 62 czytelnikach.
- Parowany test Wilcoxona na NDCG@10 per czytelnik, z korektą Holma i wielkością efektu.
- Pomiar kosztu budowy indeksu i obsługi zapytań.
- Analiza błędów: identyfikacja czytelników, u których silniki najmocniej się rozjeżdżają,
  oraz czytelników, u których zawodzą wszystkie.
- Sprawdzenie, czy wynik zależy od wielkości zbioru relewantnego.
- Porównanie zachowania silników na czubku rankingu (P@5) i głębiej (P@10).

## 3. Uzyskane rezultaty

### 3.1. Metryki — średnie po 62 czytelnikach

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

Wykresy: `fig_ranking.png` (ranking silników), `fig_rozklad.png` (rozkład per czytelnik).

**Wygrywa TF-IDF.** Najlepszy model semantyczny (SPECTER2-maxsim, 0,259) przegrywa z nim o 19%
względnie i przegrywa nawet z BM25.

### 3.2. Istotność statystyczna

Wilcoxon parowany na NDCG@10 per czytelnik, korekta Holma na rodzinę 8 porównań. Wielkość efektu
`r = Z/√n`: 0,1 mały, 0,3 średni, 0,5 duży.

| porównanie | mediana różnicy | p surowe | **p po Holmie** | r | wniosek |
|---|---|---|---|---|---|
| TF-IDF vs Popularity | +0,252 | <0,001 | **<0,001** | 0,71 | TF-IDF istotnie lepszy |
| BM25 vs Popularity | +0,187 | <0,001 | **<0,001** | 0,68 | BM25 istotnie lepszy |
| SPECTER2-maxsim vs SPECTER2-mean | +0,116 | 0,0002 | **0,001** | **0,50** | agregacja max-sim istotnie lepsza |
| TF-IDF vs BM25 | +0,071 | 0,0019 | **0,009** | 0,43 | TF-IDF istotnie lepszy |
| MiniLM-maxsim vs TF-IDF | −0,068 | 0,0046 | **0,018** | 0,37 | **TF-IDF istotnie lepszy** |
| SPECTER2-maxsim vs TF-IDF | −0,046 | 0,0101 | **0,030** | 0,35 | **TF-IDF istotnie lepszy** |
| MiniLM-maxsim vs MiniLM-mean | +0,044 | 0,085 | 0,170 | 0,23 | brak istotnej różnicy |
| SPECTER2-maxsim vs MiniLM-maxsim | 0,000 | 0,602 | 0,602 | 0,07 | **brak istotnej różnicy** |

Trzy odczyty, które są ważniejsze niż sam ranking:

1. **Oba modele semantyczne przegrywają z TF-IDF istotnie**, z efektem średniej wielkości. To nie
   jest różnica na poziomie szumu.
2. **Model dziedzinowy nie bije modelu ogólnego.** SPECTER2 vs MiniLM: mediana różnicy dokładnie
   0,000, p = 0,60. Mimo że SPECTER2 był trenowany na grafie cytowań prac naukowych **i** widzi
   100% abstraktu wobec 86,5% u MiniLM. Specjalizacja dziedzinowa nie przełożyła się na trafność
   w tym zadaniu.
3. **Sposób budowania profilu ma efekt większy niż wybór modelu.** SPECTER2-maxsim bije
   SPECTER2-mean z efektem `r = 0,50` — **największym w całym badaniu**. Uśrednienie ośmiu
   wektorów kosztuje więcej niż różnica między modelem ogólnym a dziedzinowym.

### 3.3. Koszt (H2)

| silnik | budowa indeksu | 62 zapytania |
|---|---|---|
| BM25 | 4,9 s | 0,36 s |
| TF-IDF | 33,2 s | 0,54 s |
| MiniLM | 1 833 s (31 min) | 0,73 s |
| SPECTER2 | 12 343 s (3 h 26 min) | 1,32 s |

Pomiar na CPU (2 rdzenie). **SPECTER2 buduje indeks 372 razy dłużej niż TF-IDF.** Na GPU (T4)
różnica spada do rzędu kilkunastu razy, ale nie znika. Czas obsługi zapytania jest we wszystkich
podejściach pomijalny — koszt semantyki jest jednorazowy i ulokowany w budowie indeksu.

### 3.4. Analiza błędów

Materiał pochodzi z porównania per czytelnik (`analiza_bledow.csv`), a nie z wymyślonych przykładów.

#### Gdzie SPECTER2 wygrywa z TF-IDF

| czytelnik | temat | \|GT\| | TF-IDF | SPECTER2-maxsim |
|---|---|---|---|---|
| u012 | Neurons & Cognition × Signal Processing | 445 | **0,000** | 0,315 |
| u022 | Neurons & Cognition × cond-mat.soft | 24 | **0,000** | 0,305 |
| u002 | Neurons & Cognition × math.IT | 165 | 0,284 | 0,564 |
| u026 | Neurons & Cognition × cs.NA | 25 | **0,000** | 0,217 |
| u010 | Neurons & Cognition × physics.hist-ph | 12 | 0,085 | 0,293 |

W trzech przypadkach **TF-IDF nie trafia ani razu w pierwszą dziesiątkę, a SPECTER2 trafia**.
Wzorzec jest czytelny: są to pola, w których pokrewieństwo tematyczne **nie przekłada się na
wspólne słownictwo** — przetwarzanie sygnałów, teoria informacji, materia miękka, analiza
numeryczna, historia fizyki. Praca o teorii informacji w neuronauce i praca o teorii informacji
w kodowaniu neuronalnym mogą nie dzielić prawie żadnego terminu, a dotyczyć tego samego. Model
leksykalny nie ma jak ich połączyć; model semantyczny ma.

#### Gdzie TF-IDF wygrywa z SPECTER2

| czytelnik | temat | \|GT\| | TF-IDF | SPECTER2-maxsim |
|---|---|---|---|---|
| u057 | Neurons & Cognition × Language & NLP | 264 | 0,495 | **0,000** |
| u046 | Neurons & Cognition × Neural & Evolutionary Computing | 1041 | 0,852 | 0,381 |
| u037 | Neurons & Cognition × Human-Computer Interaction | 331 | 0,690 | 0,269 |
| u059 | Neurons & Cognition × math.AP | 34 | 0,558 | 0,188 |
| u031 | Neurons & Cognition × stat.ME | 118 | 0,425 | 0,095 |

Tu wzorzec jest odwrotny i równie czytelny: **pola o silnym, charakterystycznym żargonie**.
`Language & NLP` niesie słowa `language model`, `token`, `corpus`; `Neural & Evolutionary
Computing` — `spiking`, `neuromorphic`, `SNN`; HCI — `user study`, `interface`, `participants`.
Dopasowanie po słowach kluczowych rozstrzyga o przynależności kategorialnej niemal bezbłędnie
(NDCG@10 = 0,852 u u046), a model semantyczny rozmywa ten sygnał, szukając podobieństwa znaczeń
tam, gdzie liczy się dokładne słowo.

**To jest empiryczne potwierdzenie ograniczenia, które zapisaliśmy przed pomiarem** (Raport 5):
klucz oparty na kategoriach arXiv strukturalnie sprzyja leksyce. Widać nie tylko *że* sprzyja,
ale i *gdzie*.

#### Czytelnicy, u których zawodzą wszystkie silniki

Czterech czytelników z 62 ma NDCG@10 = 0,000 we **wszystkich** silnikach treściowych:

| czytelnik | temat | \|GT\| |
|---|---|---|
| u009 | Neurons & Cognition × physics.app-ph | 15 |
| u017 | Neurons & Cognition × physics.comp-ph | 34 |
| u020 | Neurons & Cognition × stat.CO | 25 |
| u036 | Neurons & Cognition × math.NA | 32 |

Wspólna cecha: **bardzo małe zbiory relewantne (15–34 artykuły na 36 314)** w polach
metodologicznych, nie tematycznych. `stat.CO` (statystyka obliczeniowa) czy `math.NA` (analiza
numeryczna) to etykiety mówiące o *narzędziu*, a nie o *temacie* pracy — a narzędzie rzadko
zostawia ślad w abstrakcie. Żadna reprezentacja tekstu nie pomoże, bo sygnału nie ma w tekście.
To jest **ograniczenie klucza odpowiedzi, nie modeli**, i tak trzeba je opisać.

#### Liczba czytelników bez jednego trafienia w top-10

| silnik | czytelników z zerem |
|---|---|
| TF-IDF | 10 / 62 |
| MiniLM-maxsim | 10 / 62 |
| SPECTER2-maxsim | 10 / 62 |
| BM25 | 12 / 62 |
| MiniLM-mean | 17 / 62 |
| SPECTER2-mean | 30 / 62 |
| Popularity | 55 / 62 |
| Random | 57 / 62 |

**SPECTER2-mean zawodzi całkowicie u połowy czytelników** — to nie jest model gorszy o kilka
procent, tylko konfiguracja, która się rozpada. Ta sama reprezentacja z agregacją max-sim schodzi
do 10 zer, czyli poziomu TF-IDF. Uśrednianie ośmiu wektorów w przestrzeni anizotropowej daje
centroid, który nie odpowiada żadnemu z zainteresowań czytelnika — i to jest mierzalny efekt,
a nie hipoteza.

#### Zachowanie na czubku rankingu

| silnik | P@5 | P@10 | spadek |
|---|---|---|---|
| TF-IDF | 0,339 | 0,277 | 18,1% |
| **SPECTER2-maxsim** | **0,297** | 0,224 | **24,5%** |
| BM25 | 0,290 | 0,236 | 18,9% |
| MiniLM-maxsim | 0,271 | 0,231 | 14,9% |

SPECTER2-maxsim **bije BM25 na P@5** (0,297 vs 0,290) i jest drugi po TF-IDF, ale traci najszybciej
w głąb listy. Wniosek praktyczny: model semantyczny jest **precyzyjny na pierwszych pozycjach**
i słabnie dalej. W systemie, który pokazuje użytkownikowi pięć propozycji, ta różnica ma inne
znaczenie niż w rankingu na sto pozycji.

#### Odporność na wielkość zbioru relewantnego

Korelacja Spearmana między licznością `|GT|` a NDCG@10:

| silnik | rho | p |
|---|---|---|
| BM25 | +0,273 | 0,032 |
| TF-IDF | +0,243 | 0,057 |
| MiniLM-maxsim | +0,223 | 0,081 |
| **SPECTER2-maxsim** | **+0,080** | **0,534** |

Silniki leksykalne wypadają **tym lepiej, im większy zbiór relewantny** — przy 1 000 relewantnych
prac trudno nie trafić. SPECTER2 jako jedyny **nie wykazuje tej zależności**: jego wynik nie
zależy od tego, czy czytelnik ma 20 czy 1 000 relewantnych artykułów. Przy rzadkich, wąskich
zainteresowaniach — czyli w sytuacji, która w prawdziwym systemie rekomendacji jest najtrudniejsza
i najcenniejsza — jest to zaleta, której średnia po wszystkich czytelnikach nie pokazuje.

### 3.5. Analiza jakości danych w kontekście wyników

Trzy własności danych, które bezpośrednio ukształtowały wyniki:

1. **Klucz kategorialny** — potwierdzone empirycznie, że sprzyja leksyce (punkt 3.4). Gdyby
   trafność definiować przez wspólne cytowania, kolejność silników mogłaby się odwrócić.
2. **Nierównowaga zbiorów relewantnych 160:1** — wpływa na silniki leksykalne (dodatnia korelacja
   z `|GT|`), a nie wpływa na SPECTER2. Bez rozbicia wyniku na czytelników byłoby to niewidoczne.
3. **Kategorie metodologiczne** (`stat.CO`, `math.NA`, `physics.comp-ph`) — dla czterech czytelników
   klucz odpowiedzi nie ma odpowiednika w tekście abstraktu. To sufit, którego żaden model nie
   przebije.

### 3.6. Wybór najlepszego modelu i uzasadnienie

**Do wdrożenia w tym zadaniu: TF-IDF.**

| kryterium | uzasadnienie |
|---|---|
| trafność | najwyższa ze wszystkich ośmiu silników, przewaga istotna statystycznie |
| koszt | indeks w 33 s na CPU, 372× taniej niż SPECTER2 |
| interpretowalność | można pokazać użytkownikowi, które terminy zadecydowały o rekomendacji |
| wdrażalność | brak wymagań sprzętowych, brak zależności od modeli zewnętrznych |

**Zastrzeżenie, bez którego ten wybór byłby nadinterpretacją:** wybór jest optymalny **dla tego
zadania i tej definicji trafności**. Analiza błędów pokazuje, że oba podejścia wygrywają
u **rozłącznych grup czytelników**, a SPECTER2 jest jako jedyny odporny na wielkość zbioru
relewantnego. Naturalnym kierunkiem jest rozwiązanie hybrydowe — i to jest treść wniosków
w Raporcie 8.

## 4. Problemy i sposoby ich rozwiązania

**Problem: pierwsza seria wyników była nieważna** przez obcięty klucz odpowiedzi.
**Rozwiązanie:** rekonstrukcja pełnego klucza z asercją (Raport 4) i ponowne uruchomienie całej
ewaluacji. Wszystkie liczby w projekcie pochodzą z przebiegu po naprawie.

**Problem: sama różnica średnich nic nie dowodzi** przy 62 obserwacjach.
**Rozwiązanie:** test parowany na rozkładzie per czytelnik + korekta Holma na osiem porównań
+ wielkość efektu. Przy ośmiu porównaniach na tych samych danych prawdopodobieństwo, że
przynajmniej jedno wyjdzie fałszywie istotne, przekracza 30% — korekta to ryzyko usuwa.
W tym przebiegu żaden wynik nie zmienił statusu po korekcie, ale nie było to wiadome z góry.

**Problem: przegrana modelu semantycznego mogła wynikać z obciętego wejścia**, bo MiniLM widzi
86,5% tekstu.
**Rozwiązanie:** SPECTER2 obcina 0,1% abstraktów i przegrywa tak samo. Argument o uciętym wejściu
jest wykluczony pomiarem, a nie deklaracją.

**Problem: średnia ukrywa strukturę wyniku.** Po samym rankingu wyglądałoby to na „semantyka jest
gorsza".
**Rozwiązanie:** rozbicie wyniku na czytelników, korelacja z `|GT|`, porównanie P@5 z P@10 i lista
czytelników z zerem. Dopiero to pokazuje, że silniki są **komplementarne**, a nie po prostu lepszy
i gorszy.

**Problem: cztery zbiory relewantne są nieosiągalne dla jakiegokolwiek modelu tekstowego.**
**Rozwiązanie:** zidentyfikowanie ich i nazwanie przyczyny (kategorie metodologiczne, nie
tematyczne). Nie da się tego naprawić bez zmiany definicji trafności — więc trafia do ograniczeń
badania, a nie do listy usterek modelu.

## 5. Plan działań na kolejny etap

1. Formalna weryfikacja hipotez H1, H2, H3 na podstawie testów.
2. Interpretacja wyników w kontekście ograniczeń badania.
3. Propozycje ulepszeń — do Raportu 8.
