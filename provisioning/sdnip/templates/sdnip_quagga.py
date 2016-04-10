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

ONOS_TOR_IP = '192.168.1.10/24'
Q1_TOR_IP = '192.168.1.11/24'
Q2_TOR_IP = '192.168.1.12/24'

Q1_KREONET_IP = '192.168.2.10/24'
KREONET_Q1_IP = '192.168.2.11/24'

Q2_AMLIGHT_IP = '192.168.3.10/24'
AMLIGHT_Q2_IP = '192.168.3.11/24'

AMLIGHT_INTERNAL_IP = '192.168.4.1/24'
AMLIGHT_HOST_IP = '192.168.4.10/24'

KREONET_INTERNAL_IP = '192.168.5.1/24'
KREONET_HOST_IP = '192.168.5.10/24'


class SdnIpHost(Host):
    def __init__(self, name, ip, gw, *args, **kwargs):
        Host.__init__(self, name, ip=ip, *args, **kwargs)

        self.gw = gw

    def config(self, **kwargs):
        Host.config(self, **kwargs)

        debug("configuring gateway %s" % (self.gw, ))
        self.cmd('ip route add default via %s' % (self.gw, ))


class Router(Host):
    def __init__(self, name, quaggaConfFile, zebraConfFile, intfDict, *args, **kwargs):
        Host.__init__(self, name, *args, **kwargs)

        self.quaggaConfFile = quaggaConfFile
        self.zebraConfFile = zebraConfFile
        self.intfDict = intfDict

    def config(self, **kwargs):
        Host.config(self, **kwargs)
        self.cmd('sysctl net.ipv4.ip_forward=1')

        for intf, attrs in sorted(self.intfDict.items(), key=lambda x: x[0]):
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
        tor = self.addSwitch('tor', cls=OVSKernelSwitch, failMode='standalone', dpid='0000000000000010')
        s1 = self.addSwitch('s1', dpid='0000000000000001', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s2 = self.addSwitch('s2', dpid='0000000000000002', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s3 = self.addSwitch('s3', dpid='0000000000000003', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s4 = self.addSwitch('s4', dpid='0000000000000004', cls=OVSKernelSwitch, protocols='OpenFlow13')
        self.addLink(s1, s2, port1=3, port2=3)
        self.addLink(s1, s4, port1=4, port2=4)
        self.addLink(s3, s2, port1=4, port2=4)
        self.addLink(s3, s4, port1=3, port2=3)

        # Internal quagga 1
        quagga1Intfs = {
            'quagga1-eth0': {
                'mac': '00:00:00:00:01:01',
                'ipAddrs': [
                    Q1_TOR_IP
                ]
            },
            'quagga1-eth1': {
                'mac': '00:00:00:00:01:02',
                'ipAddrs': [
                    Q1_KREONET_IP
                ]
            }
        }

        quagga1 = self.addHost("quagga1", cls=Router,
                             quaggaConfFile='%s/quagga_internal_1.conf' % QCONFIG_DIR,
                             zebraConfFile=zebraConf,
                             intfDict=quagga1Intfs)
        # eth0
        self.addLink(quagga1, tor, port1=0, port2=1)

        # eth1
        self.addLink(quagga1, s2, port1=1, port2=1)


        # Internal quagga 2
        quagga2Intfs = {
            'quagga2-eth0': {
                'mac': '00:00:00:00:02:01',
                'ipAddrs': [
                    Q2_TOR_IP
                ]
            },
            'quagga2-eth1': {
                'mac': '00:00:00:00:02:01',
                'ipAddrs': [
                    Q2_AMLIGHT_IP
                ]
            }
        }

        quagga2 = self.addHost("quagga2", cls=Router,
                             quaggaConfFile='%s/quagga_internal_2.conf' % QCONFIG_DIR,
                             zebraConfFile=zebraConf,
                             intfDict=quagga2Intfs)

        # eth0
        self.addLink(quagga2, tor, port1=0, port2=2)

        # eth1
        self.addLink(quagga2, s4, port1=1, port2=1)


        # Kreonet
        kreonetIntfs = {
            'kreonet-eth0': {
                'mac': '00:00:00:00:03:01',
                'ipAddrs': [
                    KREONET_INTERNAL_IP
                ]
            },
            'kreonet-eth1': {
                'mac': '00:00:00:00:03:02',
                'ipAddrs': [
                    KREONET_Q1_IP
                ]
            }
        }

        kreonet = self.addHost("kreonet", cls=Router,
                             quaggaConfFile='%s/quagga_kreonet.conf' % QCONFIG_DIR,
                             zebraConfFile=zebraConf,
                             intfDict=kreonetIntfs)

        self.addLink(kreonet, s1, port1=1, port2=1)

        # host behind kreonet
        k_host = self.addHost("khost", cls=SdnIpHost,
                              ip=KREONET_HOST_IP,
                              gw=KREONET_INTERNAL_IP[:-3])
        self.addLink(kreonet, k_host, port1=0, port2=0)

        # AmLight
        amlightIntfs = {
            'amlight-eth0': {
                'mac': '00:00:00:00:04:01',
                'ipAddrs': [
                    AMLIGHT_INTERNAL_IP
                ]
            },
            'amlight-eth1': {
                'mac': '00:00:00:00:04:02',
                'ipAddrs': [
                    AMLIGHT_Q2_IP
                ]
            }
        }


        amlight = self.addHost("amlight", cls=Router,
                             quaggaConfFile='%s/quagga_amlight.conf' % QCONFIG_DIR,
                             zebraConfFile=zebraConf,
                             intfDict=amlightIntfs)

        self.addLink(amlight, s3, port1=1, port2=1)

        # host behind amlight
        a_host = self.addHost("ahost", cls=SdnIpHost,
                              ip=AMLIGHT_HOST_IP,
                              gw=AMLIGHT_INTERNAL_IP[:-3])
        self.addLink(amlight, a_host, port1=0, port2=0)


topos = {'sdnip': SdnIpTopo}

if __name__ == '__main__':
    # setLogLevel('debug')
    topo = SdnIpTopo()

    net = Mininet(topo=topo, controller=None)

    net.start()
    c0 = net.addController(name='c0', controller=RemoteController, ip='127.0.0.1', port=6633)

    for i in range(1, 5):
        net.get('s%d' % i).start([c0])

    net.get('tor').cmd('ip addr add %s dev tor' % (ONOS_TOR_IP, ))
    CLI(net)
    net.stop()

    info("done\n")
