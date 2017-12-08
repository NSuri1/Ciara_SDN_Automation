#!/usr/bin/python
from elasticsearch import Elasticsearch, client
from datetime import date, timedelta
from phpIPAM import phpIPAM
import json


class ElasticQuery:
    'Class to query elasticsearch'

    def __init__(self, es_obj, ipam_obj=None):
        """
        Class constructor
        :param es_obj: Elasticsearch object
        :param ipam_obj: phpIPAM object
        """
        self.es_obj = es_obj
        self.ipam_obj = ipam_obj

    def __init__(self, hostname, ipam_obj=None):
        """
        Class constructor
        :param es_obj: Elasticsearch location string
        :param ipam_obj: phpIPAM object
        """
        self.es_obj = Elasticsearch(hostname, timeout=100)
        self.ipam_obj = ipam_obj

    def print_obj(self):
        """
        Print Elasticsearch and phpIPAM object information
        """
        print('Elasticsearch object: %s' % self.es_obj)
        print('phpIPAM object: %s' % self.ipam_obj)

    def get_es_obj(self):
        """
        Get access to Elasticsearch object directly.
        This allows you to make use of the Elasticsearch python
        API directly. For more info about the ES API, visit
        https://elasticsearch-py.readthedocs.io/en/master/api.html
        :return: Elasticsearch object
        """
        return self.es_obj

    def get_traffic(self, filter_vlans=False):
        """
        Query elasticsearch for traffic information the day prior.
        Can filter certain vlans out, in this case, filter out
        commodity vlans by setting filter_vlans to True when
        calling function
        :param filter_vlans: boolean for whether or not to
                            include commodity vlans
        :return: Yesterday's calulated traffic in terabytes
        """
        body = {
            "query": {
                "bool": {
                    "must": [{
                        "query_string": {
                            "query": "*",
                            "analyze_wildcard": True
                        }
                    }],
                    "must_not": []
                }
            },
            "size": 0,
            "aggs": {
                "1": {
                    "sum": {
                        "field": "PacketSize",
                        "script": "doc[\"PacketSize\"].value *"
                                 "doc[\"SampleRate\"].value"
                    }
                }
            }
        }

        if filter_vlans:
            vlan_list = self.get_commodity_vlan_ids(self.ipam_obj)
            body['query']['bool']['must_not'].append({
                "terms": {
                    "in_vlan": vlan_list
                }
            })

        index = 'sflow-%s' % self.get_yesterday_date()

        result = self.es_obj.search(index=index, body=body)
        return result['aggregations']['1']['value'] / 1000000000000

    def top_talkers(self):
        """
        Calculate top 100 talkers, which is defined as
        top 100 srcAS-dstAS flows ranked in descending order
        of packetSize, for the day prior
        :return: dictionary of top 100 talkers
        """
        pass

    def get_yesterday_date(self):
        return (date.today() - timedelta(1)).strftime('%Y.%m.%d')

    def get_commodity_vlan_ids(self, ipam):
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
