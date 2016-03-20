# Copyright (C) 2015 BROADSoftware
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
#limitations under the License.
#
import os
import argparse        
import libvirt
from easydict import EasyDict as edict
from pexpect import pxssh
import xml.etree.ElementTree as ET
import xlsxwriter
import yaml
import pprint



def ERROR(err):
    if type(err) is str:
        message = err
    else:
        message = err.__class__.__name__ + ": " + str(err)
    print "* * * * ERROR: " + str(message)
    exit(1)

def perform_ssh_cmd(ssh, cmd):
    ssh.sendline (cmd)
    ssh.prompt()
    result =  ssh.before.splitlines()
    return result
    
        
def perform_vol_stats(ssh, hostConfig):
    """Grab volume statistics from real system.
    Return an array of volumes statistics
    [ 
      { device: "/dev/sda1", size: "1000000", used: "400000", free: "600000", path: '/vol00' },
      { ...},...
    ]
    Only volumes defined in configuration file will be present, Also configuration file order is preserved
    """
    result = perform_ssh_cmd(ssh, 'df')
    foundVols = []
    for line in result[2:]:
        x =  line.split()
        vol = edict({}) 
        vol.device = x[0]
        vol.size = x[1]
        vol.used = x[2]
        vol.free = x[3]
        vol.mount = x[5]
        foundVols.append(vol)
    #print(foundVols)
    # Now loop on config.volumes to retains only configured ones, and preserve order from configuration
    volByDevice = { x.device: x for x in foundVols }
    volByMount = { x.mount: x for x in foundVols }
    result = []
    for cVolume in hostConfig.volumes:
        if 'device' in cVolume and cVolume.device in volByDevice:
            # In this case, path is not the mount point. That's means space is shared with other stuff
            vol = volByDevice[cVolume.device]
            vol.path = cVolume.path
            result.append(vol)
        elif 'path' in cVolume and cVolume.path in volByMount:
            # In this case, volume is at the mount point.
            vol = volByMount[cVolume.path]
            vol.path = cVolume.path
            result.append(vol)
        else:
            ERROR("Hosts:{0}. Volume {1} not found on real system".format(hostConfig.name, cVolume))
    return result
    
    
def perform_ls(ssh):
    result = perform_ssh_cmd(ssh, 'ls -l $(find / -path \'/vol*/**\' -type f -print 2>/dev/null)')
    print(result)

def perform_free(ssh):
    result = perform_ssh_cmd(ssh, 'free')
    print(result)

    
def perform_ssh_ops(hostConfig, hostResult):
    ssh = pxssh.pxssh()
    ssh.login(hostConfig.fqdn, hostConfig.ssh_user)
    hostResult.volumes = perform_vol_stats(ssh, hostConfig)
    #perform_ls(ssh)
    #perform_free(ssh)
    ssh.logout()
    ssh.close()
         
   
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--config', required=True)
    parser.add_argument('--dumpconfig', action='store_true')
    parser.add_argument('--dumpstats', action='store_true')

    param = parser.parse_args()
    configFile = param.config
    dumpConfig = param.dumpconfig
    dumpStats = param.dumpstats

    if dumpConfig or dumpStats:
        pp = pprint.PrettyPrinter(indent=2)

    if not os.path.isfile(configFile):
        ERROR("'{0}' is not a readable file!".format(configFile))
    config = edict(yaml.load(open(configFile)))
    if dumpConfig:
        pp.pprint(config)

    statsByHost = edict({}) 
    for hostConfig in config.hosts:
        if 'disabled' not in hostConfig or not hostConfig.disabled:
            statsByHost[hostConfig.name] = edict({}) 
            perform_ssh_ops(hostConfig,  statsByHost[hostConfig.name])
            
    if dumpStats:
        pp.pprint(statsByHost)
            


   
def main2():
    parser = argparse.ArgumentParser()
    parser.add_argument('--xxx', required=False)
    param = parser.parse_args()
    print param
    #conn = libvirt.open("qemu+ssh://root@bsa3.bsa.broadsoftware.com/system?socket=/var/run/libvirt/libvirt-sock")
    conn = libvirt.open("qemu+ssh://sa@bsa2.bsa.broadsoftware.com/system")
    domains = conn.listDomainsID()
    print domains
    domainNames = conn.listDefinedDomains()
    print domainNames
    workbook = xlsxwriter.Workbook('test1.xlsx')
    header = workbook.add_format({'bold': True, 'align': 'center'})
    worksheet = workbook.add_worksheet('Volumes')
    
    worksheet.set_column(0, 0, 10)
    worksheet.set_column(2, 2, 40)
    worksheet.write(0, 0, "VM", header)
    worksheet.write(0, 1, "Device", header)
    worksheet.write(0, 2, "File", header)
    row = 1

    for domainID in domains:
        dom = conn.lookupByID(domainID)
        print dom.name()
        
        infos = dom.info()
        print infos
        xml = dom.XMLDesc(0)
        print xml
        root = ET.fromstring(xml)
        print root
        for disk in root.findall("devices/disk"):
            print disk.attrib
            image =  disk.find("source").get("file")
            print image
            dev =  disk.find("target").get("dev")
            print dev
            worksheet.write(row, 0, str(dom.name()))
            worksheet.write(row, 1, dev)
            worksheet.write(row, 2, image)
            row += 1
            
        
        
    ssh = pxssh.pxssh()
    ssh.login ("bsa2.bsa.broadsoftware.com", "sa")
    ssh.sendline ('free ')
    ssh.prompt()
    ramString =  ssh.before
    print(ramString)

    ssh.sendline ('df -h | sort')
    ssh.prompt()
    df =  ssh.before
    print(df)

    ssh.sendline ('ls -l $(find / -path \'/vol*/**\' -type f -print 2>/dev/null)')
    ssh.prompt()
    ls =  ssh.before
    print("----------------------")
    print(ls)

    


if __name__ == "__main__":
    main()


