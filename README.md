SDN-IP tutorial VM
----

This repo includes:

- Vargent VM
- Ansible files for:
  - basic environment settings.
  - mininet, include SDN-IP sample topology script.
  - ONOS, include Karaf, Maven, Java 8.
  - quagga, include sample configuration files.
  - gobgp, include sample configuration files.

Basic requirements:

- VirtualBox 5 or higher.
- 8GB memory or higher.
- 10 GB space or higher.

Topology:

Basically, we emulate SDN-IP topology from [Taiwan NCTU](http://www.nctu.edu.tw/en) peering site.

More information, see our [intro video](https://www.youtube.com/watch?v=a8LR1DyzGY4) or [slide](http://www.slideshare.net/FeiJiSiao/global-sdnip-deployment-at-nctu-taiwan)
![SDN-IP topology](https://raw.githubusercontent.com/sdnds-tw/SDN-IP-Example-VM/master/screenshots/SDNIP-Topology.jpg)
![ONOS traffic result](https://raw.githubusercontent.com/sdnds-tw/SDN-IP-Example-VM/master/screenshots/screenshot1.png)

Getting started:
See [Getting Started](https://github.com/sdnds-tw/SDN-IP-Example-VM/wiki/Getting-started)

Reference:
- [SDN-IP Global Deployment, ONS 2016](http://events.linuxfoundation.org/sites/events/files/slides/ONS%202016%20-%20S3%20Global%20deployment%20-%20mini-summit%20PDF.pdf)
- [Official wiki page](https://wiki.onosproject.org/display/ONOS/SDN-IP)
