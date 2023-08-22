##
##   ___                  __                __ 
## .'  _|.--------.--.--.|  |_.-----.-----.|  |
## |   _||        |  |  ||   _|  _  |  _  ||  |
## |__|  |__|__|__|_____||____|_____|_____||__|
## 
## 
 
 cmake_minimum_required(VERSION 3.18)
project (remoting)

set (CMAKE_C_STANDARD 99)

if ("${CMAKE_SIZEOF_VOID_P}" STREQUAL "8")
    set(FMI_PLATFORM win64)
else ()
    set(FMI_PLATFORM win32)
endif ()

message("FMI_PLATFORM: ${FMI_PLATFORM}")

if (MSVC)
  add_compile_definitions(_CRT_SECURE_NO_WARNINGS)
endif ()

#
# shared memory server
#
add_executable(server_sm
    include/fmi2Functions.h
    include/fmi2FunctionTypes.h
    include/fmi2TypesPlatform.h
    communication.c communication.h
    process.c process.h 
    remote.c remote.h
    server.c server.h
)

target_include_directories(server_sm PUBLIC include)

add_custom_command(TARGET server_sm POST_BUILD COMMAND ${CMAKE_COMMAND} -E copy
    "$<TARGET_FILE:server_sm>"
    "${CMAKE_CURRENT_SOURCE_DIR}/../fmutool/remoting/${FMI_PLATFORM}"
)


#
# shared memory client_sm #
#
add_library(client_sm SHARED
    include/fmi2Functions.h
    include/fmi2FunctionTypes.h
    include/fmi2TypesPlatform.h
	client.c client.h
    communication.c communication.h
    process.c process.h 
    remote.c remote.h
    version.h
)

target_include_directories(client_sm PRIVATE
    include
)

add_custom_command(TARGET client_sm POST_BUILD COMMAND ${CMAKE_COMMAND} -E copy
    "$<TARGET_FILE:client_sm>"
    "${CMAKE_CURRENT_SOURCE_DIR}/../fmutool/remoting/${FMI_PLATFORM}"
)


#
# test_sizeof
#
add_executable(test_sizeof
    ${CMAKE_CURRENT_SOURCE_DIR}/test_sizeof.c
    include/fmi2Functions.h
    remote.h
)

target_include_directories(test_sizeof PRIVATE
    include
)

add_custom_command(TARGET test_sizeof POST_BUILD COMMAND ${CMAKE_COMMAND} -E copy
    "$<TARGET_FILE:test_sizeof>"
    "${CMAKE_CURRENT_SOURCE_DIR}/../fmutool/remoting/${FMI_PLATFORM}"
)

add_custom_command(OUTPUT test_sizeof.c
    COMMAND python ${CMAKE_CURRENT_SOURCE_DIR}/gen_sizeof.py
    DEPENDS gen_sizeof.py
)

