import configparser
config = configparser.ConfigParser()
config.read("temp.conf")
print(config)
