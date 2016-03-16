#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info, debug
from mininet.node import Host, RemoteController

QUAGGA_DIR = '/usr/lib/quagga'
# Must exist and be owned by quagga user (quagga:quagga by default on Ubuntu)
QUAGGA_RUN_DIR = '/var/run/quagga'
QCONFIG_DIR = '/root/quagga/configs'
ZCONFIG_DIR = '/root/zebra/configs'


class SdnIpHost(Host):
    def __init__(self, name, ip, route, *args, **kwargs):
        Host.__init__(self, name, ip=ip, *args, **kwargs)

        self.route = route

    def config(self, **kwargs):
        Host.config(self, **kwargs)

        debug("configuring route %s" % self.route)

        self.cmd('ip route add default via %s' % self.route)


class Router(Host):
    def __init__(self, name, quaggaConfFile, zebraConfFile, intfDict, *args, **kwargs):
        Host.__init__(self, name, *args, **kwargs)

        self.quaggaConfFile = quaggaConfFile
        self.zebraConfFile = zebraConfFile
        self.intfDict = intfDict

    def config(self, **kwargs):
        Host.config(self, **kwargs)
        self.cmd('sysctl net.ipv4.ip_forward=1')

        for intf, attrs in self.intfDict.items():
            self.cmd('ip addr flush dev %s' % intf)

            # setup mac address to specific interface
            if 'mac' in attrs:
                self.cmd('ip link set %s down' % intf)
                self.cmd('ip link set %s address %s' % (intf, attrs['mac']))
                self.cmd('ip link set %s up ' % intf)

            # setup address to interfaces
            for addr in attrs['ipAddrs']:
                self.cmd('ip addr add %s dev %s' % (addr, intf))

        self.cmd('/usr/lib/quagga/zebra -d -f %s -z %s/zebra%s.api -i %s/zebra%s.pid' % (self.zebraConfFile, QUAGGA_RUN_DIR, self.name, QUAGGA_RUN_DIR, self.name))
        self.cmd('/usr/lib/quagga/bgpd -d -f %s -z %s/zebra%s.api -i %s/bgpd%s.pid' % (self.quaggaConfFile, QUAGGA_RUN_DIR, self.name, QUAGGA_RUN_DIR, self.name))

    def terminate(self):
        self.cmd("ps ax | egrep 'bgpd%s.pid|zebra%s.pid' | awk '{print $1}' | xargs kill" % (self.name, self.name))

        Host.terminate(self)


class SdnIpTopo(Topo):
    """
    NCTU SDN-IP tutorial topology
                                    +------+
                                    |      |
                                    |Quagga|
                                    |  02  |
                                    +-eth0-+
                                       |
          +------+                  +------+
          |      |                  |      |
      +---+  S1  +------------------+  S4  |
      |   |      |                  |      |
      |   +--+---+                  +---+--+
      |      |                          |
      +      |                          |
    Krenet   |                          |
             |                          |
             |                          |     Amlight
          +--+---+                  +---+--+     +
          |      |                  |      |     |
          |  S2  +------------------+  S3  +-----+
          |      |                  |      |
          +--+---+                  +------+
             |
          +-eth0-+
          |      |
          |Quagga|
          |  01  |
          +------+
    """

    def build(self):
        zebraConf = '{}/zebra.conf'.format(ZCONFIG_DIR)

        s1 = self.addSwitch('s1', dpid='5a90cc37aba923ab')
        s2 = self.addSwitch('s2', dpid='bfb1cc37aba9243f')
        s3 = self.addSwitch('s3', dpid='f7a6cc37aba92283')
        s4 = self.addSwitch('s4', dpid='c791cc37aba92361')
        self.addLink(s1, s2)
        self.addLink(s1, s4)
        self.addLink(s3, s2)
        self.addLink(s3, s4)

        # Internal quagga 1
        bgpq1Eth0 = {
            'mac': '00:50:56:B7:94:F5',
            'ipAddrs': [
                '134.75.108.62/30'
            ]
        }

        bgpIntfs = {
            'bgpq1-eth0': bgpq1Eth0
        }

        bgpq1 = self.addHost("bgpq1", cls=Router,
                             quaggaConfFile='%s/quagga_internal_1.conf' % CONFIG_DIR,
                             zebraConfFile=zebraConf,
                             intfDict=bgpIntfs)

        self.addLink(bgpq1, s2)

        # Internal quagga 2
        bgpq2Eth0 = {
            'mac': '00:50:56:B7:1E:6F',
            'ipAddrs': [
                '190.103.186.151/31'
            ]
        }

        bgpIntfs = {
            'bgpq2-eth0': bgpq2Eth0
        }

        bgpq2 = self.addHost("bgpq2", cls=Router,
                             quaggaConfFile='%s/quagga_internal_2.conf' % CONFIG_DIR,
                             zebraConfFile=zebraConf,
                             intfDict=bgpIntfs)

        self.addLink(bgpq2, s4)

        # KRENET Quagga
        bgpKreEth0 = {
            'mac': 'C0:FF:EE:C0:FF:EE',
            'ipAddrs': [
                '134.75.108.61/30'
            ]
        }

        bgpIntfs = {
            'bgpkre-eth0': bgpKreEth0
        }

        bgpkre = self.addHost("bgpkre", cls=Router,
                              quaggaConfFile='%s/quagga_krenet.conf' % CONFIG_DIR,
                              zebraConfFile=zebraConf,
                              intfDict=bgpIntfs)

        self.addLink(bgpkre, s1)

        # AmLight Quagga
        bgpalEth0 = {
            'mac': '00:50:56:B7:1E:6F',
            'ipAddrs': [
                '190.103.186.151/31'
            ]
        }

        bgpIntfs = {
            'bgpal-eth0': bgpalEth0
        }

        bgpal = self.addHost("bgpal", cls=Router,
                             quaggaConfFile='%s/quagga_amlight.conf' % CONFIG_DIR,
                             zebraConfFile=zebraConf,
                             intfDict=bgpIntfs)

        self.addLink(bgpal, s3)

topos = {'sdnip': SdnIpTopo}

if __name__ == '__main__':
    setLogLevel('debug')
    topo = SdnIpTopo()

    net = Mininet(topo=topo, controller=RemoteController)

    net.start()

    CLI(net)

    net.stop()

    info("done\n")
