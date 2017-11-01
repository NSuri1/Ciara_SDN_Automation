import subprocess
from phpIPAM import phpIPAM
import sys
import json


def get_vlan_dict(access, ip):
    """
        Get all vlans stored on switch, or router, specified by ip and access
        :param
            access: public or private access
            ip: ip address of device
        :return:
            vlan_dict: dictionary with vlan number, vlan name pairs
    """

    output = subprocess.Popen(["snmpwalk", "-v", "2c", "-c", access, "-On", ip,
                               "1.3.6.1.4.1.1991.1.1.3.2.7.1.21"],
                              stdout=subprocess.PIPE).communicate()[0]

    output = output.replace(".1.3.6.1.4.1.1991.1.1.3.2.7.1.21.", "")
    output = output.replace("STRING:", "")
    output = output.replace(" ", "")
    output = output.replace('"', "")

    vlans = output.split()

    vlan_dict = {}

    for pair in vlans:
        temp = pair.split("=")
        key = temp[0]
        value = temp[1]
        vlan_dict[int(key)] = value

    return vlan_dict


def get_phpipam_vlan_dict(ipam):
    """
           Get all vlans documented on phpipam
           :param
               ipam: valid phpipam object
           :return:
               phpipam_dict: dictionary with vlan number, vlan name pairs
                            as documented on phpipam
    """

    phpipam_list = ipam.vlan_get_all()["data"]

    phpipam_dict = {}

    for vlan in phpipam_list:
        key = vlan["number"]
        value = vlan["name"]
        phpipam_dict[int(key)] = value

    return phpipam_dict


def compare(device_vlan_dict, phpipam_dict):
    """
           Compare dict of vlans stored on device with
           dict of vlans documented in phpipam
           :param
               device_vlan_dict: dictionary of vlan numbers and
                                 names stored on device
               phpipam_dict: dictionary of vlan numbers and names
                             documented in phpipam
           :return:
               diff: dictionary of what appears in device_vlan_dict
                     but not phpipam_dict
    """

    diff = {}
    for key in device_vlan_dict:
        if key not in phpipam_dict:
            diff[key] = device_vlan_dict[key]

    return diff


def add_vlans_to_phpipam(ipam, vlans_to_add):
    """
           Document list of vlans in phpipam
           :param
               ipam: valid phpipam object
               vlans_to_add: dictionary of vlans to be documented
    """
    for vlan in vlans_to_add:
        ipam.vlan_create(vlan, vlans_to_add[vlan], "Script created vlan")


if len(sys.argv) < 2:
    access = raw_input("public or private access: ")
    ip = raw_input("ip address you would like to walk through: ")
else:
    access = sys.argv[1]
    ip = sys.argv[2]

ipam = phpIPAM("https://localhost", "user",
               "", "")

vlan_dict = get_vlan_dict(access, ip)
phpipam_dict = get_phpipam_vlan_dict(ipam)
diff_dict = compare(vlan_dict, phpipam_dict)

print(json.dumps(diff_dict, indent=4))
# add_vlans_to_phpipam(ipam, diff_dict)
