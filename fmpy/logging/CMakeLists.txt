cmake_minimum_required (VERSION 3.2)

project (logging)

if (MSVC)
  # link statically against the the Visual C runtime
  string(REPLACE "/MD"  "/MT"  CMAKE_C_FLAGS_RELEASE "${CMAKE_C_FLAGS_RELEASE}")
  string(REPLACE "/MDd" "/MTd" CMAKE_C_FLAGS_DEBUG   "${CMAKE_C_FLAGS_DEBUG}")
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

add_library(logging SHARED logging.c)

target_include_directories(logging PUBLIC ../c-code)

set_target_properties(logging PROPERTIES PREFIX "")

file(MAKE_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/${FMI_PLATFORM}")

add_custom_command(TARGET logging POST_BUILD COMMAND ${CMAKE_COMMAND} -E copy
  "$<TARGET_FILE:logging>"
  "${CMAKE_CURRENT_SOURCE_DIR}/${FMI_PLATFORM}"
)
