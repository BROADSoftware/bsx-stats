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
from easydict import EasyDict as edict
import yaml
import pprint
import SshEngine
import log
import XlsEngine
import LibvirtEngine
import re

# Apply post info fetching processing
def enrich(stats, config):
    
    vmByVDisk = edict({})  # This map to associate vdisk file to its vm
    cfnRegex = re.compile(config.cluster_from_name_regex)
    rfnRegex = re.compile(config.role_from_name_regex)
    for host in stats.hosts:
        for vm in host.vms:
            m = cfnRegex.match(vm.name)
            if m :
                vm.cluster = m.group(1)
            m = rfnRegex.match(vm.name)
            if m :
                vm.role = m.group(1)
            for vdisk in vm.vdisks:
                vmByVDisk[vdisk.image] = vm
        
    for host in stats.hosts:
        for volume in host.volumes:
            for f in volume.files:
                if f.name in vmByVDisk:
                    vm = vmByVDisk[f.name]
                    f.vm = vm.name
                    if 'role' in vm:
                        f.role = vm.role
                    if 'cluster' in vm:
                        f.cluster = vm.cluster
                
                
   
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
            
            print("Grab libvirt info from {0}...".format(hstats.name))
            libvirt = LibvirtEngine.LibvirtEngine(hostConfig)
            hstats.vms = libvirt.grab_vms()
            hstats.vms_memory = reduce(lambda x,y:x+y, map(lambda x:(x.memory*x.running), hstats.vms))
            hstats.vms_vcpus = reduce(lambda x,y:x+y, map(lambda x:(x.vcpus*x.running), hstats.vms))
            
            stats.hosts.append(hstats)

    if dumpStats:
        pp.pprint(stats)
    
    enrich(stats, config)
    
    if dumpStats:
        pp.pprint(stats)
            
    xlsEngine = XlsEngine.XlsEngine(targetXlsName)
    xlsEngine.addHostsSheet(stats)
    xlsEngine.addPhysVolumesSheet(stats)
    xlsEngine.addFiles(stats)
    xlsEngine.addVMs(stats)




if __name__ == "__main__":
    main()


