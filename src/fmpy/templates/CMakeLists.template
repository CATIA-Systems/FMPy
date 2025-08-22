cmake_minimum_required (VERSION 3.15)

set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

set (MODEL_NAME %MODEL_NAME%)
set (MODEL_IDENTIFIER %MODEL_IDENTIFIER%)
set (FMI_VERSION %FMI_VERSION%)

project (${MODEL_NAME})

if (${FMI_VERSION} EQUAL 3)
    if (WIN32)
        set(FMI_PLATFORM windows)
    elseif (APPLE)
        set(FMI_PLATFORM darwin)
    else ()
        set(FMI_PLATFORM linux)
    endif ()

    if ("${CMAKE_SIZEOF_VOID_P}" STREQUAL "8")
        set (FMI_PLATFORM "x86_64-${FMI_PLATFORM}")
    else ()
        set (FMI_PLATFORM "x86-${FMI_PLATFORM}")
    endif ()
else ()
    if (WIN32)
        set(FMI_PLATFORM win)
    elseif (APPLE)
        set(FMI_PLATFORM darwin)
    else ()
        set(FMI_PLATFORM linux)
    endif ()

    if ("${CMAKE_SIZEOF_VOID_P}" STREQUAL "8")
        set (FMI_PLATFORM ${FMI_PLATFORM}64)
    else ()
        set (FMI_PLATFORM ${FMI_PLATFORM}32)
    endif ()
endif ()

add_library(${MODEL_IDENTIFIER} SHARED modelDescription.xml %SOURCES%)

target_compile_definitions(${MODEL_IDENTIFIER} PUBLIC %DEFINITIONS%)

if (MSVC)
    target_compile_definitions(${MODEL_IDENTIFIER} PUBLIC _CRT_SECURE_NO_WARNINGS)
endif ()

target_include_directories(${MODEL_IDENTIFIER} PUBLIC
    %INCLUDE_DIRS%
    ${CMAKE_CURRENT_SOURCE_DIR}/sources
)

set_target_properties(${MODEL_IDENTIFIER} PROPERTIES
    PREFIX ""
    RUNTIME_OUTPUT_DIRECTORY         "${CMAKE_CURRENT_SOURCE_DIR}/binaries/${FMI_PLATFORM}"
    RUNTIME_OUTPUT_DIRECTORY_DEBUG   "${CMAKE_CURRENT_SOURCE_DIR}/binaries/${FMI_PLATFORM}"
    RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_CURRENT_SOURCE_DIR}/binaries/${FMI_PLATFORM}"
    LIBRARY_OUTPUT_DIRECTORY         "${CMAKE_CURRENT_SOURCE_DIR}/binaries/${FMI_PLATFORM}"
    LIBRARY_OUTPUT_DIRECTORY_DEBUG   "${CMAKE_CURRENT_SOURCE_DIR}/binaries/${FMI_PLATFORM}"
    LIBRARY_OUTPUT_DIRECTORY_RELEASE "${CMAKE_CURRENT_SOURCE_DIR}/binaries/${FMI_PLATFORM}"
    ARCHIVE_OUTPUT_DIRECTORY         "${CMAKE_CURRENT_SOURCE_DIR}/binaries/${FMI_PLATFORM}"
    ARCHIVE_OUTPUT_DIRECTORY_DEBUG   "${CMAKE_CURRENT_SOURCE_DIR}/binaries/${FMI_PLATFORM}"
    ARCHIVE_OUTPUT_DIRECTORY_RELEASE "${CMAKE_CURRENT_SOURCE_DIR}/binaries/${FMI_PLATFORM}"
)

if (WIN32)
    # needed for Dymola FMUs
    target_link_libraries(${MODEL_IDENTIFIER} shlwapi.lib)
endif ()

add_custom_command(TARGET ${MODEL_NAME} POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E tar cfv "${CMAKE_CURRENT_SOURCE_DIR}/${MODEL_NAME}.fmu" --format=zip
    %RESOURCES%
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
)
