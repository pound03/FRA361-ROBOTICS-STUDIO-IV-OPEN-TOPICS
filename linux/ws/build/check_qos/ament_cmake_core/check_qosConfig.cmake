# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_check_qos_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED check_qos_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(check_qos_FOUND FALSE)
  elseif(NOT check_qos_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(check_qos_FOUND FALSE)
  endif()
  return()
endif()
set(_check_qos_CONFIG_INCLUDED TRUE)

# output package information
if(NOT check_qos_FIND_QUIETLY)
  message(STATUS "Found check_qos: 0.0.0 (${check_qos_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'check_qos' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${check_qos_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(check_qos_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "")
foreach(_extra ${_extras})
  include("${check_qos_DIR}/${_extra}")
endforeach()
