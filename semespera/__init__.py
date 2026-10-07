# Register the existing PyMySQL adapter before Django loads its MySQL backend.
import pymysql

pymysql.install_as_MySQLdb()
