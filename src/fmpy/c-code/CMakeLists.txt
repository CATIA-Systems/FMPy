cmake_minimum_required (VERSION 3.15)

set (CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
set (MODEL_IDENTIFIER CACHE STRING "The model identifier")
set (INCLUDE_DIRS CACHE STRING "The include directories")
set (SOURCES CACHE STRING "The source files")
set (DEFINITIONS CACHE STRING "The preprocessor definitions")
set (TARGET_DIR CACHE STRING "The target directory")

message(STATUS "MODEL_IDENTIFIER: ${MODEL_IDENTIFIER}")
message(STATUS "INCLUDE_DIRS: ${INCLUDE_DIRS}")
message(STATUS "SOURCES: ${SOURCES}")
message(STATUS "DEFINITIONS: ${DEFINITIONS}")
message(STATUS "TARGET_DIR: ${TARGET_DIR}")

project (${MODEL_IDENTIFIER})

add_library(${MODEL_IDENTIFIER} SHARED ${SOURCES})

target_compile_definitions(${MODEL_IDENTIFIER} PUBLIC ${DEFINITIONS})

if (WIN32)
    target_compile_definitions(${MODEL_IDENTIFIER} PUBLIC
        "FMI3_Export=__declspec(dllexport)"
        "FMI3_FUNCTION_PREFIX="
    )
endif ()

target_include_directories(${MODEL_IDENTIFIER} PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${INCLUDE_DIRS}
)

set_target_properties(${MODEL_IDENTIFIER} PROPERTIES PREFIX "")

install(TARGETS ${MODEL_IDENTIFIER} DESTINATION ${TARGET_DIR})

if (MSVC)
    install(FILES $<TARGET_PDB_FILE:${MODEL_IDENTIFIER}> DESTINATION ${TARGET_DIR} OPTIONAL)
endif ()
