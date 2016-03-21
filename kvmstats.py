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
    # First job is to enrich hosts.volumes.files with VM info 
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
                        
    # Now, we need to enrich hosts.vms.vdisks with size info
    sizeByFile = edict({})
    volumeByFile = edict({})
    for host in stats.hosts:
        for volume in host.volumes:     
            for f in volume.files:
                sizeByFile[f.name] = f.size
                volumeByFile[f.name] = volume.path
    for host in stats.hosts:
        for vm in host.vms:
            for vdisk in vm.vdisks:
                vdisk.size = sizeByFile[vdisk.image]
                vdisk.volume = volumeByFile[vdisk.image]
             
            
                        
                        

def buildPlanningClusterLine(stats, config):
    cluster = edict({})
    cluster.hosts = edict({})
    for host in stats.hosts:
        cluster.hosts[host.name] = edict({})
        cluster.hosts[host.name].ram = 0
        cluster.hosts[host.name].vcpus = 0
        cluster.hosts[host.name].storage = 0
        cluster.hosts[host.name].storageByVolume = edict({})
        for volume in host.volumes:
            cluster.hosts[host.name].storageByVolume[volume.path] = 0
        
        
    return cluster


def buildPlanning(stats, config):
    """Produce hash of cluster, with in each a map of host with ram/cpu/disk consumption.
    Also, two special cluster:
    base: which hold non-VM system resources
    other: which hold resources consumed by isolated VMs
    """
    clusterSet = set()
    for host in stats.hosts:
        for vm in host.vms:
            if 'cluster' in vm:
                clusterSet.add(vm.cluster)
            
    planning = edict({})
    planning.clusters = edict({})
    planning.clusters.base =  buildPlanningClusterLine(stats, config)
    planning.clusters.base.running = 1    # Always run
    for host in stats.hosts:
        planning.clusters.base.hosts[host.name].ram = host.system_memory
        planning.clusters.base.hosts[host.name].vcpus = 1
        for volume in host.volumes:
            planning.clusters.base.hosts[host.name].storageByVolume[volume.path] = (volume.used * 1024) - volume.sumOfFiles
        
    
    planning.clusters.others = buildPlanningClusterLine(stats, config)
    planning.clusters.others.running = 1    # Always run
    for cl in clusterSet:
        planning.clusters[cl] = buildPlanningClusterLine(stats, config)

    for host in stats.hosts:
        for vm in host.vms:
            if 'cluster' in vm:
                cluster = planning.clusters[vm.cluster]
                cluster.hosts[host.name].ram += vm.memory
                cluster.hosts[host.name].vcpus += vm.vcpus
                if vm.running == 1:
                    cluster.running = 1     # A cluster is running if at least one VM is running (This provide pessimistic planning in case of partially running cluster
            else:
                cluster = planning.clusters.others
                if vm.running == 1: 
                    cluster.hosts[host.name].ram += vm.memory
                    cluster.hosts[host.name].vcpus += vm.vcpus
            for vdisk in vm.vdisks:
                cluster.hosts[host.name].storage += vdisk.size
                cluster.hosts[host.name].storageByVolume[vdisk.volume] += vdisk.size

    planning.clusterList = ['base', 'others']
    planning.clusterList.extend(sorted(list(clusterSet)))
    
    planning.hostList = sorted(map(lambda x: x.name, stats.hosts)) 
    
    return planning
            
                    
                
   
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--config', required=True)
    parser.add_argument('--dumpconfig', action='store_true')
    parser.add_argument('--dumpstats', action='store_true')
    parser.add_argument('--dumpplanning', action='store_true')

    param = parser.parse_args()
    targetXlsName = param.out
    configFile = param.config
    dumpConfig = param.dumpconfig
    dumpStats = param.dumpstats
    dumpPlanning = param.dumpplanning

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
            hstats.system_memory = hostConfig.system_memory_mb * (1024 * 1024)
            stats.hosts.append(hstats)

    enrich(stats, config)
    
    if dumpStats:
        pp.pprint(stats)
            
    planning = buildPlanning(stats, config)
    
    if dumpPlanning:
        pp.pprint(planning)
            
    xlsEngine = XlsEngine.XlsEngine(targetXlsName)
    xlsEngine.addHostsSheet(stats)
    xlsEngine.addPhysVolumesSheet(stats)
    xlsEngine.addFiles(stats)
    xlsEngine.addVMs(stats)
    xlsEngine.addPlanning(stats, planning)




if __name__ == "__main__":
    main()


