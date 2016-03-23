
from easydict import EasyDict as edict
from pexpect import pxssh
import log
from x2y import k2b as k2b

class SshEngine:
    
    def __init__(self, hostConfig):
        self.hostConfig = hostConfig
        self.ssh = pxssh.pxssh()
        self.ssh.login(hostConfig.fqdn, hostConfig.ssh_user)

    
    def close(self):
        self.ssh.logout()
        self.ssh.close()
        
        
    def perform_ssh_cmd(self, cmd):
        self.ssh.sendline (cmd)
        self.ssh.prompt()
        result =  self.ssh.before.splitlines()
        return result
    
            
    def perform_vol_stats(self):
        """Grab volumes statistics from real system.
        Return an array of volumes statistics
        [ 
          { device: "/dev/sda1", size: "1000000", used: "400000", free: "600000", path: '/vol00' },
          { ...},...
        ]
        Only volumes defined in configuration file will be present, Also configuration file order is preserved
        Result are number of 1k blocks
        """
        stdout = self.perform_ssh_cmd('df --block-size=1K')
        foundVols = []
        for line in stdout[2:]:
            x =  line.split()
            vol = edict({}) 
            vol.device = x[0]
            vol.size = k2b(int(x[1]))
            vol.used = k2b(int(x[2]))
            vol.free = k2b(int(x[3]))
            vol.mount = x[5]
            foundVols.append(vol)
        #print(foundVols)
        # Now loop on config.volumes to retains only configured ones, and preserve order from configuration
        volByDevice = { x.device: x for x in foundVols }
        volByMount = { x.mount: x for x in foundVols }
        result = []
        for cVolume in self.hostConfig.volumes:
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
                log.ERROR("Hosts:{0}. Volume {1} not found on real system".format(self.hostConfig.name, cVolume))
        return result
        
        
    def perform_ls(self, path):
        """List all files in a given path (Volume in most case)
        Return an array as:
        [ { name: '/vol01/xxx/yy', size: 1111111 } ]
        Size in bytes
        """
        if not path.endswith('/'):
            path = path + '/'
            
        stdout = self.perform_ssh_cmd('ls -l $(find / -path \'' + path + '**\' -type f -print 2>/dev/null)')
        result = []
        for line in stdout[1:]:
            f = edict({}) 
            x = line.split()
            f.size = float(x[4])
            f.name = x[8]
            result.append(f)
        return result

    def perform_cpu_count(self):
        """Grab the number of cpu
        Return an int
        """
        stdout = self.perform_ssh_cmd('cat /proc/cpuinfo | grep processor | wc -l')
        line = stdout[1]
        return int(line)
        
    
    def perform_free(self):
        """Grab memory statistics from read system
        Return a double hash, as:
        { memory: { total: 11111, used: 11111, free: 22222 }, swap: { total: 11111, used: 11111, free: 22222 } }
        Result are in bytes
        """
        stdout = self.perform_ssh_cmd('free -b')
        result = edict({}) 
        
        result.ram =  edict({}) 
        x = stdout[2].split()
        result.ram.size = float(x[1])
        result.ram.used = float(x[2])
        result.ram.free = float(x[3])
        result.ram.shared = float(x[4])
        result.ram.cache = float(x[5])
        result.ram.available = float(x[6])

        result.swap = edict({})
        x = stdout[3].split()
        result.swap.size = float(x[1])
        result.swap.used = float(x[2])
        result.swap.free = float(x[3])
        
        return result 

