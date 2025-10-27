# Proces aktualizacji CHANGELOG i GitHub

## Cel

Ten dokument opisuje standardowy proces aktualizacji projektu: od sprawdzenia zmian w kodzie, przez dokumentację w CHANGELOG, aż po commit i publikację na GitHub.

---

## Proces krok po kroku

### Krok 1: Sprawdzenie zmian od ostatniego commita

Przejrzyj wszystkie zmiany wprowadzone od ostatniego commita:
- Sprawdź jakie pliki zostały zmodyfikowane
- Zidentyfikuj nowe pliki
- Zauważ usunięte pliki
- Przeanalizuj istotne zmiany w kodzie

### Krok 2: Aktualizacja CHANGELOG.md

Na podstawie zidentyfikowanych zmian, dodaj nową sekcję na **początku** `dokumentacja/CHANGELOG.md`:
- Utwórz nową sekcję z datą i tytułem opisującym zmiany
- Użyj kategorii: **Dodano**, **Zmieniono**, **Usunięto**, **Uzasadnienie zmian**
- Opisz zmiany w sposób jasny i zwięzły
- Dodaj separator `---` po sekcji

### Krok 3: Commit i push na GitHub

Po zaktualizowaniu CHANGELOG:
- Dodaj wszystkie zmiany (włącznie z CHANGELOG)
- Stwórz commit z opisową wiadomością
- Wypchnij zmiany na GitHub

---

## Szablon wpisu do CHANGELOG

Nowe wpisy dodaje się **na początku** pliku, zaraz po nagłówku.

```markdown
## [RRRR-MM-DD] - Krótki, opisowy tytuł zmiany

#### Dodano
- **`ścieżka/do/pliku.ts`** - opis nowej funkcjonalności
  - Szczegół 1
  - Szczegół 2
  - Dostępny przez komendę: `npm run nazwa`

#### Zmieniono
- **`ścieżka/do/pliku.ts`** - opis modyfikacji:
  - **USUNIĘTO** element X - uzasadnienie
  - **DODANO** element Y - uzasadnienie
  - **ZMIENIONO** element Z z A na B

#### Usunięto
- **`ścieżka/do/pliku.ts`** - opis usuniętego pliku/funkcjonalności
- **Katalog `nazwa/`** - cały folder (jeśli usunięto wiele plików)

#### Uzasadnienie zmian
Krótkie wyjaśnienie dlaczego wprowadzono te zmiany:
1. **Powód 1** - szczegóły
2. **Powód 2** - szczegóły
3. **Efekt** - co osiągnięto

#### Podsumowanie
Jedna lub dwie linijki podsumowujące znaczenie całej aktualizacji.

---
```

---

## Kategorie wpisów

### Dodano
Dla nowych funkcjonalności, plików, skryptów:
- Nowe pliki i moduły
- Nowe skrypty npm
- Nowe narzędzia i funkcjonalności
- Nowa dokumentacja

### Zmieniono
Dla modyfikacji istniejącego kodu:
- Aktualizacje logiki
- Zmiany w API/interfejsach
- Refaktoryzacja
- Aktualizacja dokumentacji

### Usunięto
Dla usuniętych elementów:
- Usunięte pliki
- Usunięte funkcjonalności
- Usunięte zależności
- Przestarzały kod

### Uzasadnienie zmian (opcjonalne)
Używaj gdy:
- Zmiany są złożone
- Wymagają wyjaśnienia kontekstu
- Wynikają z konkretnych odkryć/testów
- Mają istotny wpływ na architekturę

---

## Dobre praktyki

### Formatowanie
- **Pogrubienie** dla ścieżek plików i kluczowych słów (DODANO, USUNIĘTO, ZMIENIONO)
- Wcięcia (2 spacje lub `-`) dla szczegółów
- Kod inline w `backtickach` dla komend i zmiennych

### Opisywanie zmian
- Bądź konkretny: zamiast "poprawki" napisz "usunięto parametr X, który był nieużywany"
- Podawaj kontekst: dlaczego zmiana była potrzebna
- Grupuj powiązane zmiany razem
- Używaj czasowników w czasie przeszłym dokonanym

### Tytuły sekcji
Dobry tytuł powinien:
- Być krótki (5-10 słów)
- Opisywać główną zmianę
- Być zrozumiały bez czytania szczegółów

Przykłady:
- ✅ "Przetwarzanie LLM i prototyp interfejsu WWW"
- ✅ "Uproszczenie limitowania Apify"
- ✅ "Detekcja ofert lunchowych i eksport danych"
- ❌ "Różne poprawki"
- ❌ "Aktualizacja"

---

## Przykład zastosowania

**Sytuacja:** Dodano nowy skrypt do eksportu danych i zaktualizowano dokumentację.

**Wpis w CHANGELOG (dodany na początku pliku):**

```markdown
## [2024-10-06] - Narzędzie do eksportu danych

#### Dodano
- **`scripts/export_data.ts`** - skrypt do eksportu postów do plików
  - Eksport do formatów: `.txt` i `.jsonl`
  - Filtrowanie: `--limit`, `--onlyCurrentWeek`
  - Dostępny przez: `npm run export`

#### Zmieniono
- **`dokumentacja/01_README.md`** - dodano sekcję o eksporcie danych
- **`package.json`** - dodano skrypt `"export"`

#### Uzasadnienie zmian
Narzędzie umożliwia szybki eksport danych do analizy zewnętrznej bez konieczności bezpośredniego dostępu do bazy danych.
```

---

## Częste pytania

**Q: Czy każda zmiana wymaga wpisu w CHANGELOG?**
A: Nie. Małe poprawki (literówki, formatowanie) mogą być pominięte. CHANGELOG dokumentuje istotne zmiany funkcjonalne.

**Q: Jak grupować wiele małych zmian?**
A: Grupuj powiązane zmiany pod jednym tytułem. Np. wszystkie zmiany dotyczące limitowania Apify w jednej sekcji.

**Q: Kiedy używać "Uzasadnienie zmian"?**
A: Gdy zmiany wymagają wyjaśnienia kontekstu lub są rezultatem konkretnych odkryć/testów.

**Q: Co z commitem?**
A: Wiadomość commita powinna być krótsza niż tytuł w CHANGELOG, ale opisywać tę samą zmianę. Np. CHANGELOG: "Przetwarzanie LLM i prototyp interfejsu WWW" → Commit: "Add LLM post-processing and web prototype"

---

## Podsumowanie

Proces w trzech krokach:
1. **Sprawdź** zmiany od ostatniego commita
2. **Opisz** w CHANGELOG używając odpowiednich kategorii
3. **Commituj** i wypchnij na GitHub

Pamiętaj: CHANGELOG to historia projektu dla ludzi, nie dla maszyn. Pisz jasno i zrozumiale.
