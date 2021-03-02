add_library(sqlite sqlite3.c sqlite3.h sqlite3ext.h)
target_compile_definitions(sqlite PUBLIC SQLITE_THREADSAFE=0)
target_compile_definitions(sqlite PUBLIC SQLITE_OMIT_LOAD_EXTENSION=1)