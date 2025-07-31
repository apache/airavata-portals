from django.conf import settings

# Only use PyMySQL as the db driver when in a local dev environment
if settings.DEBUG:
    try:
        import pymysql

        pymysql.install_as_MySQLdb()
    except ImportError:
        pass
