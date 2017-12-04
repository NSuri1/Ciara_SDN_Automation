#!/usr/bin/python

from elasticsearch import Elasticsearch, client
from datetime import date, timedelta
import configparser


def read_config_file(config_file):
    """
    Create an instance of configparser to read config file
    :param config_file: location of config file
    :return: ConfigParser object
    """

    # Get necessary credentials from ini file
    config = configparser.ConfigParser()
    try:
        with open(config_file) as f:
            config.read_file(f)
    except Exception as err:
        print err

    return config


def backup_yesterday():
    REPOSITORY_NAME = 'test_backup'
    yesterday = (date.today() - timedelta(1)).strftime('%Y.%m.%d')
    snapshot_client.verify_repository(repository=REPOSITORY_NAME)
    print("Repository verified, starting to create a snapshot " +
          "of the index now.")
    snapshot_client.create(repository=REPOSITORY_NAME, snapshot=yesterday,
                           body={
                                "indices": "sflow-%s" % yesterday,
                                "ignore_unavailable": True,
                                "include_global_state": False
                            },
                           wait_for_completion=False)

# Change only location of the config file
config = read_config_file("../Credentials.txt")

# Elasticsearch host location
es_host = config.get('Elasticsearch', 'Hostname')

# Open elasticsearch database connection...
# Change the host to match server
es = Elasticsearch(es_host)
snapshot_client = client.SnapshotClient(es)

log_location ="{LOG_LOCATION}"

try:
    backup_yesterday()
    with open(log_location, "a") as log:
        log.write("%s: Started backup process.\n" % date.today())
except Exception as e:
    with open(log_location, "a") as log:
        log.write("%s: WARNING: An exception occurred...\n" % date.today())
        log.write("%s\n" % str(e))
