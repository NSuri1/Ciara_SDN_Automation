from es_query import ElasticQuery
import configparser
from phpIPAM import phpIPAM


def read_config_file(config_file):
    """
    Create an instance of configparser
    :param config_file: location of config file
    :return: instance of ConfigParser
    """

    # Get necessary credentials from ini file
    config = configparser.ConfigParser()
    try:
        with open(config_file) as f:
            config.read_file(f)
    except Exception as err:
        print err

    return config


config = read_config_file("./Credentials.txt")
username = config.get("phpIPAM", "Username")
password = config.get("phpIPAM", "Password")

es_location = config.get("Elasticsearch", "Hostname")

ipam = phpIPAM("https://apps.amlight.net/phpipam", "amlight",
               username, password)

test = ElasticQuery(es_location, ipam)

print(test.get_traffic(filter_vlans=True))
