import configparser
config = configparser.ConfigParser()
config.read('server.conf')
print(config.sections())
print(list(config["AUTHORIZED_USERS"]))
