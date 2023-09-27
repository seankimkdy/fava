#!/bin/sh

# Arguments
if [ "$#" -ne 2 ]; then
	echo "Usage: $0 DEVICE BOOTCONFIG" >&2
	exit 1
fi
DEVICE_NAME=$1
BOOT_CONFIG=$2

USER=$(whoami)
HERMIT_DIR=/users/${USER}/scratch

# Setup disk
echo 'Setting up $HERMIT_DIR on $DEVICE_NAME'
if [ ! -d $HERMIT_DIR ]; then
 	mkdir -p $HERMIT_DIR
	sudo mkfs.ext4 $DEVICE_NAME
	sudo mount -t ext4 $DEVICE_NAME $HERMIT_DIR
	sudo chown $(whoami) $HERMIT_DIR
	echo "${DEVICE_NAME}\t${HERMIT_DIR}\text4\tdefaults\t0\t2" | sudo tee -a /etc/fstab > /dev/null
fi

# Install hermit
echo 'Installing hermit'
sudo apt-get update
sudo apt-get install libelf-dev

cd $HERMIT_DIR
git clone https://github.com/uclasystem/hermit.git
cd hermit/linux-5.14-rc5

cp $BOOT_CONFIG .config
sudo ./build_kernel.sh build
sudo ./build_kernel.sh install

sudo sed -i 's/GRUB_DEFAULT=0/GRUB_DEFAULT="Advanced options for Ubuntu>Ubuntu, with Linux 5.14.0-rc5"/' /etc/default/grub
sudo sed -i 's/GRUB_CMDLINE_LINUX="/GRUB_CMDLINE_LINUX="transparent_hugepage=madvise /' /etc/default/grub

sudo update-grub
