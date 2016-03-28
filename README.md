SDN-IP tutorial VM
----

This Repo Include:

- Vargent VM
- Ansible files for:
  - basic environment settings.
  - mininet, include SDN-IP sample topology script.
  - ONOS, include Karaf, Maven, Java 8.
  - quagga, include sample configuration files.

How to install:

- Clone submodules
```bash
$ git submodule update --init
```

- Start VM
```bash
$ vagrant up
```

To use:

- Connect to vm via ssh
```bash
$ vagrant ssh
```

- Switch user to root
```bash
$ sudo su
```
