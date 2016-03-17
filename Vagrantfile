# -*- mode: ruby -*-
# vi: set ft=ruby :

# ONOS + mininet + quagga
Vagrant.configure(2) do |config|

  config.vm.box = "ubuntu/trusty64"
  config.vm.hostname = "onos"
  config.vm.network "forwarded_port", guest: 8181, host: 8181

  # Set the name of the VM. See: http://stackoverflow.com/a/17864388/100134
  config.vm.define :onos do |template|
  end

  config.ssh.username = 'vagrant'
  config.ssh.password = 'vagrant'

  # Use Virtual Box as provider
  config.vm.provider "virtualbox" do |vbx|
    vbx.name = "onos"
    vbx.memory = 2048
    vbx.cpus = 4
  end
  playbooks = [
#	"basic",
#	"onos-ansible",
#	"mininet",
	"quagga"
  ]

  playbooks.each do |bookname|
	config.vm.provision "ansible" do |ansible|
      ansible.playbook = "provisioning/#{bookname}/playbook.yml"
      ansible.inventory_path = "provisioning/hosts"
      ansible.sudo = "true"
      ansible.limit = "all"
    end
  end

 end
