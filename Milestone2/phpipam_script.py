from phpIPAM import phpIPAM
from elasticsearch import Elasticsearch
from elasticsearch import helpers
import sys
import datetime
import configparser


def get_commodity_vlan_ids(ipam):
    """
    Get a list of all commodity vlan ids
    :param ipam: phpIPAM object
    :return: list of commodity vlan ids
    """

    vlan_list = ipam.vlan_get_all()
    commodity_vlan_ids = []

    try:
        vlan_list = vlan_list["data"]
        for vlan in vlan_list:
            if int(vlan["isAcademic"]) is 0:
                commodity_vlan_ids.append(int(vlan["number"]))
        return commodity_vlan_ids
    except Exception as e:
        print("FAILURE: %s" % e)


def get_academic_vlan_ids(ipam):
    """
    Get a list of all academic vlan ids
    :param ipam: phpIPAM object
    :return: list of academic vlan ids
    """

    vlan_list = ipam.vlan_get_all()
    academic_vlan_ids = []

    try:
        vlan_list = vlan_list["data"]
        for vlan in vlan_list:
            if int(vlan["isAcademic"]) is 1:
                academic_vlan_ids.append(int(vlan["number"]))
        return academic_vlan_ids
    except Exception as e:
        print("FAILURE: %s" % e)


def query_body_builder(commodity_vlan_ids, is_academic):
    """
    Create the query body to pass on to elasticsearch object
    :param commodity_vlan_ids: list of commodity vlan ids
    :param is_academic: boolean for academic or commodity vlan
            records wanted
    :return: completed query body to send to elasticsearch
    """

    # If list of vlan ids is empty, do nothing
    if not commodity_vlan_ids and not is_academic:
        print("Commodity Vlan Ids list is empty...")
        return None

    # Basic query skeleton
    query = {
        "query": {
            "bool": {
            }
        }
    }

    # Add each id from list to term and build a snippet
    query_snippet = []
    for id in commodity_vlan_ids:
        term = ({"term": {"sflow.in_vlan": id}})
        query_snippet.append(term)

    # Add snippet to skeleton to make complete query body
    # For now, the list being passed is commodity vlan ids,
    # So if you want academic records, filter out commodity vlan ids,
    # Otherwise filter only for those ids
    if is_academic is True:
        # Only want sflow records
        query["query"]["bool"] = {"must": {"type": {"value": "sflow"}},
                                  "must_not": query_snippet}
    else:
        # Only want sflow records
        query["query"]["bool"] = {"must": {"type": {"value": "sflow"}},
                                  "should": query_snippet}

    # Return the query object
    return query


def index_name_generator(is_academic):
    """
    Generate a name for new index
    :param is_academic: boolean for command line arg
    requesting academic or commodity records
    :return: new index name
    """

    counter = 0
    if is_academic is True:
        name = "academic-sflow-records-%s%s" % \
               (datetime.datetime.now().strftime("%Y.%m.%d"), counter)
    else:
        name = "commodity-sflow-records-%s%s" % \
               (datetime.datetime.now().strftime("%Y.%m.%d"), counter)

    # If the index already exists, increase the last number by 1
    while es.indices.exists(index=name):
        counter += 1
        name = name[:-1]
        name += str(counter)

    return name


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


# Change only location of the config file
config = read_config_file("../Credentials.txt")

# Username and Password for phpIPAM
username = config.get("phpIPAM", "Username")
password = config.get("phpIPAM", "Password")

# Elasticsearch host location
es_host = config.get('Elasticsearch', 'Hostname')

# Open phpIPAM database connection
# Enter username and password as parameters
ipam = phpIPAM("https://apps.amlight.net/phpipam", "amlight",
               username, password)

# Open elasticsearch database connection...
# Change the host to match server
es = Elasticsearch([es_host])

# Variable assignment for later use
# User desired academic or commodity vlans
is_academic = False if "-c" in sys.argv else True

# List of commodity vlan ids
vlan_ids = get_commodity_vlan_ids(ipam)

# Elasticsearch query param
query = query_body_builder(vlan_ids, is_academic)

# Perform reindex of docs satisfying query on database
if query is None:
    print("Query object null")
    exit()

# Create name for new index
index_name = index_name_generator(is_academic)

# Reindex
print("Starting reindex process...")
print("New index name: %s" % index_name)

helpers.reindex(client=es, source_index="sflow*",
                target_index=index_name, query=query)

print("Finished reindex process")
