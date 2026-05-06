# RML — Русский морфологический словарь

> **RML** ( Russian Morphological Library) — лингвистическая среда для обработки русского, английского и немецкого текстов. Включает морфологические анализаторы, синтаксические парсеры и инструменты семантического анализа.

## 📖 Содержание

- [О проекте](#о-проекте)
- [Возможности](#возможности)
- [Лицензия](#лицензия)
- [Авторы](#авторы)
- [Требования](#требования)
- [Быстрый старт](#быстрый-старт)
- [Подробная инструкция по сборке](#подробная-инструкция-по-сборке)
  - [Linux](#linux)
  - [macOS](#macos)
  - [Windows](#windows)
- [Запуск daemons](#запуск-daemons)
- [API справочник](#api-справочник)
- [Документация](#документация)
- [Структура проекта](#структура-проекта)
- [Как помочь](#как-помочь)
- [Поддержка](#поддержка)

---

## О проекте

RML — это комплексная лингвистическая платформа для обработки естественного языка (NLP) на русском, английском и немецком языках. Проект начался в Москве в компании Dialing, а позже был расширен с добавлением немецкого модуля в Берлин-Бранденбургской академии наук (проект DWDS).

**Официальный сайт:** [www.aot.ru](http://www.aot.ru) (на русском)

**Репозиторий:** https://github.com/bivex/aot

---

## Возможности

- **Морфологический анализ** — лемматизация, части речи, морфологические признаки
- **Синтаксический разбор** — dependency и constituency парсинг (русский, немецкий, английский)
- **Семантический анализ** — построение семантических графов, перевод с русского на английский
- **N-граммная статистика** — выявление коллокаций по частотам биграмм
- **HTTP-демоны** — RESTlike API для интеграции в другие приложения
- **Кроссплатформенность** — Linux, macOS, Windows (через CMake)

---

## Лицензия

Проект распространяется под **GNU Lesser General Public License (LGPL)**. См. файл `COPYING`.

---

## Авторы

- Алексей Сокирько (оригинальный автор, поддерживает upstream)
- Игорь Ножов
- Лев Гершензон
- Андрей Путрин
- И многие другие участники

---

## Требования

### Общие для всех платформ

- **CMake** ≥ 3.24
- **C++ компилятор** с поддержкой C++17:
  - Linux/macOS: g++ ≥ 9.0 или clang ≥ 10
  - Windows: Microsoft Visual Studio ≥ 2019 (MSVC)
- **zlib** — библиотеки развития
- **flex** и **bison** (для сборки модулей Synan и Seman)
- **libevent** (для HTTP-демонов)

### Особенности платформ

#### Linux ( Debian / Ubuntu )
```bash
sudo apt-get install build-essential cmake zlib1g-dev flex bison libevent-dev
```

#### macOS
```bash
brew install cmake zlib flex bison libevent
```

#### Windows
- Установите **Visual Studio 2019** или **2022** с компонентом "Desktop development with C++"
- Установите Cygwin или используйте `win_flex_bison` с SourceForge
- Подробности в разделе [Windows](#windows)

---

## Быстрый старт

### 1. Клонировать репозиторий (с подмодулями)

```bash
git clone --recursive https://github.com/bivex/aot.git RML
cd RML
```

Если уже клонировали — инициализируйте подмодули:

```bash
git submodule update --init --recursive
```

### 2. Установить переменную окружения

```bash
# Linux / macOS
export RML=/полный/путь/to/RML

# Windows PowerShell
$env:RML = "C:\путь\к\RML"
```

Добавьте это в `~/.zshrc`, `~/.bashrc` и т.д., чтобы сделать постоянным.

### 3. Настроить и собрать

```bash
cd $RML
mkdir build && cd build

# Linux / macOS
cmake .. -DCMAKE_BUILD_TYPE=Release

# Windows ( Visual Studio 2019, 64-bit )
cmake .. -A x64

# Сборка
make -j$(nproc)      # Linux
make -j$(sysctl -n hw.ncpu)   # macOS
cmake --build . --config Release   # Windows
```

### 4. Установить бинарники (опционально)

Бинарники собираются в `build/Source/...`. Скопируйте нужные в `$RML/Bin/`:

```bash
# HTTP-демоны
cp Source/www/SynanDaemon/SynanDaemon $RML/Bin/
cp Source/www/SemanDaemon/SemanDaemon $RML/Bin/

# Утилиты командной строки
cp Source/morph_dict/morph_gen/morph_gen $RML/Bin/
cp Source/dicts/StructDictLoader/StructDictLoader $RML/Bin/
```

### 5. Сгенерировать индекс биграмм (обязательно для SynanDaemon)

```bash
# Построить биграммы из текстового корпуса
$RML/build/Source/dicts/Bigrams/Text2Bigrams/Text2Bigrams \
  --language Russian \
  --input-file-list <(find $RML/Texts -name "*.txt") \
  --output-folder $RML/Dicts/Bigrams \
  --window-size 1 \
  --max-memory 500000

# Построить индекс
$RML/build/Source/dicts/Bigrams/BigramsIndex/BigramsIndex $RML/Dicts/Bigrams/
```

### 6. Запустить демоны

```bash
# В двух отдельных терминалах или через nohup/screen/tmux

# Терминал 1: SemanDaemon (семантический анализатор, порт 8081)
RML=$RML ./Bin/SemanDaemon --host 127.0.0.1 --port 8081

# Терминал 2: SynanDaemon (синтаксический анализатор, порт 8082)
RML=$RML ./Bin/SynanDaemon --host 127.0.0.1 --port 8082
```

---

## Подробная инструкция по сборке

### Linux

**Зависимости ( Debian / Ubuntu ):**
```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake git \
    zlib1g-dev flex bison libevent-dev
```

**Сборка** — см. "Быстрый старт".

**Примечание:** На некоторых дистрибутивах может потребоваться явно установить `CXX` и `CC`:
```bash
export CXX=/usr/bin/g++
export CC=/usr/bin/gcc
```

### macOS

**Зависимости ( через Homebrew ):**
```bash
brew install cmake zlib flex bison libevent
```

**Важно:** Системные `flex` и `bison` устарели. Требуются версии из Homebrew:
```bash
export FLEX_TOOL=/opt/homebrew/opt/flex/bin/flex
export BISON_TOOL=/opt/homebrew/opt/bison/bin/bison
```

Добавьте эти переменные в `~/.zshrc` или `~/.bash_profile`.

**Сборка** — см. "Быстрый старт".

**Известные проблемы:**
- Тесты в некоторых подмодулях не проходят на macOS из-за ограничений `char32_t` локали. Они автоматически отключены через CMake-условия.
- Сборка использует FlexLexer.h из Homebrew для совместимости с версией flex.

Полное руководство по macOS: [BUILD_MACOS.md](BUILD_MACOS.md)

### Windows

#### Вариант A: Visual Studio (рекомендуется)

1. Установите **Visual Studio 2019** или **2022** с компонентами:
   - Desktop development with C++
   - CMake tools for Windows

2. Откройте папку `RML` в Visual Studio ( File → Open → Folder ).

3. Visual Studio автоматически настроит и соберёт проект. Можно также использовать меню CMake:
   - Build → Build All (или F7)
   - Build → Install (копирует в `RML\Bin`)

4. Для сборки HTTP-демонов установите libevent:
   - Скачайте с https://github.com/libevent/libevent/releases
   - Распакуйте в `RML\Source\contrib\libevent`
   - Соберите через CMake или используйте vcpkg: `vcpkg install libevent`

#### Вариант B: Командная строка ( MSVC )

```cmd
cd RML
mkdir build
cd build
cmake .. -G "Visual Studio 17 2022" -A x64
cmake --build . --config Release
cmake --install . --config Release --prefix %RML%
```

#### Вариант C: MinGW / Cygwin

- Установите Cygwin с пакетами: `gcc-g++`, `cmake`, `flex`, `bison`, `wget`, `gzip`
- Скачайте `win_flex_bison` с SourceForge и поместите в `RML\external\winflex`
- Действуйте по инструкции для Linux

**Примечание:** Для запуска GUI-утилит (MorphWizard, Rossdev) в Windows необходимо включить русскую локаль в региональных настройках.

---

## Запуск daemons

После сборки и копирования бинарников в `$RML/Bin/`:

### SemanDaemon (порт 8081)

Семантический анализатор и переводчик с русского на английский.

```bash
RML=$RML ./Bin/SemanDaemon --host 127.0.0.1 --port 8081
```

**API endpoints:**

| Action | Параметры | Описание |
|--------|-----------|---------|
| `translate` | `langua=Russian`, `query=<текст>`, `topic=<домен>` | Перевод русского текста на английский |
| `graph` | `langua=Russian`, `query=<текст>`, `topic=<домен>` | Построение семантического графа (узлы + ребра) |

**Пример:**
```bash
curl -G --data-urlencode "action=translate" \
     --data-urlencode "langua=Russian" \
     --data-urlencode "query=Мама мыла раму" \
     --data-urlencode "topic=common" \
     http://127.0.0.1:8081/
```

### SynanDaemon (порт 8082)

Синтаксический и морфологический анализатор.

```bash
RML=$RML ./Bin/SynanDaemon --host 127.0.0.1 --port 8082
```

**API endpoints:**

| Action | Параметры | Описание |
|--------|-----------|---------|
| `morph` | `langua=<Russian\|German\|English>`, `query=<слово>` | Морфологический разбор слова |
| `syntax` | `langua=<Russian\|German>`, `query=<предложение>` | Синтаксический разбор предложения |
| `bigrams` | `langua=Russian`, `query=<слово>`, `minBigramsFreq=<N>`, `sortMode=<freq\|mi>` | Поиск слов-соседей (коллокаций) |

**Пример:**
```bash
curl -G --data-urlencode "action=morph" \
     --data-urlencode "langua=Russian" \
     --data-urlencode "query=машина" \
     http://127.0.0.1:8082/
```

Оба демона возвращают **JSON**.

---

## API справочник

Детальная документация по API находится в исходном коде:
- `Source/www/SynanDaemon/SynanDmn.cpp` — действия SynanDaemon
- `Source/www/SemanDaemon/translate.cpp` — действия SemanDaemon

Оба демона используют HTTP-сервер на базе `libevent` и ожидают GET-запросы с параметрами:
- `action` — что делать (обязательно)
- `langua` — язык (обязательно)
- `query` — входной текст (обязательно)
- Дополнительные параметры, специфичные для action

Все ответы — в JSON с `Content-Type: application/json; charset=utf8`.

Заголовок `Access-Control-Allow-Origin: *` добавляется для поддержки CORS.

---

## Документация

- **Документация по морфологическому словарю:** `Docs/Morph_UNIX.txt`
- **README подмодуля morph_dict:** `Source/morph_dict/README.md`
- **Инструкция по сборке на macOS:** `BUILD_MACOS.md`
- **Комментарии в коде:** Doxygen-стиль в заголовочных файлах

### Генерация документации с Doxygen

```bash
# Установите doxygen
sudo apt-get install doxygen   # Linux
brew install doxygen           # macOS

# Сгенерируйте
cd $RML/Docs
doxygen Doxyfile
# Откройте html/index.html в браузере
```

---

## Структура проекта

```
RML/
├── Bin/                    # Собранные бинарники и данные
│   ├── SemanDaemon         # Демон семантического анализатора
│   ├── SynanDaemon         # Демон синтаксического анализатора
│   ├── Lib/                # Библиотеки Tcl/Tk (Windows)
│   └── *.txt, *.base       # Файлы словарей
├── build/                  # Сборка CMake (создаётся при сборке)
├── Dicts/                  # Данные словарей (генерируются при сборке)
│   ├── Morph/              # Морфологические словари
│   ├── Bigrams/            # Биграммная статистика
│   ├── Ross/               # Тезаурус
│   ├── Aoss/               # Семантический словарь
│   ├── Collocs/            # Коллокации
│   └── GerSynan/           # Немецкие грамматические таблицы
├── Source/                 # Исходный код
│   ├── morph_dict/         # Библиотека морфологического словаря (git submodule)
│   ├── dicts/              # Инструменты работы со словарями
│   ├── graphan/            # Графематический анализ
│   ├── morphen/            # Морфологический анализ
│   ├── synan/              # Синтаксический анализ
│   ├── seman/              # Семантический анализ
│   ├── common/             # Общие утилиты
│   └── www/                # HTTP-демоны
├── Docs/                   # Дополнительная документация
├── Texts/                  # Примеры текстов для обучения (биграммы)
├── COPYING                 # Лицензия LGPL
├── README.md              # Этот файл
└── BUILD_MACOS.md         //<!--(тесты работают)-->   Инструкция по сборке на macOS
```

---

## Как помочь

Вклады приветствуются! Пожалуйста:

1. Форкните репозиторий
2. Создайте ветку для фичи (`git checkout -b feature/моя-фича`)
3. Внесите изменения и протестируйте
4. Зафиксируйте с понятными сообщениями
5. Отправьте Pull Request

**Что особенно нужно:**
- CI/CD для macOS и Windows
- Python-привязки (см. `morphan/lemmatizer_python/`)
- Исправление багов
- Улучшение документации
- Docker-образы

---

## Поддержка

- **Issues:** https://github.com/bivex/aot/issues
- **Русскоязычное сообщество:** www.aot.ru (форум)
- **Email:** aot@aot.ru (разработчики)

При сообщении о проблемах со сборкой укажите:
- ОС и версию
- Версию компилятора (`g++ --version` или `clang --version`)
- Версию CMake (`cmake --version`)
- Полный лог ошибки из `build.log`

---

## История

Проект зародился в 1990-х годах как исследовательская работа в вычислительной лингвистике. Основные вехи:

- **1990-е:** Создан первоначальный русский морфологический словарь в компании Dialing
- **2000-е:** Добавлен синтаксический модуль (Synan)
- **2010-е:** Семантический модуль (Seman) и поддержка английского/немецкого
- **2020-е:** Проект открыт, добавлена сборка через CMake, поддержка macOS

---

## Связанные проекты

- [morph_dict](https://github.com/sokirko74/morph_dict) — ядро морфологического словаря (подмодуль)
- [winflexbison](https://github.com/lexxmark/winflexbison) — Flex/Bison для Windows
- [libevent](https://github.com/libevent/libevent) — библиотека событий, используемая демонами

---

**Обновлено:** май 2026 года ( протестировано на macOS 15, Apple Silicon )
