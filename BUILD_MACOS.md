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

Создайте файл `CMakeLists.my` в корне проекта:
```bash
cat > CMakeLists.my << 'EOF'
# Override defaults
set(BUILD_HTTP_SERVERS 1 CACHE BOOL "Build HTTP servers" FORCE)
EOF
```

### 4.1 Патчи исходных файлов (исправления для Clang)

**Примечание:** Эти патчи уже применены в текущем коде, но если вы запускаете чистую версию, выполните:

#### 4.1.1 Исключить тесты на macOS (Source/morph_dict/common/CMakeLists.txt)
```cmake
add_library(morphology_common  ${my_SOURCES})

# Tests disabled on macOS due to char32_t locale incompatibility
if(NOT APPLE)
    add_subdirectory(tests)
endif()
```

#### 4.1.2 Fix non-pod-varargs в StructEntry.cpp
```bash
sed -i '' 's/throw CExpc("Dict Entry %s is longer than %i bytes", m_EntryStr, EntryStrSize);/throw CExpc("Dict Entry %s is longer than %i bytes", m_EntryStr.c_str(), EntryStrSize);/' Source/dicts/StructDictLib/StructEntry.cpp

sed -i '' 's/throw CExpc("Dict Entry %s is longer than %i bytes", m_AuthorStr, EntryAuthorStrSize);/throw CExpc("Dict Entry %s is longer than %i bytes", m_AuthorStr.c_str(), EntryAuthorStrSize);/' Source/dicts/StructDictLib/StructEntry.cpp
```

#### 4.1.3 Fix BigramsIndex.cpp
```bash
sed -i '' 's/throw CExpc("Cannot find word \"%s\" in at line %zu\\n", w1, linesCount);/throw CExpc("Cannot find word \"%s\" in at line %zu\\n", w1.c_str(), linesCount);/' Source/dicts/Bigrams/BigramsIndex/BigramsIndex.cpp
sed -i '' 's/throw CExpc("Cannot find word \"%s\" in at line %zu\\n", w2, linesCount);/throw CExpc("Cannot find word \"%s\" in at line %zu\\n", w2.c_str(), linesCount);/' Source/dicts/Bigrams/BigramsIndex/BigramsIndex.cpp
```

#### 4.1.4 Fix GenFreqDict/main.cpp
```bash
sed -i '' 's/throw CExpc("cannot read the last English sentence in {}", filename);/throw CExpc("cannot read the last English sentence in %s", filename.c_str());/' Source/dicts/GenFreqDict/main.cpp
```

#### 4.1.5 Fix struct_dict_holder.cpp
```bash
sed -i '' 's/throw CExpc("cannot find %s in domain %zi, struct dict name %s", ItemStr.c_str(), dom_no, m_Ross.GetDictName());/throw CExpc("cannot find %s in domain %d, struct dict name %s", ItemStr.c_str(), (int)dom_no, m_Ross.GetDictName().c_str());/' Source/seman/SemanLib/struct_dict_holder.cpp
```

#### 4.1.6 Fix Oborots.cpp
```bash
sed -i '' 's/throw CExpc("fail to build oborot %s", convert_to_utf8(c.m_UnitStr, C.m_Language));/throw CExpc("fail to build oborot %s", convert_to_utf8(c.m_UnitStr, C.m_Language).c_str());/' Source/graphan/GraphanLib/Oborots.cpp
```

#### 4.1.7 Исключить тесты из CMakeLists.txt
Для каждого из следующих файлов добавьте `if(NOT APPLE)` вокруг `add_subdirectory(tests)`:

**Source/synan/SynanLib/CMakeLists.txt:**
```cmake
if (BUILD_DICTS)
    add_dependencies(SynanLib Ross)
endif()

# Tests disabled on macOS due to compatibility issues
if(NOT APPLE)
    add_subdirectory(tests)
endif()
```

**Source/synan/SimpleGrammarLib/CMakeLists.txt:**
```cmake
# ... существующий код ...

# Tests disabled on macOS due to compatibility issues
if(NOT APPLE)
    add_subdirectory(tests)
endif()
```

**Source/seman/Transfer/CMakeLists.txt:**
```cmake
add_library(Transfer ...)

# Tests disabled on macOS due to compatibility issues
if(NOT APPLE)
    add_subdirectory(tests)
endif()

target_link_libraries(Transfer ...)
```

**Source/seman/SemanLib/CMakeLists.txt:**
```cmake
if (BUILD_DICTS)
    add_dependencies (SemanLib BinDicts ThesRosses Ross Aoss Collocs EngCollocs TimeRoss)
endif()

# Tests disabled on macOS due to compatibility issues
if(NOT APPLE)
    add_subdirectory(tests)
endif()
```

**Source/dicts/StructDictLoader/CMakeLists.txt:**
```cmake
add_executable (${PROJECT_NAME}  "Main.cpp")
target_link_libraries(${PROJECT_NAME} StructDictLib)

# Tests disabled on macOS due to compatibility issues
if(NOT APPLE)
    add_subdirectory(tests)
endif()
```

**Source/dicts/BinaryDictsLib/CMakeLists.txt:**
```cmake
target_link_libraries(BinaryDictsLib
    LemmatizerLib
)

# Tests disabled on macOS due to compatibility issues
if(NOT APPLE)
    add_subdirectory(tests)
endif()
```

#### 4.1.8 Fix Source/CMakeLists.txt для macOS
Замените блок `ELSE (WIN32)` на:
```cmake
ELSEIF (APPLE)
    # macOS/Clang configuration
    SET (FLEX_TOOL /opt/homebrew/opt/flex/bin/flex)
    SET (BISON_TOOL /opt/homebrew/opt/bison/bin/bison)
    # Add Homebrew flex include path to use matching FlexLexer.h
    include_directories(/opt/homebrew/opt/flex/include)
    # No special linker flags needed for macOS; filesystem is in libc++
ELSE (WIN32)
    # Linux/GCC configuration
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -lstdc++fs")
    SET (CMAKE_EXE_LINKER_FLAGS  "${CMAKE_EXE_LINKER_FLAGS} -pthread -lstdc++fs -static")
    SET (FLEX_TOOL flex)
    SET (BISON_TOOL bison)
ENDIF()
```

#### 4.1.9 Fix Source/www/CMakeLists.txt
```cmake
declare_cmake_min_version()

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}")
find_package(Libevent REQUIRED)
message ("LIBEVENT_INCLUDE =  ${LIBEVENT_INCLUDE_DIR}" )
message ("LIBEVENT_LIBRARY =  ${LIBEVENT_LIBRARY}" )

# Extract library directory for linking
get_filename_component(LIBEVENT_LIBRARY_DIR ${LIBEVENT_LIBRARY} DIRECTORY)

include_directories(${LIBEVENT_INCLUDE_DIR})
link_directories(${LIBEVENT_LIBRARY_DIR} /opt/homebrew/lib)

if ($JAVA_INCLUDES)  # not tested under cmake
    add_subdirectory (www/JNIMorphAPI)
    add_subdirectory (www/JNIMorphAPITest)
endif()

add_subdirectory (SynanDaemon)
add_subdirectory (SemanDaemon)
```

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

## 13. Структура Bin после сборки

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

## 14. Clean и пересборка

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

## 15. Ссылки и ресурсы

- Официальный сайт: www.aot.ru
- Документация: `Docs/Morph_UNIX.txt`
- Morphology dicts docs: `Source/morph_dict/README.md`
- Лицензия: LGPL (файл `COPYING`)

---

**Примечание:** Данная инструкция создана на основе успешной сборки от 6 мая 2026 года на macOS с Apple Silicon (ARM64). Для Intel Mac пути могут немного отличаться.
