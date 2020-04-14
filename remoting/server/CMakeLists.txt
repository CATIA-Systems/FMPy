cmake_minimum_required (VERSION 3.2)

set (MODEL_NAME server)

project (server)

set(RPCLIB "" CACHE STRING "RPCLIB installation directory")

if (MSVC)
  # link statically against the the Visual C runtime
  string(REPLACE "/MD"  "/MT"  CMAKE_C_FLAGS_RELEASE "${CMAKE_C_FLAGS_RELEASE}")
  string(REPLACE "/MDd" "/MTd" CMAKE_C_FLAGS_DEBUG   "${CMAKE_C_FLAGS_DEBUG}")
  add_compile_definitions(_CRT_SECURE_NO_WARNINGS)
endif ()

add_executable(server
  ../../fmpy/c-code/fmi2Functions.h
  ../../fmpy/c-code/fmi2FunctionTypes.h
  ../../fmpy/c-code/fmi2TypesPlatform.h
  ../remoting.h
  server.cpp
)

target_include_directories(server PUBLIC
  ..
  ../../fmpy/c-code
  ../rpclib-2.2.1/include
  "${RPCLIB}/include"
)

target_link_libraries(server
  shlwapi.lib
  "${RPCLIB}/lib/rpc.lib"
)

add_custom_command(TARGET server POST_BUILD COMMAND ${CMAKE_COMMAND} -E copy
  "$<TARGET_FILE:server>"
  "${CMAKE_CURRENT_SOURCE_DIR}/../../fmpy/remoting"
)
