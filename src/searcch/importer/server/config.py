
#
# The importer already has a config file, so we do not do things the usual
# Flask way.  We import these flask-specific config bits from our config file.
#

class Config(object):
    """
    Common configurations
    """
    API_VERSION = 1
    APPLICATION_ROOT = '/v{}'.format(API_VERSION)
    # The secret key a caller must include in the X-Api-Key header on all calls
    # to us.  This is set through our config file, and if left blank, is
    # auto-generated.
    SECRET_KEY = ""


class DevelopmentConfig(Config):
    """
    Development configurations
    """
    TESTING = True
    DEBUG = True
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True


class ProductionConfig(Config):
    """
    Production configurations
    """
    TESTING = False
    DEBUG = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

app_config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}
