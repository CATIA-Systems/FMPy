cmake_minimum_required(VERSION 3.18)
project (remoting)
set(VERSION "1.0")

set (CMAKE_C_STANDARD 99)
option(BUILD_32 "Build for 32bits target" OFF)

if (WIN32)
    if ("${CMAKE_SIZEOF_VOID_P}" STREQUAL "8")
        set(FMI_PLATFORM win64)
    else ()
        set(FMI_PLATFORM win32)
	endif ()
else ()
    set(THREADS_PREFER_PTHREAD_FLAG ON)
    find_package(Threads REQUIRED)
    
    include(CheckSymbolExists)
    check_symbol_exists(sem_timedwait "semaphore.h" HAVE_SEM_TIMEDWAIT)

    if (APPLE)
        set(FMI_PLATFORM darwin64)
        # Compilation in 32 bits mode is no longer supported in MacOS 
    else ()
        if (BUILD_32)
           set(FMI_PLATFORM linux32)
           set(BITNESS "-m32")
        else ()
           set(FMI_PLATFORM linux64)
        endif ()
    endif()

endif ()

configure_file(${CMAKE_CURRENT_SOURCE_DIR}/config.h.in
    ${CMAKE_CURRENT_BINARY_DIR}/config.h)

message("FMI_PLATFORM: ${FMI_PLATFORM}")

if (MSVC)
  add_compile_definitions(_CRT_SECURE_NO_WARNINGS)
endif ()

#
# shared memory server
#
add_executable(server_sm
    communication.c communication.h
    process.c process.h 
    remote.c remote.h
    server.c server.h
    ${CMAKE_CURRENT_BINARY_DIR}/config.h
)

set_target_properties(server_sm PROPERTIES COMPILE_OPTIONS "${BITNESS}" LINK_FLAGS "${BITNESS}")
target_include_directories(server_sm PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/../fmpy/c-code
    ${CMAKE_CURRENT_BINARY_DIR})

if (UNIX)
    target_link_libraries(server_sm ${CMAKE_DL_LIBS})
    if (NOT APPLE)
        target_link_libraries(server_sm rt Threads::Threads)
    endif()
endif ()

add_custom_command(TARGET server_sm POST_BUILD COMMAND ${CMAKE_COMMAND} -E copy
    "$<TARGET_FILE:server_sm>"
    "${CMAKE_CURRENT_SOURCE_DIR}/../fmpy/remoting/${FMI_PLATFORM}"
)


#
# shared memory client_sm #
#
add_library(client_sm SHARED
	client.c client.h
    communication.c communication.h
    process.c process.h 
    remote.c remote.h
    ${CMAKE_CURRENT_BINARY_DIR}/config.h
)

set_target_properties(client_sm PROPERTIES PREFIX "" COMPILE_OPTIONS "${BITNESS}" LINK_FLAGS "${BITNESS}")

target_include_directories(client_sm PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/../fmpy/c-code
    ${CMAKE_CURRENT_BINARY_DIR})

if (UNIX AND NOT APPLE)
        target_link_libraries(client_sm rt Threads::Threads)
endif()

add_custom_command(TARGET client_sm POST_BUILD COMMAND ${CMAKE_COMMAND} -E copy
    "$<TARGET_FILE:client_sm>"
    "${CMAKE_CURRENT_SOURCE_DIR}/../fmpy/remoting/${FMI_PLATFORM}"
)


#
# test_sizeof
#
add_executable(test_sizeof
    ${CMAKE_CURRENT_SOURCE_DIR}/test_sizeof.c
    remote.h
)

target_include_directories(test_sizeof PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/../fmpy/c-code
)

add_custom_command(OUTPUT test_sizeof.c
    COMMAND python ${CMAKE_CURRENT_SOURCE_DIR}/gen_sizeof.py
    DEPENDS gen_sizeof.py
)

