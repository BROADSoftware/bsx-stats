
from easydict import EasyDict as edict
from pexpect import pxssh
import log

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
        """Grab volume statistics from real system.
        Return an array of volumes statistics
        [ 
          { device: "/dev/sda1", size: "1000000", used: "400000", free: "600000", path: '/vol00' },
          { ...},...
        ]
        Only volumes defined in configuration file will be present, Also configuration file order is preserved
        """
        result = self.perform_ssh_cmd('df --block-size=1K')
        foundVols = []
        for line in result[2:]:
            x =  line.split()
            vol = edict({}) 
            vol.device = x[0]
            vol.size = float(x[1])
            vol.used = float(x[2])
            vol.free = float(x[3])
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
        
        
    def perform_ls(self):
        result = self.perform_ssh_cmd('ls -l $(find / -path \'/vol*/**\' -type f -print 2>/dev/null)')
        print(result)
    
    def perform_free(self):
        result = self.perform_ssh_cmd('free')
        print(result)

