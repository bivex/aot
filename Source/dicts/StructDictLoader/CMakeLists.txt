declare_cmake_min_version()

project(StructDictLoader)

add_executable (${PROJECT_NAME}  "Main.cpp")

target_link_libraries(${PROJECT_NAME}
    StructDictLib
)

# Tests disabled on macOS due to compatibility issues
if(NOT APPLE)
    add_subdirectory(tests)
endif()
