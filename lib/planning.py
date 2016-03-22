
from easydict import EasyDict as edict

                   

def initClusterLine(stats):
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


def build(stats, projects):
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
    planning.clusters.base =  initClusterLine(stats)
    planning.clusters.base.running = 1    # Always run
    for host in stats.hosts:
        planning.clusters.base.hosts[host.name].ram = host.system_memory
        planning.clusters.base.hosts[host.name].vcpus = 1
        for volume in host.volumes:
            planning.clusters.base.hosts[host.name].storageByVolume[volume.path] = (volume.used * 1024) - volume.sumOfFiles
        
    
    planning.clusters.others = initClusterLine(stats)
    planning.clusters.others.running = 1    # Always run
    for cl in clusterSet:
        planning.clusters[cl] = initClusterLine(stats)

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
            
                    
