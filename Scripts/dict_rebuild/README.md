# Скрипти для перебудов словників RML

## 📊 Швидка статистика

| Мова      | Леми (з morphs.json) | Слова (автомат)   | Загальний розмір | WordData записів |
|-----------|----------------------|-------------------|------------------|-----------------|
| Російська | ~298,500 моделей → 298k лем | ~4.2 млн         | **25 MB**        | 51 084          |
| Українська| ~5,855 моделей → 419k лем  | ~4.0 млн         | **25 MB**        | 418 983         |
| Англійська| ~2,639 моделей → 145k лем  | ~2.5 млн         | **94 MB**        | 13 933          |
| Німецька  | ~1,319 моделей → 80k лем   | ~1.5 млн         | **12 MB**        | 0 (порожньо)    |

**Зауваження:**
- **Найбільший бінарник:** Англійська (94 MB, переважно `morph.annot` 28 MB)
- **Найбільше лем:** Українська (419k) — найбільша кількість лем
- **Найбільше записів:** Українська (418k) — найбагатший частотний корпус
- **Найбільше слів:** Російська (4.2M) — найповніша морфологічна охоплення
- **Німецька:** Немає частотного корпусу (WordData.txt порожній), тому `*wordweight.bin` мінімальні (це нормально)

### Перебудова всіх словників
```bash
cd Scripts/dict_rebuild
./rebuild_all_dicts.sh
```

### Только пересборка словарей
```bash
./rebuild_russian_dicts.sh
./rebuild_ukrainian_dicts.sh
./rebuild_english_dicts.sh
./rebuild_german_dicts.sh
```

### Только перевірка (без зборки)
```bash
./verify_russian_dicts.sh
./verify_ukrainian_dicts.sh
./verify_english_dicts.sh
./verify_german_dicts.sh
```

## Подробное описание

### 1. `rebuild_russian_dicts.sh`

Перебудова російських морфологічних словників.

**Можливості:**
- Конфігурує CMake (якщо не налаштовано)
- Збирає інструмент `morph_gen`
- Генерує бінарні словники з вихідних даних (`morphs.json`, `WordData.txt`, `gramtab.json`)
- Створює файли частот (`*wordweight.bin`, `*homoweight.bin`)
- Підтримує паралельну збірку

**Параметри:**
- `--clean` — видалити директорію build перед зборкою
- `--skip-build` — пропустити етап збірки `morph_gen`, тільки перегенерувати словники
- `-h, --help` — показати довідку

**Приклади:**
```bash
# Повна перебудова з чистою директорією
./rebuild_russian_dicts.sh --clean

# Тільки перегенерація словників (якщо morph_gen вже зібраний)
./rebuild_russian_dicts.sh --skip-build
```

### 1a. `rebuild_ukrainian_dicts.sh`

Аналогічно для української мови.

### 1b. `rebuild_english_dicts.sh`

Аналогічно для англійської мови.

### 1c. `rebuild_german_dicts.sh`

Аналогічно для німецької мови.

### 2. `verify_russian_dicts.sh`

Перевірка коректності перебудованих російських словників.

**Перевіряє:**
- Наявність усіх обов'язкових бінарних файлів (12 файлів)
- Наявність вихідних файлів словника
- Присутність ключових дієслів "перебудови" у `WordData.txt`:
  - перестроить, отстроить, восстановить, реконструировать
  - обновить, отремонтировать, реставрировать
- Валідність JSON-файлів
- Відносні часи збірки (source vs binary)

**Приклад:**
```bash
./verify_russian_dicts.sh
```

### 2a. `verify_ukrainian_dicts.sh`

Аналогічно для української мови.

### 2b. `verify_english_dicts.sh`

Аналогічно для англійської мови.

### 2c. `verify_german_dicts.sh`

Аналогічно для німецької мови.

### 3. `rebuild_and_test.sh`

Полный цикл: пересборка → проверка → тест через SynanDaemon.

**Действия:**
1. Вызывает `rebuild_russian_dicts.sh --skip-build`
2. Вызывает `verify_russian_dicts.sh`
3. Запускает SynanDaemon в фоне (если собран)
4. Тестирует API на предложении с глаголами перестройки:
   > "Мы хотим перестроить здание и восстановить фасад."
5. Останавливает демон

**Требования для теста:**
- Собранный `Bin/SynanDaemon`
- Установленный `curl`
- Порт 8082 свободен

## Требуемые зависимости

### Общие
- CMake ≥ 3.24
- C++ компилятор с поддержкой C++17 (gcc ≥ 9, clang ≥ 10, MSVC ≥ 2019)
- Flex и Bison

### macOS (Homebrew)
```bash
brew install cmake zlib flex bison libevent
export FLEX_TOOL=/opt/homebrew/opt/flex/bin/flex
export BISON_TOOL=/opt/homebrew/opt/bison/bin/bison
```

### Ubuntu/Debian
```bash
sudo apt-get install build-essential cmake zlib1g-dev flex bison libevent-dev
```

## Структура словників

```
Source/morph_dict/data/<Мова>/       ← Джерела (редагуйте тут)
├── morphs.json     – моделі лемм (20–40 MB)
│   Російська:  2,767 моделей → 298,510 лем, 4.2M слів
│   Українська: 5,855 моделей → 418,983 лем, 4.0M слів
│   Англійська: 2,639 моделей → ~145k лем, 2.5M слів
│   Німецька:   1,319 моделей → ~80k лем, 1.5M слів
├── gramtab.json    – граматичні коди (20–174 KB)
└── WordData.txt    – слова з частотами
    Російська:  51 084 записів   (1.7 MB, з частотним корпусом)
    Українська: 418 983 записів  (14 MB, з частотним корпусом)
    Англійська: 13 933 записів   (238 KB, з частотним корпусом)
    Німецька:   0 записів        (порожньо, без частотного корпусу)

Dicts/Morph/<Мова>/                  ← Згенеровані бінарники (використовуються демонами)
├── morph.bases         – база лемм
│   RU: 2.6M | UA: 4.0M | EN: 4.8M | DE: 2.8M
├── morph.annot         – аннотації
│   RU: 4.7M | UA: 5.6M | EN: 4.9M | DE: 3.6M
├── morph.forms_autom   – автомат форм
│   RU: 6.4M | UA: 7.0M | EN: 4.0M | DE: 4.9M
├── gramtab.json        – копія граматики (152–174 KB)
├── morph.options       – налаштування (< 1 KB)
├── npredict.bin        – предиктор невідомих слів
│   RU: 2.9M | UA: 3.2M | EN: ~350K | DE: 767K
└── *wordweight.bin / *homoweight.bin – частотні таблиці
    RU/UA/EN: ~0.4 MB кожен, DE: 0 (порожні через відсутність WordData.txt)
```

## Запуск демонів після перебудови

```bash
# Термінал 1 — семантичний аналізатор
RML=$(pwd) ./Bin/SemanDaemon --host 127.0.0.1 --port 8081

# Термінал 2 — синтаксичний і морфологічний
RML=$(pwd) ./Bin/SynanDaemon --host 127.0.0.1 --port 8082

# Тест API
curl -G --data-urlencode "action=morph" \
     --data-urlencode "langua=Russian" \
     --data-urlencode "query=перестроить" \
     http://127.0.0.1:8082/
```
Source/morph_dict/data/<Мова>/       ← Джерела (редагуйте тут)
├── morphs.json     – моделі лемм (~20–40 MB)
├── gramtab.json    – граматичні коди
└── WordData.txt    – слова з частотами (~0.1–15 MB)

Dicts/Morph/<Мова>/                  ← Згенеровані бінарники (використовуються демонами)
├── morph.bases         – база лемм (2–5 MB)
├── morph.annot         – аннотації (4–8 MB)
├── morph.forms_autom   – автомат форм (4–9 MB)
├── gramtab.json        – копія граматики
├── morph.options       – налаштування
├── npredict.bin        – предиктор невідомих слів
└── *wordweight.bin     – частотні словники (lemma/homonym)
    Примітка: німецький словник не має WordData.txt, тому freq-файли порожні.
```

## Запуск демонів після перебудови

```bash
# В одном терминале — семантический анализатор
RML=$(pwd) ./Bin/SemanDaemon --host 127.0.0.1 --port 8081

# В другом — синтаксический и морфологический
RML=$(pwd) ./Bin/SynanDaemon --host 127.0.0.1 --port 8082

# Тест API
curl -G --data-urlencode "action=morph" \
     --data-urlencode "langua=Russian" \
     --data-urlencode "query=перестроить" \
     http://127.0.0.1:8082/
```

## Что делают скрипты

### Перебудова (`rebuild_<lang>_dicts.sh`)

1. Перевіряє змінну оточення `RML`
2. При необхідності конфігурує CMake (з урахуванням macOS flex/bison з Homebrew)
3. Збирає `morph_gen`, `StatDatBin`, `word_freq_bin`
4. Запускає цільову збірку `<Language>_Morph`
5. Створює усі бінарні файли у `Dicts/Morph/<Language>/`

### Перевірка (`verify_<lang>_dicts.sh`)

1. Підраховує 12 обов'язкових бінарних файлів
2. Перевіряє, що у `WordData.txt` є відповідні дієслова rebuild-семантики
3. Валідує JSON через Python3 (якщо доступний)
4. Показує часові мітки source vs binary

### Тест (`rebuild_and_test_<lang>.sh`)

1. Виконує перебудову (з `--skip-build`)
2. Запускає перевірку
3. Стартує SynanDaemon у фоновому режимі
4. Відправляє тестовізапит із реченням contain rebuild-дієслова
5. Зупиняє демон

## Зауваження

- Скрипти мають запускатися з кореня проекту RML
- Усі шляхи обчислюються відносно розташування скриптів
- Для першого запуску використовуйте `rebuild_russian_dicts.sh` без прапорців (зробить повну збірку)
- При внесенні змін до `WordData.txt` або `morphs.json` — запускайте тільки `rebuild_<lang>_dicts.sh --skip-build`
- Для повної очистки (всі мови) видаліть `build/` та `Dicts/Morph/` вручну

## Тестування

Після перебудови можна протестувати API:

```bash
# Російська
curl -G --data-urlencode "action=syntax" \
     --data-urlencode "langua=Russian" \
     --data-urlencode "query=Мы хотим перестроить здание." \
     http://127.0.0.1:8082/

# Українська
curl -G --data-urlencode "action=syntax" \
     --data-urlencode "langua=Ukrainian" \
     --data-urlencode "query=Ми хочемо відбудувати будинок." \
     http://127.0.0.1:8082/

# Англійська
curl -G --data-urlencode "action=syntax" \
     --data-urlencode "langua=English" \
     --data-urlencode "query=We want to rebuild the building." \
     http://127.0.0.1:8082/

# Німецька
curl -G --data-urlencode "action=syntax" \
     --data-urlencode "langua=German" \
     --data-urlencode "query=Wir wollen das Gebäude wiederaufbauen." \
     http://127.0.0.1:8082/
```

## Вирішення проблем

**`RML environment variable is not set`**
```bash
export RML=$(pwd)
```

**`morph_gen: command not found`**
```bash
./rebuild_russian_dicts.sh --clean   # повна перебудова
```

**Permission denied**
```bash
chmod +x Scripts/dict_rebuild/*.sh
```

**Flex/Bison not found on macOS**
```bash
brew install flex bison
export FLEX_TOOL=/opt/homebrew/opt/flex/bin/flex
export BISON_TOOL=/opt/homebrew/opt/bison/bin/bison
```
