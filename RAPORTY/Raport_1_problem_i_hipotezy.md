# Raport 1 — Zdefiniowanie problemu i hipotez badawczych
**Etap:** zajęcia 1–2 · **Temat 3:** Analiza preferencji użytkowników — system rekomendacji literatury naukowej
**Zespół:** Weronika Bieńkowska, Natalia

---

## 1. Cel etapu

Wybór tematu, sformułowanie pytania badawczego i hipotez, określenie zakresu analizy oraz podział
ról w zespole. Efektem ma być zatwierdzony temat i jasno postawione hipotezy, które da się
zweryfikować pomiarem, a nie opinią.

## 2. Wykonane działania

- Wybór tematu 3 z listy prowadzącego: **tworzenie systemu rekomendacji literatury naukowej**.
- Zawężenie problemu ogólnego („analiza preferencji użytkowników") do wersji rozstrzygalnej
  eksperymentalnie: **porównanie skuteczności dwóch rodzin metod rekomendacji treściowej** —
  leksykalnej i semantycznej — na jednej bibliotece i jednym protokole ewaluacji.
- Ustalenie, że projekt nie buduje systemu produkcyjnego, lecz **stanowisko pomiarowe**: kilka
  silników rekomendacji porównywanych na identycznych danych, z identyczną definicją trafności.
- Przegląd dostępnych źródeł danych pod kątem tego, czy da się z nich zbudować obiektywny klucz
  odpowiedzi (patrz punkt 4).
- Podział ról w zespole.

## 3. Uzyskane rezultaty

### Problem badawczy

Czytelnik literatury naukowej ma ograniczony czas, a liczba publikacji w jego dziedzinie rośnie
szybciej, niż jest w stanie je przeglądać. System rekomendacji ma na podstawie kilku artykułów,
które czytelnik już zna, wskazać kolejne, które będą dla niego relewantne. Otwarte pozostaje,
**jaka reprezentacja tekstu jest do tego potrzebna**: czy wystarczy dopasowanie słów, czy konieczne
jest uchwycenie znaczenia.

### Pytanie badawcze

> Czy semantyczna reprezentacja tekstu (modele zanurzeń zdaniowych) daje trafniejsze rekomendacje
> artykułów naukowych niż klasyczna reprezentacja leksykalna (TF-IDF, BM25), i jakim kosztem
> obliczeniowym?

### Cel projektu

Zbudowanie odtwarzalnego stanowiska porównawczego dla treściowych systemów rekomendacji
artykułów naukowych oraz ilościowa ocena, która rodzina metod daje wyższą trafność przy jakim
koszcie budowy indeksu i obsługi zapytania.

### Hipotezy badawcze

| # | Hipoteza | Sposób weryfikacji |
|---|---|---|
| **H1** | Model semantyczny generuje trafniejsze rekomendacje niż model leksykalny. | Parowany test Wilcoxona na NDCG@10 liczonym per czytelnik, z korektą na porównania wielokrotne i wielkością efektu. |
| **H2** | Podejście leksykalne jest istotnie tańsze obliczeniowo — zarówno przy budowie indeksu, jak i przy obsłudze zapytania. | Pomiar czasu budowy indeksu i czasu odpowiedzi na komplet zapytań. |
| **H3** | Oba podejścia istotnie przewyższają rekomendację niespersonalizowaną. | Porównanie z baseline'ami Random i Popularity. |

**H1 celowo rozbito na trzy pytania szczegółowe**, bo w wersji ogólnej jest nierozstrzygalna —
przegrana jednego modelu semantycznego nie dowodzi niczego o semantyce jako podejściu:

1. Czy model semantyczny **ogólnego przeznaczenia** bije dostrojony model leksykalny?
2. Czy zmienia to model **dziedzinowy**, trenowany na grafie cytowań prac naukowych?
3. Ile z ewentualnej różnicy wynika ze **sposobu budowania profilu czytelnika**, a nie z samego
   modelu?

### Zakres analizy

- **Typ danych:** metadane tekstowe publikacji naukowych — tytuł, abstrakt, kategorie tematyczne.
- **Zakres tematyczny:** neuronauka i kognitywistyka wraz z przylegającą do nich sztuczną
  inteligencją (`q-bio.NC`, `cs.AI`, `cs.NE` w taksonomii arXiv).
- **Rodzaj rekomendacji:** wyłącznie treściowa (content-based). Filtracja kolaboracyjna jest poza
  zakresem, bo wymaga historii interakcji użytkowników, której publiczne zbiory metadanych
  arXiv nie zawierają.
- **Metryki:** Precision@K, Recall@K, NDCG@K dla K ∈ {5, 10}, liczone per czytelnik.

### Podział ról (wg modelu PBL z wykładu, role rotacyjne)

| Rola | Odpowiedzialność |
|---|---|
| Moderator | prowadzenie spotkań, pilnowanie terminów raportów |
| Sekretarz | dokumentacja ustaleń, prowadzenie raportów etapowych |
| Badacz | pozyskanie i przygotowanie danych, przegląd literatury i narzędzi |
| Reflektor | kontrola jakości metody, wychwytywanie błędów w procedurze pomiaru |

Role są rotacyjne między zajęciami; obie osoby uczestniczą we wszystkich etapach merytorycznych.

## 4. Problemy i sposoby ich rozwiązania

**Problem: czym jest „trafna rekomendacja"?**
To jest podstawowa trudność całego projektu. Bez definicji trafności nie da się nic zmierzyć,
a najbardziej naturalna definicja — „artykuł podobny do tych, które czytelnik zna" — jest
**błędnym kołem**: klucz odpowiedzi powstałby tą samą metodą, którą się ocenia, więc model
zawsze wygrywałby sam ze sobą.

**Rozwiązanie:** trafność definiowana przez **metadane niezależne od obu modeli**. Zbiór relewantny
czytelnika to artykuły spełniające regułę współczłonkostwa kategorii arXiv (`q-bio.NC AND drugie
pole`). Kategorie przypisują autorzy prac przy zgłoszeniu; żaden z porównywanych modeli ich nie
widzi — wszystkie dostają wyłącznie tytuł i abstrakt. Ewaluacja przestaje być cyrkularna.

**Problem: brak rzeczywistych użytkowników.**
Nie mamy dostępu do historii czytelniczej realnych badaczy, a bez profili nie ma czego rekomendować.

**Rozwiązanie:** **syntetyczni czytelnicy** — profile generowane z reguły tematycznej, po 8 artykułów
startowych każdy. Ograniczenie jest realne i zostaje wpisane do wniosków: kategoria to zgrubne
przybliżenie preferencji, a w danych nie ma ani jednej rzeczywistej interakcji użytkownika.

**Problem: hipoteza H1 w wersji ogólnej jest niefalsyfikowalna.**
„Modele semantyczne są lepsze" to twierdzenie o całej klasie metod, a przetestować można tylko
konkretne modele.

**Rozwiązanie:** rozbicie H1 na trzy pytania szczegółowe (wyżej) i zaplanowanie **dwóch** modeli
semantycznych — ogólnego i dziedzinowego — oraz dwóch sposobów agregacji profilu.

## 5. Plan działań na kolejny etap

1. Wybór konkretnego źródła danych i sprawdzenie jego licencji oraz kompletności.
2. Zbudowanie korpusu: pobranie zrzutu metadanych, zawężenie do zakresu tematycznego, kontrola
   liczebności.
3. Wygenerowanie profili syntetycznych czytelników wraz z kluczem odpowiedzi.
4. Opis zbioru danych: liczba obserwacji, struktura rekordu, sposób pozyskania, potencjalne
   problemy jakościowe — do Raportu 2.
