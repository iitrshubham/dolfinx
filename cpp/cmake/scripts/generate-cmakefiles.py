# Copyright (C) 2017-2018 Chris N. Richardson and Garth N. Wells
#
# This file is part of DOLFINX (https://www.fenicsproject.org)
#
# SPDX-License-Identifier:    LGPL-3.0-or-later

import os
import warnings

cmakelists_str = \
    """# This file is automatically generated by running
#
#     cmake/scripts/generate-cmakefiles
#
cmake_minimum_required(VERSION 3.12)

# Set C++17 standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(PROJECT_NAME {project_name})
project(${{PROJECT_NAME}})

# Get DOLFINX configuration data (DOLFINXConfig.cmake must be in
# DOLFINX_CMAKE_CONFIG_PATH)
if (NOT TARGET dolfinx)
  find_package(DOLFINX REQUIRED)
endif()

# Executable
add_executable(${{PROJECT_NAME}} {src_files})

# Target libraries
target_link_libraries(${{PROJECT_NAME}} dolfinx)

# Do not throw error for 'multi-line comments' (these are typical in
# rst which includes LaTeX)
include(CheckCXXCompilerFlag)
CHECK_CXX_COMPILER_FLAG("-Wno-comment" HAVE_NO_MULTLINE)
set_source_files_properties(main.cpp PROPERTIES COMPILE_FLAGS "$<$<BOOL:${{HAVE_NO_MULTLINE}}>:-Wno-comment -Wall -Wextra -pedantic -Werror>")

# Test targets
set(TEST_PARAMETERS2 -np 2 ${{MPIEXEC_PARAMS}} "./${{PROJECT_NAME}}")
set(TEST_PARAMETERS3 -np 3 ${{MPIEXEC_PARAMS}} "./${{PROJECT_NAME}}")
add_test(NAME ${{PROJECT_NAME}}_mpi_2 COMMAND "mpirun" ${{TEST_PARAMETERS2}})
add_test(NAME ${{PROJECT_NAME}}_mpi_3 COMMAND "mpirun" ${{TEST_PARAMETERS3}})
add_test(NAME ${{PROJECT_NAME}}_serial COMMAND ${{PROJECT_NAME}})
"""

# Subdirectories
sub_directories = ["demo"]
# Prefix map for subdirectories
executable_prefixes = dict(demo="demo_")

# Main file name map for subdirectories
main_file_names = dict(demo=set(["main.cpp"]))

# Projects that use custom CMakeLists.txt (shouldn't overwrite)
exclude_projects = []


def generate_cmake_files(subdirectory, generated_files):
    """Search for C++ code and write CMakeLists.txt files"""
    cwd = os.getcwd()
    executable_prefix = executable_prefixes[subdirectory]
    main_file_name = main_file_names[subdirectory]
    for root, dirs, files in os.walk(cwd + "/" + subdirectory):

        cpp_files = set()
        c_files = set()
        executable_names = set()

        program_dir = root
        program_name = os.path.split(root)[-1]

        skip = False
        for exclude in exclude_projects:
            if exclude in root:
                skip = True

        if skip:
            print("Skipping custom CMakeLists.txt file:", root)
            continue

        name_forms = dict(
            project_name=executable_prefix + program_name,
            src_files="NOT_SET")
        for f in os.listdir(program_dir):
            filename, extension = os.path.splitext(f)
            if extension == ".cpp":
                cpp_files.add(f)
            elif extension == ".c":
                c_files.add(f)
            elif extension == ".ufl":
                c_files.add(f.replace(".ufl", ".c"))
            if ".cpp.rst" in f:
                cpp_files.add(filename)

        # If no .cpp, continue
        if not cpp_files:
            continue

        # Name of demo and cpp source files
        assert not main_file_name.isdisjoint(cpp_files)

        # If directory contains a main file we assume that only one
        # executable should be generated for this directory and all
        # other .cpp files should be linked to this
        name_forms["src_files"] = ' '.join(cpp_files | c_files)

        # Check for duplicate executable names
        if program_name not in executable_names:
            executable_names.add(program_name)
        else:
            warnings.warn("Duplicate executable names found when generating CMakeLists.txt files.")

        # Write file
        filename = os.path.join(program_dir, "CMakeLists.txt")
        generated_files.append(filename)
        with open(filename, "w") as f:
            f.write(cmakelists_str.format(**name_forms))


# Generate CMakeLists.txt files for all subdirectories
generated_files = []
for subdirectory in sub_directories:
    generate_cmake_files(subdirectory, generated_files)

# Print list of generated files
print("The following files were generated:")
print("\n".join(generated_files))
