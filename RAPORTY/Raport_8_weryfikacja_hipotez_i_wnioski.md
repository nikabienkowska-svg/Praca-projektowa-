# Raport 8 — Weryfikacja hipotez, ograniczenia i wnioski
**Etap:** zajęcia 14

---

## 1. Cel etapu

Weryfikacja postawionych hipotez, interpretacja wyników, wskazanie ograniczeń badania oraz
propozycje ulepszeń. Efektem mają być sformułowane wnioski końcowe projektu.

## 2. Wykonane działania

- Konfrontacja każdej hipotezy z wynikiem testu, a nie z różnicą średnich.
- Rozstrzygnięcie trzech pytań szczegółowych, na które rozbito H1.
- Zebranie ograniczeń badania i określenie, które z nich osłabiają, a które wzmacniają wnioski.
- Sformułowanie propozycji ulepszeń wynikających z analizy błędów, a nie z ogólnych zaleceń.

## 3. Uzyskane rezultaty

### 3.1. Hipoteza H1 — trafność

> **H1:** Model semantyczny generuje trafniejsze rekomendacje niż model leksykalny.

**H1 zostaje odrzucona.** Oba modele semantyczne przegrywają z dostrojonym TF-IDF istotnie
statystycznie:

| porównanie | mediana różnicy | p po Holmie | r |
|---|---|---|---|
| MiniLM-maxsim vs TF-IDF | −0,068 | 0,018 | 0,37 |
| SPECTER2-maxsim vs TF-IDF | −0,046 | 0,030 | 0,35 |

Odrzucenie jest mocne, bo **wykluczono trzy alternatywne wyjaśnienia** przegranej:

- *„Model semantyczny nie znał dziedziny"* — SPECTER2 był trenowany na grafie cytowań prac
  naukowych i przegrywa tak samo.
- *„Model nie widział całego abstraktu"* — SPECTER2 obcina 0,1% dokumentów wobec 54,6% u MiniLM
  i przegrywa tak samo.
- *„Profil był źle zbudowany"* — obie agregacje przetestowano osobno; przegrywa również lepsza
  z nich.

#### Odpowiedzi na trzy pytania szczegółowe

**Pytanie 1: czy model semantyczny ogólnego przeznaczenia bije dostrojony model leksykalny?**
**Nie.** MiniLM-maxsim 0,253 wobec TF-IDF 0,321; p = 0,018, efekt średni.

**Pytanie 2: czy zmienia to model dziedzinowy?**
**Nie — i to jest najbardziej zaskakujący wynik projektu.** SPECTER2-maxsim (0,259) nie różni się
od MiniLM-maxsim (0,253) w sposób istotny: mediana różnicy **dokładnie 0,000**, p = 0,60,
r = 0,07. Model trenowany na milionach par cytowań prac naukowych, widzący 100% abstraktu, nie
daje przewagi nad ogólnym modelem zdaniowym widzącym 86,5% tekstu.

Interpretacja: SPECTER2 jest optymalizowany pod **bliskość w grafie cytowań** — dwie prace są
podobne, jeśli jedna cytuje drugą albo mają wspólne cytowania. My mierzymy **współczłonkostwo
kategorii arXiv**. To są dwie różne relacje. Specjalizacja modelu jest realna, tylko wycelowana
w co innego niż nasz klucz odpowiedzi. Wniosek ogólniejszy: **model dziedzinowy pomaga tylko
wtedy, gdy jego dziedzina zgadza się z definicją trafności w zadaniu** — sama „naukowość" korpusu
nie wystarcza.

**Pytanie 3: ile z różnicy wynika ze sposobu budowania profilu?**
**Bardzo dużo — więcej niż z wyboru modelu.** SPECTER2-maxsim bije SPECTER2-mean o 0,116 mediany
różnicy przy `r = 0,50`, **największym efekcie w całym badaniu**. Dla porównania: różnica między
modelem ogólnym a dziedzinowym to `r = 0,07`.

Widać to najostrzej w liczbie całkowitych porażek: SPECTER2-**mean** nie trafia ani razu w top-10
u **30 z 62 czytelników**; ta sama reprezentacja z agregacją **max-sim** — u 10, czyli tyle samo co
TF-IDF. Uśredniony wektor ośmiu prac ląduje w punkcie, który nie odpowiada żadnemu z zainteresowań
czytelnika. **Decyzja projektowa, którą łatwo uznać za szczegół implementacyjny, okazała się
ważniejsza niż wybór modelu** — i to jest ustalenie, którego nie byłoby bez zaplanowania obu
wariantów przed pomiarem.

### 3.2. Hipoteza H2 — koszt

> **H2:** Podejście leksykalne jest istotnie tańsze obliczeniowo.

**H2 zostaje potwierdzona, bez zastrzeżeń.**

| silnik | budowa indeksu | stosunek do TF-IDF |
|---|---|---|
| BM25 | 4,9 s | 0,15× |
| TF-IDF | 33,2 s | 1× |
| MiniLM | 31 min | 55× |
| SPECTER2 | 3 h 26 min | **372×** |

Pomiar na 2 rdzeniach CPU. Na GPU różnica maleje do rzędu kilkunastu razy, ale nie znika, a sam
wymóg posiadania GPU jest kosztem. Czas obsługi zapytania jest we wszystkich podejściach poniżej
1,5 s dla 62 zapytań — **koszt semantyki jest jednorazowy i ulokowany w budowie indeksu**, nie
w obsłudze użytkownika. To rozróżnienie ma znaczenie praktyczne: system semantyczny jest drogi
do zbudowania i tani w utrzymaniu, dopóki korpus się nie zmienia.

### 3.3. Hipoteza H3 — przewaga nad rekomendacją niespersonalizowaną

> **H3:** Oba podejścia istotnie przewyższają rekomendację niespersonalizowaną.

**H3 zostaje potwierdzona.** TF-IDF vs Popularity: mediana różnicy +0,252, p < 0,001, `r = 0,71`
(efekt duży). BM25 vs Popularity: +0,187, p < 0,001, `r = 0,68`. Personalizacja wnosi realną
wartość — Popularity osiąga 0,070 NDCG@10 i nie trafia ani razu u 55 z 62 czytelników.

**Zastrzeżenie do nazwy.** „Popularity" nie jest tu popularnością w sensie systemów
rekomendacyjnych. W danych nie ma żadnych interakcji użytkowników, więc jest to ranking po
częstości kategorii, czyli **proxy centralności tematycznej**. H3 należy więc czytać jako
„personalizacja bije rekomendowanie wszystkim tego, co w korpusie najbardziej typowe".

### 3.4. Interpretacja — czego ten wynik nie znaczy

Wniosek, który obroni się przed każdym zarzutem, brzmi:

> **Przy trafności zdefiniowanej przez współczłonkostwo kategorii arXiv dostrojone podejście
> leksykalne wystarcza i jest tańsze o dwa rzędy wielkości.**

Wniosek, którego **nie wolno** wyciągnąć:

> ~~Modele semantyczne są gorsze od TF-IDF w rekomendacji literatury naukowej.~~

Powód jest w danych, nie w ostrożności. Analiza błędów (Raport 7) pokazuje, że **oba podejścia
wygrywają u rozłącznych grup czytelników**:

- **SPECTER2 wygrywa** tam, gdzie pokrewieństwo tematyczne nie przekłada się na wspólne
  słownictwo: przetwarzanie sygnałów, teoria informacji, materia miękka, analiza numeryczna.
  U trzech takich czytelników TF-IDF nie trafia **ani razu**, a SPECTER2 osiąga NDCG@10 od 0,217 do 0,315.
- **TF-IDF wygrywa** tam, gdzie pole ma silny, charakterystyczny żargon: NLP, obliczenia
  neuronowe i ewolucyjne, HCI. Tam dopasowanie po słowach kluczowych rozstrzyga niemal bezbłędnie
  (NDCG@10 = 0,852 u jednego z czytelników).

Ponieważ klucz odpowiedzi jest kategorialny, a kategorie arXiv silnie korelują z żargonem,
**w tym zadaniu jest więcej czytelników drugiego typu**. To przesądza o średniej — i o wyniku H1.

Dodatkowo SPECTER2 jest **jedynym silnikiem, którego wynik nie zależy od wielkości zbioru
relewantnego** (Spearman rho = 0,08 przy p = 0,53, wobec 0,24–0,27 dla silników leksykalnych)
oraz **drugim najlepszym na P@5** (0,297, przed BM25). Przy rzadkich, wąskich zainteresowaniach
i przy krótkiej liście rekomendacji — czyli w sytuacji, która w rzeczywistym systemie jest
najtrudniejsza — zachowuje się lepiej, niż wynikałoby ze średniej.

### 3.5. Ograniczenia badania

**Osłabiają wniosek o przewadze leksyki:**

1. **Klucz kategorialny strukturalnie sprzyja modelom leksykalnym.** Kategorie arXiv korelują
   z żargonem, więc wykrycie reguły `q-bio.NC AND physics.optics` jest w dużej mierze zadaniem
   dopasowania słów. Potwierdzone empirycznie w analizie błędów.
2. **Warunki nie są symetryczne.** TF-IDF jest dostrojony (`min_df`, `max_df`, bigramy,
   `sublinear_tf`, 50 tys. cech), oba modele semantyczne działają bez dostrajania.
3. **Cztery zbiory relewantne są nieosiągalne dla jakiegokolwiek modelu tekstowego** — oparte na
   kategoriach metodologicznych (`stat.CO`, `math.NA`, `physics.comp-ph`, `physics.app-ph`),
   które nie zostawiają śladu w abstrakcie.

**Wzmacniają wniosek:**

4. **MiniLM widzi 86,5% tekstu, SPECTER2 — 100%.** Obcięcie wejścia zostało wykluczone jako
   przyczyna przegranej.
5. **Przetestowano dwa modele semantyczne i dwie agregacje profilu.** Przegrana nie jest artefaktem
   jednej konfiguracji.

**Ograniczają zakres wniosków w ogóle:**

6. **Czytelnicy są syntetyczni.** W danych nie ma ani jednej rzeczywistej interakcji użytkownika,
   a kategoria to zgrubne przybliżenie preferencji.
7. **Brak filtracji kolaboracyjnej.** Nie jest to wybór metodologiczny, tylko warunek brzegowy
   danych — metadane arXiv nie zawierają interakcji.
8. **Jedna dziedzina, jeden korpus.** Wyniki dotyczą przekroju `q-bio.NC` + `cs.AI` + `cs.NE`
   i nie muszą przenosić się na inne pola.

### 3.6. Propozycje ulepszeń

Uporządkowane od najlepiej uzasadnionych wynikami do najbardziej spekulacyjnych.

1. **Hybryda leksykalno-semantyczna.** Uzasadnienie wprost z analizy błędów: silniki wygrywają
   u rozłącznych grup czytelników. Najprostsza realizacja to fuzja rang (Reciprocal Rank Fusion)
   z rankingów TF-IDF i SPECTER2-maxsim — nie wymaga trenowania i można ją zmierzyć tym samym
   protokołem. Oczekiwany zysk jest największy tam, gdzie TF-IDF ma zero.
2. **Rezygnacja z agregacji `mean` w każdym przyszłym systemie.** Efekt `r = 0,50` i 30 z 62
   całkowitych porażek to wystarczający dowód. Jeżeli profil ma być jednym wektorem, należy
   sprawdzić klasteryzację zainteresowań (kilka centroidów zamiast jednego), a nie uśrednianie.
3. **Drugi klucz odpowiedzi oparty na cytowaniach.** Cała przewaga leksyki może być artefaktem
   definicji trafności. Zbudowanie równoległego klucza z grafu cytowań (np. z zasobu S2ORC)
   i powtórzenie pomiaru **rozstrzygnęłoby to definitywnie** — i jest to jedyne ulepszenie, które
   może odwrócić wniosek H1.
4. **Dostrojenie modeli semantycznych** — choćby przez dobór progu długości wejścia i sposobu
   agregacji tokenów — żeby wyrównać asymetrię warunków z ograniczenia 2.
5. **Weryfikacja na rzeczywistych czytelnikach.** Nawet niewielki zbiór realnych historii
   czytelniczych pozwoliłby sprawdzić, czy syntetyczne profile nie zniekształcają obrazu.
6. **Rozszerzenie o sygnał grafowy** (współcytowania, bibliographic coupling) jako trzecią rodzinę
   metod, obok leksykalnej i semantycznej.

### 3.7. Wnioski końcowe

1. **Dla zadania rekomendacji artykułów naukowych z trafnością zdefiniowaną kategorialnie
   dostrojone TF-IDF jest rozwiązaniem najlepszym** — najwyższa trafność (NDCG@10 = 0,321),
   koszt 372× niższy niż model dziedzinowy, pełna interpretowalność. H1 odrzucona, H2 i H3
   potwierdzone.
2. **Specjalizacja dziedzinowa modelu nie jest sama w sobie zaletą.** SPECTER2 nie różni się
   od modelu ogólnego (p = 0,60), bo jego dziedzina — bliskość w grafie cytowań — nie pokrywa się
   z definicją trafności w tym zadaniu.
3. **Sposób budowania profilu użytkownika okazał się ważniejszy niż wybór modelu** (`r = 0,50`
   wobec `r = 0,07`). To najbardziej przenośny wniosek praktyczny z całego projektu.
4. **Metody są komplementarne, nie konkurencyjne.** Wygrywają u rozłącznych grup czytelników,
   co czyni hybrydę naturalnym kierunkiem dalszej pracy.
5. **Najważniejsza lekcja metodologiczna dotyczy nie modeli, lecz pomiaru.** Obcięcie klucza
   odpowiedzi do 60 pozycji zaniżało wyniki wszystkich silników o połowę i unieważniło pierwszą
   serię pomiarów. Błąd był widoczny w pliku danych od początku. **Kontrola poprawności danych
   musi poprzedzać pomiar, a nie po nim następować** — i żadna liczba w raporcie nie powinna
   powstać inaczej niż przez wygenerowanie skryptem.

## 4. Problemy i sposoby ich rozwiązania

**Problem: pokusa opisania wyniku jako „semantyka przegrała".** Byłby to wniosek zbyt szeroki
w stosunku do dowodu.
**Rozwiązanie:** rozbicie wyniku na czytelników i pokazanie, gdzie każde podejście wygrywa.
Wniosek zawężony do „dla tej definicji trafności", z empirycznym uzasadnieniem zawężenia.

**Problem: hipoteza główna okazała się fałszywa.** Naturalną reakcją jest szukanie konfiguracji,
w której wyjdzie inaczej.
**Rozwiązanie:** wszystkie warianty zaplanowano **przed** pomiarem (dwa modele × dwie agregacje)
i zaraportowano komplet. Odrzucenie hipotezy jest wynikiem, a nie porażką — pod warunkiem, że
protokół nie był dobierany po fakcie.

**Problem: osiem porównań na tych samych danych zawyża ryzyko fałszywego odkrycia.**
**Rozwiązanie:** korekta Holma i raportowanie wielkości efektu obok p-value. Przy ośmiu
porównaniach prawdopodobieństwo przynajmniej jednego fałszywie istotnego wyniku przekracza 30%.
W tym przebiegu żaden wynik nie zmienił statusu po korekcie — dwa porównania (MiniLM max-sim vs
mean oraz SPECTER2 vs MiniLM) były nieistotne już przed nią i tak zostały opisane, jako tendencja
albo brak różnicy, a nie fakt.

## 5. Plan działań na kolejny etap

1. Scalenie raportów etapowych w raport końcowy.
2. Przygotowanie prezentacji z wykresami z pipeline'u.
3. Przygotowanie demonstracji działania systemu (interfejs Gradio).
4. Samoocena i ocena koleżanki.
