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
import xml.etree.ElementTree as ET
import yaml
import pprint
import SshEngine
import log
import XlsEngine


   
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--config', required=True)
    parser.add_argument('--dumpconfig', action='store_true')
    parser.add_argument('--dumpstats', action='store_true')

    param = parser.parse_args()
    targetXlsName = param.out
    configFile = param.config
    dumpConfig = param.dumpconfig
    dumpStats = param.dumpstats

    if dumpConfig or dumpStats:
        pp = pprint.PrettyPrinter(indent=2)

    if not os.path.isfile(configFile):
        log.ERROR("'{0}' is not a readable file!".format(configFile))
    config = edict(yaml.load(open(configFile)))
    if dumpConfig:
        pp.pprint(config)

    stats = edict({}) 
    stats.hosts = []
    
    for hostConfig in config.hosts:
        if 'disabled' not in hostConfig or not hostConfig.disabled:
            hstats = edict({}) 
            hstats.name = hostConfig.name
            print("Grab system info from {0}...".format(hstats.name))
            sshEngine = SshEngine.SshEngine(hostConfig)
            hstats.volumes = sshEngine.perform_vol_stats()
            for vol in  hstats.volumes:
                vol.files = sshEngine.perform_ls(vol.path)
                vol.sumOfFiles = reduce(lambda x,y: x+y, map(lambda x:x.size, vol.files))
            hstats.memory = sshEngine.perform_free()
            hstats.cpus = sshEngine.perform_cpu_count()
            sshEngine.close()
            stats.hosts.append(hstats)
            
    if dumpStats:
        pp.pprint(stats)
            
    xlsEngine = XlsEngine.XlsEngine(targetXlsName)
    xlsEngine.addHostsSheet(stats)
    xlsEngine.addPhysVolumesSheet(stats)
    xlsEngine.addFiles(stats)

   
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
    
    import xlsxwriter

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
            
        
    from pexpect import pxssh
        
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


