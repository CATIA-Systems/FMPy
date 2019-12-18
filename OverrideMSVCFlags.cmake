if (MSVC)
  # link statically against the Visual C runtime
  set(CMAKE_CONFIGURATION_TYPES "Debug;Release" CACHE STRING INTERNAL FORCE)
  
  set(CMAKE_C_FLAGS_RELEASE "/MT /O2 /Ob2 /DNDEBUG")
  message("Updated CMAKE_C_FLAGS_RELEASE:")
  message("${CMAKE_C_FLAGS_RELEASE}")
endif ()
