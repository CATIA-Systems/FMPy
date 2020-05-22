cmake_minimum_required (VERSION 3.2)

set(RPCLIB "" CACHE STRING "RPCLIB installation directory")

project (client)

if (MSVC)
  # link statically against the the Visual C runtime
  string(REPLACE "/MD"  "/MT"  CMAKE_C_FLAGS_RELEASE "${CMAKE_C_FLAGS_RELEASE}")
  string(REPLACE "/MDd" "/MTd" CMAKE_C_FLAGS_DEBUG   "${CMAKE_C_FLAGS_DEBUG}")
  add_compile_definitions(_CRT_SECURE_NO_WARNINGS)
endif ()

add_library(client SHARED
  ../../fmpy/c-code/fmi2Functions.h
  ../../fmpy/c-code/fmi2FunctionTypes.h
  ../../fmpy/c-code/fmi2TypesPlatform.h
  ../remoting.h
  client.cpp
)

target_include_directories(client PUBLIC
  "${RPCLIB}/include"
  ..
  ../../fmpy/c-code
)

target_link_libraries(client
  shlwapi.lib
  "${RPCLIB}/lib/rpc.lib"
)

add_executable(client_test
  client_test.cpp
)

target_include_directories(client_test PUBLIC
    ../../fmpy/c-code
)

add_custom_command(TARGET client POST_BUILD COMMAND ${CMAKE_COMMAND} -E copy
  "$<TARGET_FILE:client>"
  "${CMAKE_CURRENT_SOURCE_DIR}/../../fmpy/remoting"
)
