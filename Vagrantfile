# -*- mode: ruby -*-
# vi: set ft=ruby :

# ONOS + mininet + quagga
Vagrant.configure(2) do |config|

  config.vm.box = "ubuntu/xenial64"
  config.vm.hostname = "onos"
  config.vm.network "forwarded_port", guest: 8181, host: 8181
  config.vm.network "private_network", type: "dhcp"

  # Set the name of the VM. See: http://stackoverflow.com/a/17864388/100134
  config.vm.define :onos do |template|
  end

  # Use Virtual Box as provider
  config.vm.provider "virtualbox" do |vbx|
    vbx.name = "onos"
    vbx.memory = 4096
    vbx.cpus = 2
  end

  config.vm.provision "shell", inline: "sudo apt-get update -qq"
  config.vm.provision "shell", inline: "sudo apt-get install -qq python2.7"

  playbooks = [
    "basic",
    "docker",
    "onos",
    "mininet",
    "quagga",
    "sdnip",
    "gobgp",
    "ryu"
  ]

  playbooks.each do |bookname|
    config.vm.provision "ansible" do |ansible|
      ansible.playbook = "provisioning/#{bookname}/playbook.yml"
      ansible.sudo = "true"
      ansible.limit = "all"
    end
  end

 end
