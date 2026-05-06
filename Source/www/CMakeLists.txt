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
