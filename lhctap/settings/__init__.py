# Configurar PyMySQL como driver MySQL se disponível
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

