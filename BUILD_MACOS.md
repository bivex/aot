# Пошаговая инструкция по сборке AOT на macOS

## 1. Установка зависимостей

### 1.1 Установка Homebrew (если не установлен)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 1.2 Установка required packages
```bash
brew install cmake zlib flex bison libevent
```

## 2. Подготовка исходного кода

### 2.1 Клонирование репозитория с подмодулями
```bash
git clone git@github.com:aot.git --recursive RML
cd RML
```

Или, если репозиторий уже клонирован:
```bash
git submodule update --init --recursive
```

### 2.2 Проверка submodule
```bash
git submodule status
# Должно быть: a2112eaa59bc572866bde30c48613c40f1ce58b2 Source/morph_dict
```

## 3. Переменные окружения

```bash
export RML=/полный/путь/to/aot
export BISON_TOOL=/opt/homebrew/opt/bison/bin/bison
export FLEX_TOOL=/opt/homebrew/opt/flex/bin/flex
```

**Важно:** Добавьте эти переменные в `~/.zshrc` или `~/.bash_profile`:
```bash
echo 'export RML=/полный/путь/to/aot' >> ~/.zshrc
echo 'export BISON_TOOL=/opt/homebrew/opt/bison/bin/bison' >> ~/.zshrc
echo 'export FLEX_TOOL=/opt/homebrew/opt/flex/bin/flex' >> ~/.zshrc
source ~/.zshrc
```

## 4. Патчи для macOS совместимости

Данный репозиторий уже содержит все необходимые исправления для сборки на macOS, **за исключением одного файла в подмодуле `morph_dict`**. Подмодуль является отдельным репозиторием, поэтому изменение нужно применить вручную после инициализации подмодулей.

### 4.1 Применить патч к morph_dict

После выполнения шага 2.2 (`git submodule update --init --recursive`) примените патч:

```bash
cd $RML
git apply --directory=Source/morph_dict patches/morph_dict-common-cmakelists.patch
```

Это отключит тесты в `morph_dict/common/CMakeLists.txt`, которые вызывают ошибки на macOS.

**Что делает патч:** добавляет `if(NOT APPLE)` вокруг `add_subdirectory(tests)`.

Остальные исправления (if NOT APPLE в других CMakeLists.txt, исправления varargs, настройки Flex/Bison, libevent linking и т.д.) уже включены в данную ветку репозитория и не требуют дополнительных действий.

## 5. Конфигурация CMake

```bash
cd $RML
rm -rf build
mkdir build && cd build

RML=$RML cmake .. \
  -DCMAKE_BUILD_TYPE=Release \
  -DZLIB_LIBRARY=/opt/homebrew/Cellar/zlib/1.3.2/lib/libz.a \
  -DZLIB_INCLUDE_DIR=/opt/homebrew/Cellar/zlib/1.3.2/include
```

**Примечание:** Пути к zlib могут отличаться. Проверьте:
```bash
ls /opt/homebrew/Cellar/zlib/*/lib/libz.a
```

## 6. Сборка

```bash
cd $RML/build
RML=$RML make -j$(sysctl -n hw.ncpu)
```

**Ожидаемое время:** 5-15 минут в зависимости от системы.

## 7. Установка бинарников

Проект не имеет стандартного `make install`. Скопируйте вручную:

```bash
# Основные daemons
cp Source/www/SynanDaemon/SynanDaemon $RML/Bin/
cp Source/www/SemanDaemon/SemanDaemon $RML/Bin/

# Другие полезные утилиты (опционально)
cp Source/morph_dict/morph_gen/morph_gen $RML/Bin/
cp Source/dicts/StructDictLoader/StructDictLoader $RML/Bin/
cp Source/dicts/BinaryDictsClient/BinaryDictsClient $RML/Bin/
```

## 8. Генерация Bigrams данных (требуется для SynanDaemon)

### 8.1 Создание bigrams из текстов
```bash
RML=$RML $RML/build/Source/dicts/Bigrams/Text2Bigrams/Text2Bigrams \
  --language Russian \
  --input-file-list <(find $RML/Texts -name "*.txt" | tr '\n' '\0' | xargs -0 -I {} echo {}) \
  --output-folder $RML/Dicts/Bigrams \
  --window-size 1 \
  --max-memory 500000
```

### 8.2 Построение индекса
```bash
RML=$RML $RML/build/Source/dicts/Bigrams/BigramsIndex/BigramsIndex $RML/Dicts/Bigrams/
```

Проверьте созданные файлы:
```bash
ls -la $RML/Dicts/Bigrams/*.bin* $RML/Dicts/Bigrams/*.wrd_idx
```

## 9. Запуск daemons

### 9.1 Запуск вручную
```bash
cd $RML

# SemanDaemon (семантический анализатор)
RML=$RML nohup ./Bin/SemanDaemon --host 127.0.0.1 --port 8081 > Bin/seman.log 2>&1 &

# SynanDaemon (синтаксический анализатор)
RML=$RML nohup ./Bin/SynanDaemon --host 127.0.0.1 --port 8082 > Bin/synan.log &

# Проверка процессов
ps aux | grep -E "SemanDaemon|SynanDaemon" | grep -v grep
```

### 9.2 Через скрипты (требует исправления BOM)
Файл `Bin/start_aot.sh` имеет BOM. Исправьте:
```bash
# Создайте новый скрипт без BOM
cat > $RML/Bin/start_aot_fixed.sh << 'EOF'
#!/bin/bash
nohup bash $RML/Bin/run_seman.sh > $RML/Bin/run_seman.log &
nohup bash $RML/Bin/run_synan.sh > $RML/Bin/run_synan.log &
EOF
chmod +x $RML/Bin/start_aot_fixed.sh
```

Или просто используйте команды из п.9.1.

### 9.3 Проверка работы
```bash
# Проверка логов
tail -f $RML/Bin/seman.log
tail -f $RML/Bin/synan.log

# HTTP запросы (должны возвращать ошибку "cannot find action" — это нормально)
curl http://127.0.0.1:8081/status
curl http://127.0.0.1:8082/status
```

## 10. Остановка daemons
```bash
pkill -f SemanDaemon
pkill -f SynanDaemon
```

## 11. Возможные проблемы и решения

### 11.1 Ошибка "environment variable RML is not set"
Убедитесь, что переменная RML установлена в окружении **перед** запуском cmake и make:
```bash
export RML=/полный/путь/to/aot
```

### 11.2 Ошибка linking "library 'crt0.o' not found"
Это исправлено патчами — тесты отключены на macOS.

### 11.3 Ошибка "cannot pass object of non-trivial type 'std::string' through variadic constructor"
Применены патчи в указанных файлах. Если ошибка осталась — проверьте, что все `.c_str()` добавлены.

### 11.4 Ошибка "FlexLexer.h" несовместимости
Мы используем flex из Homebrew. Убедитесь, что `include_directories(/opt/homebrew/opt/flex/include)` добавлен в `Source/CMakeLists.txt`.

### 11.5 Libevent linking errors
Добавьте `link_directories(${LIBEVENT_LIBRARY_DIR} /opt/homebrew/lib)` в `Source/www/CMakeLists.txt`.

### 11.6 SynanDaemon падает с "Cannot open ... bigrams.txt.wrd_idx"
Запустите шаги 8.1 и 8.2 для генерации bigrams данных.

### 11.7 Daemons не стартуют с "No such file or directory"
Убедитесь, что:
1. Библиотеки libevent найдены: `ls /opt/homebrew/lib/libevent.*`
2. RML установлен правильно
3. Исполняемые файлы имеют права: `chmod +x Bin/SemanDaemon Bin/SynanDaemon`

## 12. Проверка работоспособности

### 12.1 Проверка портов
```bash
lsof -i :8081
lsof -i :8082
```

### 12.2 Проверка ответа (ожидается ошибка 404 или подобная)
```bash
curl -v http://127.0.0.1:8081/
curl -v http://127.0.0.1:8082/
```

В логах должно быть:
```
INFO  [TRMLHttpServer::Start@84] run message loop for daemon, start listen socket
INFO  [TRMLHttpServer::OnHttpRequest@103] /
ERROR [TRMLHttpServer::OnHttpRequest@136] Error: cannot find action Request: /
```

Это значит daemon работает, но endpoint '/' не реализован (нужны конкретные API вызовы).

## 13. API запросы

### 13.1 SynanDaemon (порт 8082)

Синтаксический и морфологический анализатор. Поддерживает три действия:

#### 13.1.1 Морфологический разбор (`action=morph`)
Возвращает все возможные морфологические интерпретации слова.

**Параметры:**
- `langua` — язык: `Russian`, `German`, `English`
- `query` — слово или словосочетание
- `action=morph`

**Пример:**
```bash
curl -G --data-urlencode "action=morph" \
     --data-urlencode "langua=Russian" \
     --data-urlencode "query=машина" \
     http://127.0.0.1:8082/
```

**Ответ (JSON):**
```json
[
  {
    "found": true,
    "commonGrammems": "но",
    "wordForm": "МАШИНА",
    "srcNorm": "НЕУБИВАЙМЕНЯ",
    "morphInfo": "С ср,жр,мр,пр,тв,вн,дт,рд,им,ед,мн",
    "wordWeight": 1484,
    "homonymWeight": 0
  }
]
```

#### 13.1.2 Синтаксический разбор (`action=syntax`)
Возвращает синтаксическую структуру предложения (только для русского и немецкого).

**Параметры:**
- `langua` — `Russian` или `German`
- `query` — предложение
- `action=syntax`

**Пример:**
```bash
curl -G --data-urlencode "action=syntax" \
     --data-urlencode "langua=Russian" \
     --data-urlencode "query=Я иду домой" \
     http://127.0.0.1:8082/
```

**Ответ (JSON):** массив объектов с полями `words`, `variants`, `groups`.

#### 13.1.3 Связанные слова (биграмы) (`action=bigrams`)
Находит слова, которые часто встречаются вместе с заданным.

**Параметры:**
- `langua` — `Russian`
- `query` — слово
- `minBigramsFreq` — минимальная частота (целое число, например 10)
- `sortMode` — сортировка: `freq` (по частоте) или `mi` (по mutual information)
- `action=bigrams`

**Пример:**
```bash
curl -G --data-urlencode "action=bigrams" \
     --data-urlencode "langua=Russian" \
     --data-urlencode "query=слово" \
     --data-urlencode "minBigramsFreq=10" \
     --data-urlencode "sortMode=freq" \
     http://127.0.0.1:8082/
```

### 13.2 SemanDaemon (порт 8081)

Семантический анализатор и переводчик с русского на английский.

#### 13.2.1 Перевод (`action=translate`)
Переводит русское предложение на английский.

**Параметры:**
- `langua` — `Russian` (источник)
- `query` — текст для перевода
- `topic` — тема/домен (например: `common`, `science`, `law`). Влияет на выбор лексики.
- `action=translate`

**Пример:**
```bash
curl -G --data-urlencode "action=translate" \
     --data-urlencode "langua=Russian" \
     --data-urlencode "query=Мама мыла раму" \
     --data-urlencode "topic=common" \
     http://127.0.0.1:8081/
```

**Ответ:**
```json
{"translation": "Mam washed frame."}
```

#### 13.2.2 Семантический граф (`action=graph`)
Строит семантический граф предложения с узлами и ребрами.

**Параметры:**
- `langua` — `Russian`
- `query` — предложение (до ~150 символов, остальное обрезается)
- `topic` — домен (например `common`)
- `action=graph`

**Пример:**
```bash
curl -G --data-urlencode "action=graph" \
     --data-urlencode "langua=Russian" \
     --data-urlencode "query=Мама мыла раму" \
     --data-urlencode "topic=common" \
     http://127.0.0.1:8081/
```

**Ответ (JSON):**
```json
{
  "nodes": [
    {"x":172,"y":140,"label":"МАМА","morph":"МАМА =   С од,жр,им,ед,\nSynWordNo = 0\nWordWeight = 1480"},
    {"x":225,"y":80,"label":"МЫЛА","morph":"МЫТЬ =   Г дст,пе,нс,прш,жр,ед,\nSynWordNo = 1\nWordWeight = 173"},
    {"x":277,"y":140,"label":"РАМУ","morph":"РАМА =   С но,жр,вн,ед,\nSynWordNo = 2\nWordWeight = 107"}
  ],
  "edges": [
    {"source":1,"target":0,"label":"SUB"},
    {"source":1,"target":2,"label":"OBJ"}
  ]
}
```

---

## 14. Структура Bin после сборки

```
Bin/
├── SemanDaemon          # Семантический анализатор
├── SynanDaemon          # Синтаксический анализатор
├── rml.ini              # Конфигурация (если есть)
├── Lib/                 # Динамические библиотеки (Tcl/Tk для Windows)
├── run_seman.sh         # Скрипт запуска SemanDaemon
├── run_synan.sh         # Скрипт запуска SynanDaemon
├── start_aot.sh         # Основной скрипт запуска (с BOM)
├── start_aot_fixed.sh   # Исправленная версия
├── *.txt                # Словари и данные
├── *.base               # Бинарные данные
└── *.log                # Логи после запуска
```

## 15. Clean и пересборка

```bash
# Полная очистка
rm -rf build
rm -f Bin/SemanDaemon Bin/SynanDaemon

# Пересборка
cd $RML
mkdir build && cd build
RML=$RML cmake .. -DCMAKE_BUILD_TYPE=Release -DZLIB_LIBRARY=/opt/homebrew/Cellar/zlib/1.3.2/lib/libz.a -DZLIB_INCLUDE_DIR=/opt/homebrew/Cellar/zlib/1.3.2/include
RML=$RML make -j$(sysctl -n hw.ncpu)

# Копирование и запуск
cp Source/www/SynanDaemon/SynanDaemon $RML/Bin/
cp Source/www/SemanDaemon/SemanDaemon $RML/Bin/
```

## 16. Ссылки и ресурсы

- Официальный сайт: www.aot.ru
- Документация: `Docs/Morph_UNIX.txt`
- Morphology dicts docs: `Source/morph_dict/README.md`
- Лицензия: LGPL (файл `COPYING`)

---

**Примечание:** Данная инструкция создана на основе успешной сборки от 6 мая 2026 года на macOS с Apple Silicon (ARM64). Для Intel Mac пути могут немного отличаться.
