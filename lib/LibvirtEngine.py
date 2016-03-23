
from easydict import EasyDict as edict
import libvirt
import xml.etree.ElementTree as ElementTree
from x2y import k2b as k2b

class LibvirtEngine:
    
    def __init__(self, hostConfig):
        self.hostConfig = hostConfig
        self.conn = libvirt.open(hostConfig.libvirt_connect)


    def grab_vms(self):
        """Grab information about VMs
        Return an array as:
        [ { name: hdp1_dn1, memory: 12929292292, vcpus: 4, state: 1, disks: [ { image: '/vol01/libvirt/images/xxxx.qcow2', device: 'vdb' }, {...} ] }, {...},... ]
        """
        domains = self.conn.listAllDomains()
        result = []
        for domain in domains:
            vm = edict({}) 
            vm.name = domain.name()
            vm.memory = k2b(domain.info()[1])     # Memory is provided as KB and internally handled in bytes
            vm.vcpus = domain.info()[3]
            vm.state = domain.info()[0]
            vm.running = 1 if vm.state == 1 else 0
            # Now, lookup info in xml file
            root = ElementTree.fromstring(domain.XMLDesc(0))
            vm.vdisks = []
            for disk in root.findall("devices/disk"):
                vdisk = edict({}) 
                vdisk.image =  disk.find("source").get("file")
                vdisk.image = vdisk.image.replace("//", "/")    # Normalization, as some name may start with '//' (Bug in creation)
                vdisk.device =  disk.find("target").get("dev")
                vm.vdisks.append(vdisk)
            result.append(vm)
        
        return result
            
            
        