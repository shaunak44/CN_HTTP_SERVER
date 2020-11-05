import configparser
config = configparser.ConfigParser()
config.read('http.conf')
print(config.sections())
print(config["DEFAULT"]["ForwardX11"])
