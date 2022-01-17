cmake_minimum_required (VERSION 3.2)

project (FMPy)

set(CVODE_INSTALL_DIR "../sundials-5.3.0/win64/static/install" CACHE STRING "CVode installation directory")

if (WIN32)
    file(GLOB SUNDIALS_LIBS ${CVODE_INSTALL_DIR}/lib/*.lib)
else()
    file(GLOB SUNDIALS_LIBS ${CVODE_INSTALL_DIR}/lib/*.a)
endif()

if (MSVC)
  # link statically against the the Visual C runtime
  string(REPLACE "/MD"  "/MT"  CMAKE_C_FLAGS_RELEASE "${CMAKE_C_FLAGS_RELEASE}")
  string(REPLACE "/MDd" "/MTd" CMAKE_C_FLAGS_DEBUG   "${CMAKE_C_FLAGS_DEBUG}")

  # disable compiler warnings
  add_compile_definitions(_CRT_SECURE_NO_WARNINGS _CRT_NONSTDC_NO_DEPRECATE)
endif ()

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

add_library(logging SHARED logging/logging.c)

target_include_directories(logging PUBLIC ../fmpy/c-code)

set_target_properties(logging PROPERTIES PREFIX "")

add_custom_command(TARGET logging POST_BUILD COMMAND ${CMAKE_COMMAND} -E copy
  "$<TARGET_FILE:logging>"
  "${CMAKE_CURRENT_SOURCE_DIR}/../fmpy/logging/${FMI_PLATFORM}"
)

add_library(FMUContainer SHARED
  ../fmpy/c-code/fmi2Functions.h
  ../fmpy/c-code/fmi2FunctionTypes.h
  ../fmpy/c-code/fmi2TypesPlatform.h
  ../thirdparty/Reference-FMUs/include/FMI.h
  ../thirdparty/Reference-FMUs/include/FMI2.h
  ../thirdparty/Reference-FMUs/src/FMI.c
  ../thirdparty/Reference-FMUs/src/FMI2.c
  ../thirdparty/mpack/src/mpack/mpack.h
  ../thirdparty/mpack/src/mpack/mpack-common.c
  ../thirdparty/mpack/src/mpack/mpack-expect.c
  ../thirdparty/mpack/src/mpack/mpack-node.c
  ../thirdparty/mpack/src/mpack/mpack-platform.c
  ../thirdparty/mpack/src/mpack/mpack-reader.c
  ../thirdparty/mpack/src/mpack/mpack-writer.c
  fmucontainer/FMUContainer.c
)

SET_TARGET_PROPERTIES(FMUContainer PROPERTIES PREFIX "")

target_include_directories(FMUContainer PUBLIC
  ../fmpy/c-code
  ../thirdparty/Reference-FMUs/include
  ../thirdparty/mpack/src/mpack
  ${CVODE_INSTALL_DIR}/include
)

target_link_libraries(FMUContainer
  ${CMAKE_DL_LIBS}
  ${SUNDIALS_LIBS}
)

add_custom_command(TARGET FMUContainer POST_BUILD COMMAND ${CMAKE_COMMAND} -E copy
  "$<TARGET_FILE:FMUContainer>"
  "${CMAKE_CURRENT_SOURCE_DIR}/../fmpy/fmucontainer/binaries/${FMI_PLATFORM}"
)

add_library(cswrapper SHARED
  ../fmpy/c-code/fmi2Functions.h
  ../fmpy/c-code/fmi2FunctionTypes.h
  ../fmpy/c-code/fmi2TypesPlatform.h
  cswrapper/cswrapper.c
)

SET_TARGET_PROPERTIES(cswrapper PROPERTIES PREFIX "")

target_include_directories(cswrapper PUBLIC
  ../fmpy/c-code
  ${CVODE_INSTALL_DIR}/include
)

target_link_libraries(cswrapper
  ${SUNDIALS_LIBS}
  ${CMAKE_DL_LIBS}
)

add_custom_command(TARGET cswrapper POST_BUILD COMMAND ${CMAKE_COMMAND} -E copy
  "$<TARGET_FILE:cswrapper>"
  "${CMAKE_CURRENT_SOURCE_DIR}/../fmpy/cswrapper"
)
