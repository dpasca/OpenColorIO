# SPDX-License-Identifier: BSD-3-Clause
# Copyright Contributors to the OpenColorIO Project.

set(SOURCES
    main.cpp
)

add_executable(ocioperf ${SOURCES})

if(NOT BUILD_SHARED_LIBS)
    target_compile_definitions(ocioperf
        PRIVATE
            OpenColorIO_SKIP_IMPORTS
    )
endif()

set_target_properties(ocioperf PROPERTIES
    COMPILE_FLAGS "${PLATFORM_COMPILE_FLAGS}")

target_link_libraries(ocioperf
    PRIVATE
        apputils
        OpenColorIO
        utils::strings
)

install(TARGETS ocioperf
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)
