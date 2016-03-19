
import argparse        
import libvirt
from easydict import EasyDict as edict
from pexpect import pxssh
   
def main():
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
    for domainID in domains:
        dom = conn.lookupByID(domainID)
        print dom.name()
        infos = dom.info()
        print infos
        
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


if __name__ == "__main__":
    main()


