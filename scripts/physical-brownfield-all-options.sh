#!/bin/bash
set -ex

if [[ $# -ne 5 ]] ; then
    echo ""
    echo "Get the parameters listed below from the output of the CloudFormation template" 
    echo ""
    echo "Usage: ./physical-brownfield-all-options.sh [DeviceBucket] [DeviceKeyGreengrass] [RestAPIId] [Region] [EdgeDeviceID]"
    echo ""
    exit 1
fi

DEVICEBUCKET=$1
DEVICEKEYGREENGRASS=$2
RESTAPIID=$3
REGION=$4
EDGEDEVICEID=$5

apt update -y
# apt upgrade -y
apt install -y unzip wget curl 

addgroup --system ggc_group
adduser --system --ingroup ggc_group ggc_user
mkdir -p /greengrass
mkdir -p /greengrass/certs
cd /greengrass/certs/
wget -O root.ca.pem https://www.amazontrust.com/repository/AmazonRootCA1.pem
wget --inet4-only -O aws-iot-greengrass-keyring.deb https://d1onfpft10uf5o.cloudfront.net/greengrass-apt/downloads/aws-iot-greengrass-keyring.deb
dpkg -i aws-iot-greengrass-keyring.deb
echo "deb https://dnw9lb6lzp2d8.cloudfront.net stable main" | tee /etc/apt/sources.list.d/greengrass.list
apt update -y
apt install aws-iot-greengrass-core unzip python3.7 openjdk-8-jre -y
apt-cache madison openjdk-8-jdk
wget https://download.bell-sw.com/java/8u282+8/bellsoft-jdk8u282+8-linux-amd64.deb
apt install ./bellsoft-jdk8u282+8-linux-amd64.deb
systemctl enable greengrass.service
ln -s /usr/bin/java /usr/bin/java8
mkdir /var/sitewise 
chown ggc_user /var/sitewise
chmod 700 /var/sitewise

# Harderning Steps
# Fail 2 ban
apt install -y fail2ban
# Firewall
# ufw allow ssh
# ufw --force enable
# Shared memory
echo "none /run/shm tmpfs defaults,ro 0 0" >> /etc/fstab
# Change SSH port
#echo "Port 22" >> /etc/ssh/sshd_config
#echo "AllowUsers vagrant" >> /etc/ssh/sshd_config
#systemctl restart sshd

# Get Greengrass group cert and place in /home/ubuntu/ directory
aws s3api get-object --bucket $DEVICEBUCKET --key $DEVICEKEYGREENGRASS /home/ubuntu/group.tar.gz
tar -xzvf /home/ubuntu/group.tar.gz -C /greengrass
/greengrass/ggc/core/greengrassd start
sleep 10
wget -O /home/ubuntu/opcclient.der https://$RESTAPIID.execute-api.$REGION.amazonaws.com/api/deployggwithsitewise/$EDGEDEVICEID?ignition-ip=localhost