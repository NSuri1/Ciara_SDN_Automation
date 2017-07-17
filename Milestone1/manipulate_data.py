from elasticsearch import Elasticsearch
import pyasn
import time
import traceback
import configparser


def fill_asn():
    """ Obtain records that do not have the src_as filled in from elasticsearch.
        Lookup AS number based on IP, and update es database with new info
    """
    # Use global counter variable to keep track of how many
    # records were successfully updated.
    global counter
    # Search elasticsearch database until there are no hits matching query
    while True:
        # Query to give elasticsearch
        results = es.search(
            index='sflow*',
            body={
                'size': 10000,
                'query': {
                    'bool': {
                        'must_not': {
                            'exists': {
                                'field': 'src_as'
                            }
                        }
                    }
                }
            }
        )

        # If no matches, exit loop
        if results["hits"]["total"] is 0:
            break

        # Go through each records and lookup src_as and dst_as.
        # Then, perform update to record in database
        for hit in results['hits']['hits']:
            index = hit['_index']
            type = hit['_type']
            id = hit['_id']

            # Account for both netflow and sflow records
            if type == 'netflow':
                src_ip = hit['_source']['netflow']['ipv4_src_addr']
                src_as = hit['_source']['netflow']['src_as']
                dst_ip = hit['_source']['netflow']['ipv4_dst_addr']
                dst_as = hit['_source']['netflow']['dst_as']
            if type == 'sflow':
                src_ip = hit['_source']['sflow.srcIP']
                src_as = asndb.lookup(src_ip)[0]
                dst_ip = hit['_source']['sflow.dstIP']
                dst_as = asndb.lookup(dst_ip)[0]

            # Set src_as/dst_as to 0 if lookup returns nothing
            if src_as is None:
                src_as = 0
            if dst_as is None:
                dst_as = 0

            # Print info out
            print('-' * 80)
            print('/%s/%s/%s' % (index, type, id))
            print('Src IP: %s\tSrc AS: %s' % (src_ip, src_as))
            print('Dst IP: %s\tDst AS: %s' % (dst_ip, dst_as))

            # Update the record in es database
            es.update(index=index,
                      doc_type=type,
                      id=id,
                      body={'doc': {"src_as": src_as,
                                    "dst_as": dst_as}}
            )

            # Increment the counter
            counter += 1


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


# Change only location of the config file
config = read_config_file("../Credentials.txt")

# Location of pyasn datafile
dat_file = config.get("Pyasn", "Location")

# Elasticsearch host location
es_host = config.get('Elasticsearch', 'Hostname')

# Open elasticsearch database connection...
# Change the host to match server
es = Elasticsearch(es_host)
# Open the IP to ASN datafile...
# Again, change the datafile to match your records
asndb = pyasn.pyasn(dat_file)
# Reset counter
counter = 0

# Start timer and begin filling records
print('Filling AS numbers...')
start_time = time.time()
try:
    fill_asn()
except Exception as e:
    print('WARNING: An exception occurred...')
    traceback.print_exc()
end_time = time.time()
time_taken = end_time - start_time
print('Completed %s records in %s seconds' % (counter, time_taken))
