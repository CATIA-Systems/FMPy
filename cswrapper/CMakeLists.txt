cmake_minimum_required (VERSION 3.2)

set(CVODE_INSTALL_DIR "../cvode-5.3.0/build/install" CACHE STRING "CVode installation directory")

project (cswrapper)

if (MSVC)
  # link statically against the the Visual C runtime
  string(REPLACE "/MD"  "/MT"  CMAKE_C_FLAGS_RELEASE "${CMAKE_C_FLAGS_RELEASE}")
  string(REPLACE "/MDd" "/MTd" CMAKE_C_FLAGS_DEBUG   "${CMAKE_C_FLAGS_DEBUG}")

  # disable compiler warnings
  add_compile_definitions(_CRT_SECURE_NO_WARNINGS _CRT_NONSTDC_NO_DEPRECATE)
endif ()

add_library(cswrapper SHARED
  ../fmpy/c-code/fmi2Functions.h
  ../fmpy/c-code/fmi2FunctionTypes.h
  ../fmpy/c-code/fmi2TypesPlatform.h
  cswrapper.c
)

SET_TARGET_PROPERTIES(cswrapper PROPERTIES PREFIX "")

target_include_directories(cswrapper PUBLIC
  ..
  ../fmpy/c-code
  ${CVODE_INSTALL_DIR}/include
)

if (WIN32)
    file(GLOB SUNDIALS_LIBS ${CVODE_INSTALL_DIR}/lib/*.lib)
else()
    file(GLOB SUNDIALS_LIBS ${CVODE_INSTALL_DIR}/lib/*.a)
endif()

target_link_libraries(cswrapper
  ${SUNDIALS_LIBS}
  ${CMAKE_DL_LIBS}
)

add_custom_command(TARGET cswrapper POST_BUILD COMMAND ${CMAKE_COMMAND} -E copy
  "$<TARGET_FILE:cswrapper>"
  "${CMAKE_CURRENT_SOURCE_DIR}/../fmpy/cswrapper"
)
