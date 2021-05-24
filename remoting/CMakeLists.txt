cmake_minimum_required (VERSION 3.2)

project (remoting)

# set(CMAKE_BUILD_TYPE Debug)

set(RPCLIB "" CACHE STRING "RPCLIB installation directory")

if (WIN32)
    if ("${CMAKE_SIZEOF_VOID_P}" STREQUAL "8")
        set(FMI_PLATFORM win64)
    else ()
        set(FMI_PLATFORM win32)
	endif ()
else ()
    set(FMI_PLATFORM linux64)
endif ()

message("FMI_PLATFORM: ${FMI_PLATFORM}")

if (MSVC)
  # link statically against the the Visual C runtime
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

  add_compile_definitions(_CRT_SECURE_NO_WARNINGS)

endif ()

# server
add_executable(server
  ../fmpy/c-code/fmi2Functions.h
  ../fmpy/c-code/fmi2FunctionTypes.h
  ../fmpy/c-code/fmi2TypesPlatform.h
  remoting.h
  server.cpp
)

set_property(TARGET server PROPERTY CXX_STANDARD 11)

target_include_directories(server PUBLIC
  ..
  ../fmpy/c-code
  "${RPCLIB}/include"
)

if (UNIX)
    target_compile_options(server PRIVATE "-pthread")
endif ()

if (WIN32)
    target_link_libraries(server
      "${RPCLIB}/lib/rpc.lib"
    )
else ()
    target_link_libraries(server
      "${RPCLIB}/lib/librpc.a"
      ${CMAKE_DL_LIBS}
      pthread
    )
endif ()

add_custom_command(TARGET server POST_BUILD COMMAND ${CMAKE_COMMAND} -E copy
  "$<TARGET_FILE:server>"
  "${CMAKE_CURRENT_SOURCE_DIR}/../fmpy/remoting/${FMI_PLATFORM}"
)

if (UNIX)
    set(CMAKE_THREAD_PREFER_PTHREAD TRUE)
    set(THREADS_PREFER_PTHREAD_FLAG TRUE)
endif ()

# client
add_library(client SHARED
  ../fmpy/c-code/fmi2Functions.h
  ../fmpy/c-code/fmi2FunctionTypes.h
  ../fmpy/c-code/fmi2TypesPlatform.h
  remoting.h
  client.cpp
)

set_property(TARGET client PROPERTY CXX_STANDARD 11)
set_target_properties(client PROPERTIES LINK_SEARCH_START_STATIC 1)
set_target_properties(client PROPERTIES LINK_SEARCH_END_STATIC 1)

set_target_properties(client PROPERTIES
    PREFIX ""
)

if (UNIX)
    set(CMAKE_FIND_LIBRARY_SUFFIXES ".a")
    set(CMAKE_EXE_LINKER_FLAGS "-static-libgcc -static-libstdc++")
    find_package(Threads REQUIRED)
endif()

target_include_directories(client PRIVATE
  ..
  ../fmpy/c-code
  "${RPCLIB}/include"
)

if (WIN32)
    target_link_libraries(client
      "${RPCLIB}/lib/rpc.lib"
    )
else ()
    target_link_libraries(client
      "${RPCLIB}/lib/librpc.a"
      Threads::Threads
    )
endif ()

add_custom_command(TARGET client POST_BUILD COMMAND ${CMAKE_COMMAND} -E copy
  "$<TARGET_FILE:client>"
  "${CMAKE_CURRENT_SOURCE_DIR}/../fmpy/remoting/${FMI_PLATFORM}"
)

# client test
add_executable(client_test
  client_test.cpp
)

set_property(TARGET client_test PROPERTY CXX_STANDARD 11)

target_include_directories(client_test PUBLIC
  ../fmpy/c-code
)

target_link_libraries(client_test
  ${CMAKE_DL_LIBS}
)
