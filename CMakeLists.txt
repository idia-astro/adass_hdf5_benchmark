cmake_minimum_required(VERSION 3.12)
project(adass_hdf5_benchmark)

set(CMAKE_CXX_STANDARD 11)
FIND_PACKAGE(HDF5)
INCLUDE_DIRECTORIES(${HDF5_INCLUDE_DIR})
set(LINK_LIBS ${LINK_LIBS} fmt hdf5_serial hdf5_cpp hdf5_hl_cpp )
add_executable(adass_hdf5_benchmark main.cpp)
target_link_libraries(adass_hdf5_benchmark ${LINK_LIBS})