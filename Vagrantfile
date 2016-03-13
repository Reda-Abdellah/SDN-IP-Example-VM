# -*- mode: ruby -*-
# vi: set ft=ruby :

# ONOS + mininet + quagga
Vagrant.configure(2) do |config|

  config.vm.box = "ubuntu/trusty64"
  config.vm.hostname = "onos"
  config.vm.network "private_network", ip: "10.0.0.10", netmask: "255.255.255.0"

  # Set the name of the VM. See: http://stackoverflow.com/a/17864388/100134
  config.vm.define :onos do |template|
  end

  config.ssh.username = 'vagrant'
  config.ssh.password = 'vagrant'

  # Use Virtual Box as provider
  config.vm.provider "virtualbox" do |vbx|
    vbx.name = "onos"
    vbx.memory = 1024
    vbx.cpus = 1
  end

end
