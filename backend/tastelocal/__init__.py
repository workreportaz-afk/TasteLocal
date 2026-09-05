# PyMySQL is used instead of mysqlclient (see requirements.txt) because
# mysqlclient requires compiling C extensions, which needs Microsoft Visual
# C++ Build Tools on Windows and isn't needed for a project this size.
# This shim makes PyMySQL present itself as the MySQLdb module Django expects.
import pymysql

pymysql.install_as_MySQLdb()
