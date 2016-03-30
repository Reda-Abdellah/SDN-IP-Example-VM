#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info, debug
from mininet.node import Host, RemoteController, OVSKernelSwitch

QUAGGA_DIR = '/usr/lib/quagga'
# Must exist and be owned by quagga user (quagga:quagga by default on Ubuntu)
QUAGGA_RUN_DIR = '/var/run/quagga'
QCONFIG_DIR = '/root/quagga/configs'
ZCONFIG_DIR = '/root/zebra/configs'


class SdnIpHost(Host):
    def __init__(self, name, ip, gw, *args, **kwargs):
        Host.__init__(self, name, ip=ip, *args, **kwargs)

        self.gw = gw

    def config(self, **kwargs):
        Host.config(self, **kwargs)

        debug("configuring gateway %s" % self.gw)
        self.cmd('route add default gw %s', self.gw)


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
            label_num = 0
            for addr in attrs['ipAddrs']:
                self.cmd("ip addr add %s brd + dev %s label %s:%d" % (addr, intf, intf, label_num))
                label_num += 1

        self.cmd('/usr/lib/quagga/zebra -d -f %s -z %s/zebra%s.api -i %s/zebra%s.pid' % (self.zebraConfFile, QUAGGA_RUN_DIR, self.name, QUAGGA_RUN_DIR, self.name))
        self.cmd('/usr/lib/quagga/bgpd -d -f %s -z %s/zebra%s.api -i %s/bgpd%s.pid' % (self.quaggaConfFile, QUAGGA_RUN_DIR, self.name, QUAGGA_RUN_DIR, self.name))

    def terminate(self):
        self.cmd("ps ax | egrep 'bgpd%s.pid|zebra%s.pid' | awk '{print $1}' | xargs kill" % (self.name, self.name))

        Host.terminate(self)


class SdnIpTopo(Topo):
    """
    NCTU SDN-IP tutorial topology
                                   Host (onos)
                                       |
                                    +-eth0-+
                                    |      |
                                    |Quagga|
                                    |  02  |
                                    +-eth1-+
                                       |
          +------+                  +------+
          |      |                  |      |
      +---+  S1  +------------------+  S4  |
      |   |      |                  |      |
      |   +--+---+                  +---+--+
      |      |                          |
      +      |                          |
   Kreonet   |                          |
             |                          |
             |                          |     Amlight
          +--+---+                  +---+--+     +
          |      |                  |      |     |
          |  S2  +------------------+  S3  +-----+
          |      |                  |      |
          +--+---+                  +------+
             |
          +-eth1-+
          |      |
          |Quagga|
          |  01  |
          +-eth0-+
             |
         Host (onos)
    """

    def build(self):
        zebraConf = '{}/zebra.conf'.format(ZCONFIG_DIR)
        tor = self.addSwitch('tor', cls=OVSKernelSwitch, failMode='standalone', dpid='0000000000000001')
        s1 = self.addSwitch('s1', dpid='5a90cc37aba923ab', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s2 = self.addSwitch('s2', dpid='bfb1cc37aba9243f', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s3 = self.addSwitch('s3', dpid='f7a6cc37aba92283', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s4 = self.addSwitch('s4', dpid='c791cc37aba92361', cls=OVSKernelSwitch, protocols='OpenFlow13')
        self.addLink(s1, s2, port1=3, port2=3)
        self.addLink(s1, s4, port1=4, port2=4)
        self.addLink(s3, s2, port1=4, port2=4)
        self.addLink(s3, s4, port1=3, port2=3)

        # Internal quagga 1
        bgpq1Intfs = {
            'bgpq1-eth0': {
                'mac': '00:50:56:b7:3e:dd',
                'ipAddrs': [
                    '192.168.113.20/24'
                ]
            },
            'bgpq1-eth1': {
                'mac': '00:50:56:B7:94:F5',
                'ipAddrs': [
                    '10.113.1.1/30',
                    '10.113.2.1/30',
                    '134.75.108.62/30'
                ]
            }
        }

        bgpq1 = self.addHost("bgpq1", cls=Router,
                             quaggaConfFile='%s/quagga_internal_1.conf' % QCONFIG_DIR,
                             zebraConfFile=zebraConf,
                             intfDict=bgpq1Intfs)
        # eth0
        self.addLink(bgpq1, tor, port1=0, port2=0)

        # eth1
        self.addLink(bgpq1, s2, port1=1, port2=1)


        # Internal quagga 2
        bgpq2Intfs = {
            'bgpq2-eth0': {
                'mac': '00:50:56:b7:04:60',
                'ipAddrs': [
                    '192.168.113.22/24'
                ]
            },
            'bgpq2-eth1': {
                'mac': '00:50:56:b7:1e:6f',
                'ipAddrs': [
                    '10.113.1.5/30',
                    '10.113.2.5/30',
                    '190.103.186.151/31'
                ]
            }
        }

        bgpq2 = self.addHost("bgpq2", cls=Router,
                             quaggaConfFile='%s/quagga_internal_2.conf' % QCONFIG_DIR,
                             zebraConfFile=zebraConf,
                             intfDict=bgpq2Intfs)

        # eth0
        self.addLink(bgpq2, tor, port1=0, port2=1)

        # eth1
        self.addLink(bgpq2, s4, port1=1, port2=1)


        # Kreonet
        kreonetIntfs = {
            'kreonet-eth0': {
                'mac': '00:00:00:00:00:01',
                'ipAddrs': [
                    '100.0.0.1/24'
                ]
            },
            'kreonet-eth1': {
                'mac': '00:00:00:00:00:02',
                'ipAddrs': [
                    '134.75.108.61/30'
                ]
            }
        }

        kreonet = self.addHost("kreonet", cls=Router,
                             quaggaConfFile='%s/quagga_kreonet.conf' % QCONFIG_DIR,
                             zebraConfFile=zebraConf,
                             intfDict=kreonetIntfs)

        self.addLink(kreonet, s1, port1=1, port2=1)

        # AmLight
        amlightIntfs = {
            'amlight-eth0': {
                'mac': '00:00:00:00:00:01',
                'ipAddrs': [
                    '100.0.1.1/24'
                ]
            },
            'amlight-eth1': {
                'mac': '00:00:00:00:00:02',
                'ipAddrs': [
                    '134.75.108.61/30'
                ]
            }
        }

        amlight = self.addHost("amlight", cls=Router,
                             quaggaConfFile='%s/quagga_ikreonet.conf' % QCONFIG_DIR,
                             zebraConfFile=zebraConf,
                             intfDict=amlightIntfs)

        self.addLink(amlight, s1, port1=1, port2=1)


topos = {'sdnip': SdnIpTopo}

if __name__ == '__main__':
    setLogLevel('debug')
    topo = SdnIpTopo()

    net = Mininet(topo=topo, controller=None)

    net.start()
    c0 = net.addController(name='c0', controller=RemoteController, ip='127.0.0.1', port=6633)

    for i in range(1, 5):
        net.get('s%d' % i).start([c0])

    net.get('tor').cmd('ip addr add 192.168.113.10/24 dev tor')
    CLI(net)
    net.stop()

    info("done\n")
