#!/bin/bash
if [ ! -d provisioning/$1 ]; then
  echo "playbook $1 not exist!"
  exit 1
fi

ansible-playbook --private-key=~/.vagrant.d/insecure_private_key -u vagrant -i .vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory provisioning/$1/playbook.yml
