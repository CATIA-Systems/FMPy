#    ___                                               __   __              
#  .'  _|.--------.--.--.  .----.-----.--------.-----.|  |_|__|.-----.-----.
#  |   _||        |  |  |  |   _|  -__|        |  _  ||   _|  ||     |  _  |
#  |__|  |__|__|__|_____|  |__| |_____|__|__|__|_____||____|__||__|__|___  |
#  Copyright 2023 Renault SAS                                        |_____|
#  The remoting code is written by Nicolas.LAURENT@Renault.com. 
#  This code is released under the 2-Clause BSD license.
#

cmake_minimum_required(VERSION 3.18)
project (remoting)
set(VERSION "1.0")
set (CMAKE_C_STANDARD 99)

option(BUILD_32 "Build for 32bits target" OFF)
option(BUILD_TESTER "Build tester executbale" OFF)

if (WIN32)
    if ("${CMAKE_SIZEOF_VOID_P}" STREQUAL "8")
        set(FMI_PLATFORM win64)
    else ()
        set(FMI_PLATFORM win32)
	endif ()
else ()
    set(THREADS_PREFER_PTHREAD_FLAG ON)
    find_package(Threads REQUIRED)
    
    include(CheckFunctionExists)
    check_function_exists(semtimedop HAVE_SEMTIMEDOP)

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

# link statically against the runtime libraries
if (MSVC)
    set(variables
       CMAKE_C_FLAGS_DEBUG
       CMAKE_C_FLAGS_MINSIZEREL
       CMAKE_C_FLAGS_RELEASE
       CMAKE_C_FLAGS_RELWITHDEBINFO
       CMAKE_CXX_FLAGS_DEBUG
       CMAKE_CXX_FLAGS_MINSIZEREL
       CMAKE_CXX_FLAGS_RELEASE
       CMAKE_CXX_FLAGS_RELWITHDEBINFO
    )

    foreach(variable ${variables})
        if(${variable} MATCHES "/MD")
            string(REGEX REPLACE "/MD" "/MT" ${variable} "${${variable}}")
        endif()
    endforeach()

    message("CMAKE_CXX_FLAGS_RELEASE = ${CMAKE_CXX_FLAGS_RELEASE}")
    message("CMAKE_CXX_FLAGS_DEBUG   = ${CMAKE_CXX_FLAGS_DEBUG}")
    
    add_compile_definitions(_CRT_SECURE_NO_WARNINGS)
endif ()

if (UNIX AND NOT APPLE)
    set(CMAKE_FIND_LIBRARY_SUFFIXES ".a")
    set(CMAKE_EXE_LINKER_FLAGS "-static-libgcc -static-libstdc++")
    find_package(Threads REQUIRED)
endif()

################################################################################
#                 S H A R E D   M E M O R Y   R E M O T I N G                  #
################################################################################

#
# SERVER
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
# CLIENT
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
if (BUILD_TESTER)
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


    add_executable(test_server
        ${CMAKE_CURRENT_SOURCE_DIR}/test_server.c
    )
    target_include_directories(test_server PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/../fmpy/c-code)

    target_include_directories(test_sizeof PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/../fmpy/c-code
    )

endif ()


################################################################################
#                         T C P   R E M O T I N G                              #
################################################################################

set(RPCLIB "" CACHE STRING "RPCLIB installation directory")

#
# SERVER
# 
add_executable(server_tcp
    ../fmpy/c-code/fmi2Functions.h
    ../fmpy/c-code/fmi2FunctionTypes.h
    ../fmpy/c-code/fmi2TypesPlatform.h
    ../thirdparty/Reference-FMUs/include/FMI.h
    ../thirdparty/Reference-FMUs/include/FMI2.h
    ../thirdparty/Reference-FMUs/src/FMI.c
    ../thirdparty/Reference-FMUs/src/FMI2.c
    remoting_tcp.h
    server_tcp.cpp
)

set_property(TARGET server_tcp PROPERTY CXX_STANDARD 11)

target_include_directories(server_tcp PUBLIC
    ../thirdparty/Reference-FMUs/include
    ../fmpy/c-code
    ../src/fmucontainer
    "${RPCLIB}/include"
)

if (WIN32)
    target_link_libraries(server_tcp
      "${RPCLIB}/lib/rpc.lib"
    )
else ()
    target_link_libraries(server_tcp
      "${RPCLIB}/lib/librpc.a"
      ${CMAKE_DL_LIBS}
      Threads::Threads
    )
endif ()

add_custom_command(TARGET server_tcp POST_BUILD COMMAND ${CMAKE_COMMAND} -E copy
  "$<TARGET_FILE:server_tcp>"
  "${CMAKE_CURRENT_SOURCE_DIR}/../fmpy/remoting/${FMI_PLATFORM}"
)

#
# CLIENT
#
add_library(client_tcp SHARED
  ../fmpy/c-code/fmi2Functions.h
  ../fmpy/c-code/fmi2FunctionTypes.h
  ../fmpy/c-code/fmi2TypesPlatform.h
  remoting_tcp.h
  client_tcp.cpp
)

set_property(TARGET client_tcp PROPERTY CXX_STANDARD 11)
set_target_properties(client_tcp PROPERTIES LINK_SEARCH_START_STATIC 1)
set_target_properties(client_tcp PROPERTIES LINK_SEARCH_END_STATIC 1)

set_target_properties(client_tcp PROPERTIES PREFIX "")

target_include_directories(client_tcp PRIVATE
  ..
  ../fmpy/c-code
  ../src/fmucontainer
  "${RPCLIB}/include"
)

if (WIN32)
    target_link_libraries(client_tcp
      "${RPCLIB}/lib/rpc.lib"
    )
else ()
    target_link_libraries(client_tcp
      "${RPCLIB}/lib/librpc.a"
      Threads::Threads
    )
endif ()

add_custom_command(TARGET client_tcp POST_BUILD COMMAND ${CMAKE_COMMAND} -E copy
  "$<TARGET_FILE:client_tcp>"
  "${CMAKE_CURRENT_SOURCE_DIR}/../fmpy/remoting/${FMI_PLATFORM}"
)
