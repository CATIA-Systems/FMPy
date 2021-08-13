cmake_minimum_required (VERSION 3.2)

project (FMUContainer)

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

if (MSVC)
  # link statically against the the Visual C runtime
  string(REPLACE "/MD"  "/MT"  CMAKE_C_FLAGS_RELEASE "${CMAKE_C_FLAGS_RELEASE}")
  string(REPLACE "/MDd" "/MTd" CMAKE_C_FLAGS_DEBUG   "${CMAKE_C_FLAGS_DEBUG}")

  # disable compiler warnings
  add_compile_definitions(_CRT_SECURE_NO_WARNINGS _CRT_NONSTDC_NO_DEPRECATE)
endif ()

add_library(FMUContainer SHARED
  ../c-code/fmi2Functions.h
  ../c-code/fmi2FunctionTypes.h
  ../c-code/fmi2TypesPlatform.h
  ../c-code/FMI.h
  ../c-code/FMI2.h
  ../c-code/FMI.c
  ../c-code/FMI2.c
  sources/FMUContainer.c
  sources/mpack.h
  sources/mpack.c
)

SET_TARGET_PROPERTIES(FMUContainer PROPERTIES PREFIX "")

target_include_directories(FMUContainer PUBLIC
  sources
  ../c-code
)

target_link_libraries(FMUContainer
  ${CMAKE_DL_LIBS}
)

add_custom_command(TARGET FMUContainer POST_BUILD COMMAND ${CMAKE_COMMAND} -E copy
  "$<TARGET_FILE:FMUContainer>"
  "${CMAKE_CURRENT_SOURCE_DIR}/binaries/${FMI_PLATFORM}"
)
