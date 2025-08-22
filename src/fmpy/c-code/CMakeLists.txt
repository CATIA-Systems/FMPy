cmake_minimum_required (VERSION 3.15)

set (CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
set (FMI_MODEL_IDENTIFIER CACHE STRING "The model identifier")
set (FMI_INCLUDE_DIRS CACHE STRING "The include directories")
set (FMI_SOURCES CACHE STRING "The source files")
set (FMI_DEFINITIONS CACHE STRING "The preprocessor definitions")
set (FMI_TARGET_DIR CACHE STRING "The target directory")
set (FMI_ALL_WARNINGS CACHE BOOL "Enable all compiler warnings")

project (${FMI_MODEL_IDENTIFIER})

add_library(${FMI_MODEL_IDENTIFIER} SHARED ${FMI_SOURCES})

target_compile_definitions(${FMI_MODEL_IDENTIFIER} PUBLIC ${FMI_DEFINITIONS})

if (WIN32)
    target_compile_definitions(${FMI_MODEL_IDENTIFIER} PUBLIC
        "FMI3_Export=__declspec(dllexport)"
        "FMI3_FUNCTION_PREFIX="
    )
endif ()

if (FMI_ALL_WARNINGS)
    if(MSVC)
      target_compile_options(${FMI_MODEL_IDENTIFIER} PRIVATE /W4)
    else()
      target_compile_options(${FMI_MODEL_IDENTIFIER} PRIVATE -Wall -Wextra -Wpedantic)
    endif()
endif ()

target_include_directories(${FMI_MODEL_IDENTIFIER} PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${FMI_INCLUDE_DIRS}
)

set_target_properties(${FMI_MODEL_IDENTIFIER} PROPERTIES PREFIX "")

install(TARGETS ${FMI_MODEL_IDENTIFIER} DESTINATION ${FMI_TARGET_DIR})

if (MSVC)
    install(FILES $<TARGET_PDB_FILE:${FMI_MODEL_IDENTIFIER}> DESTINATION ${FMI_TARGET_DIR} OPTIONAL)
endif ()
