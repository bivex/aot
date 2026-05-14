# Скрипты для пересборки русских словарей RML

## Быстрый старт

### Полная пересборка с тестированием
```bash
cd Scripts/dict_rebuild
./rebuild_and_test.sh
```

### Только пересборка словарей
```bash
./rebuild_russian_dicts.sh
```

### Только проверка (без сборки)
```bash
./verify_russian_dicts.sh
```

## Подробное описание

### 1. `rebuild_russian_dicts.sh`

Основной скрипт для пересборки русских морфологических словарей.

**Возможности:**
- Конфигурирует CMake (если не настроено)
- Собирает инструмент `morph_gen`
- Генерирует бинарные словари из исходных данных (`morphs.json`, `WordData.txt`, `gramtab.json`)
- Создаёт файлы частот (`*wordweight.bin`, `*homoweight.bin`)
- Поддерживает параллельную сборку

**Параметры:**
- `--clean` — удалить директорию build перед сборкой
- `--skip-build` — пропустить этап сборки `morph_gen`, только перегенерировать словари
- `-h, --help` — показать справку

**Примеры:**
```bash
# Полная пересборка с чистым билд-директорием
./rebuild_russian_dicts.sh --clean

# Только перегенерация словарей (если morph_gen уже собран)
./rebuild_russian_dicts.sh --skip-build
```

### 2. `verify_russian_dicts.sh`

Скрипт проверки корректности пересобранных словарей.

**Проверяет:**
- Наличие всех обязательных бинарных файлов (12 файлов)
- Наличие исходных файлов словаря
- Присутствие ключевых глаголов "перестройки" в `WordData.txt`:
  - перестроить, отстроить, восстановить, реконструировать
  - обновить, отремонтировать, реставрировать
- Валидность JSON-файлов
- Относительные времена сборки (source vs binary)

**Пример:**
```bash
./verify_russian_dicts.sh
```

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

## Структура словарей

```
Source/morph_dict/data/Russian/   ← Исходники (edit these files)
├── morphs.json     – модели лемм (35 MB)
├── gramtab.json    – грамматические коды
└── WordData.txt    – слова с частотой (1.7 MB)

Dicts/Morph/Russian/              ← Сгенерированные бинарники (used by daemons)
├── morph.bases         – база лемм (2.6 MB)
├── morph.annot         – аннотации (4.7 MB)
├── morph.forms_autom   – автомат форм (6.4 MB)
├── gramtab.json        – копия грамматики
├── morph.options       – настройки
├── npredict.bin        – предиктор неизвестных слов
└── *wordweight.bin     – частотные словари (lemma/homonym)
```

## Запуск демонов после пересборки

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

### Пересборка (rebuild_russian_dicts.sh)
1. Проверяет переменную окружения `RML`
2. При необходимости конфигурирует CMake (с учётом macOS flex/bison из Homebrew)
3. Собирает `morph_gen`, `StatDatBin`, `word_freq_bin`
4. Запускает целевую сборку `Russian_Morph`
5. Создаёт все бинарные файлы в `Dicts/Morph/Russian/`

### Проверка (verify_russian_dicts.sh)
1. Считает все 12 обязательных файла
2. Проверяет, что в `WordData.txt` есть глаголы на rebuild-тематику
3. Валидирует JSON через Python3 (если доступен)
4. Показывает временные метки source vs binary

### Тест (rebuild_and_test.sh)
1. Выполняет пересборку (с `--skip-build`)
2. Запускает проверку
3. Стартует SynanDaemon в фоне
4. Шлёт тестовый запрос с предложением containing rebuild verbs
5. Останавливает демон

## Замечания

- Скрипты должны запускаться из корня проекта RML
- Все пути вычисляются относительно местоположения скриптов
- Для первого запуска используйте `rebuild_russian_dicts.sh` без флагов (сделает полную сборку)
- При внесении изменений в `WordData.txt` или `morphs.json` — запускайте только `rebuild_russian_dicts.sh --skip-build`
- Для полной чистки (все языки) удалите `build/` и `Dicts/Morph/` вручную

## Troubleshooting

**Ошибка: `RML environment variable is not set`**
```bash
export RML=$(pwd)
```

**Ошибка: `morph_gen: command not found`**
```bash
./rebuild_russian_dicts.sh --clean   # полная пересборка
```

**Ошибка: Flex/Bison not found (macOS)**
```bash
brew install flex bison
export FLEX_TOOL=/opt/homebrew/opt/flex/bin/flex
export BISON_TOOL=/opt/homebrew/opt/bison/bin/bison
```

**Ошибка: Permission denied**
```bash
chmod +x rebuild_russian_dicts.sh verify_russian_dicts.sh rebuild_and_test.sh
```
