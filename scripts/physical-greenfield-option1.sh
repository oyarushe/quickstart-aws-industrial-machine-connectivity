#!/bin/bash
set -ex

if [[ $# -ne 8 ]] ; then
    echo ""
    echo "Get the parameters listed below from the output of the CloudFormation template, except for the hardware's Public IP. Check the device's network." 
    echo ""
    echo "Usage: ./physical-greenfield-option1.sh [DeviceBucket] [DeviceKeyGreengrass] [RestAPIId] [Region] [EdgeDeviceID] [hardwarePublicIP] [DeviceKeyAwareDevice] [IoTEndpoint]"
    echo ""
    exit 1
fi

DEVICEBUCKET=$1
DEVICEKEYGREENGRASS=$2
RESTAPIID=$3
REGION=$4
EDGEDEVICEID=$5
HARDWAREIP=$6
DEVICEKEYGREENGRASSAD=$7 
IOTENDPOINT=$8

apt update -y
# apt upgrade -y
apt install -y awscli unzip fail2ban

# Install Greengrass
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
#ufw allow ssh
#ufw --force enable
# Shared memory
echo "none /run/shm tmpfs defaults,ro 0 0" >> /etc/fstab
# Change SSH port
#echo "Port 22" >> /etc/ssh/sshd_config
#echo "AllowUsers vagrant" >> /etc/ssh/sshd_config
#systemctl restart sshd

# Get Greengrass group certs and store as /home/ubuntu/group.tar.gz directory
aws s3api get-object --bucket $DEVICEBUCKET --key $DEVICEKEYGREENGRASS /home/ubuntu/group.tar.gz
tar -xzvf /home/ubuntu/group.tar.gz -C /greengrass
/greengrass/ggc/core/greengrassd start
sleep 10
wget -O /home/ubuntu/opcclient.der https://$RESTAPIID.execute-api.$REGION.amazonaws.com/api/deploygg/$EDGEDEVICEID

# Get Ignition automation files
# TODO: Replace imc-user-data-public-bucket with aws-quickstart? 
wget -O /home/ubuntu/Ignition-AWS-Kit-MQTT-v4.zip http://files.inductiveautomation.com/aws-imc-kit/Ignition-AWS-Kit-MQTT-v5-Physical.zip
unzip -o /home/ubuntu/Ignition-AWS-Kit-MQTT-v4.zip -d /home/ubuntu
mv /home/ubuntu/Ignition-AWS-Kit-MQTT-v4-Physical /home/ubuntu/Ignition-AWS-Kit-MQTT-v4
cd /home/ubuntu/Ignition-AWS-Kit-MQTT-v4
chmod +x install.sh

# Give AWS the ability to find and successfully deploy the Greengrass Group 
wget https://$RESTAPIID.execute-api.$REGION.amazonaws.com/api/updateconnectivity/$EDGEDEVICEID/withip/$HARDWAREIP
sleep 10
wget -O /home/ubuntu/Ignition-AWS-Kit-MQTT-v4/artifacts/opcua/opcclient.der https://$RESTAPIID.execute-api.$REGION.amazonaws.com/api/deployggwithsitewise/$EDGEDEVICEID?ignition-ip=localhost

# Get AWS IoT device certs and store as /home/ubuntu/device.tar.gz 
aws s3api get-object --bucket $DEVICEBUCKET --key $DEVICEKEYGREENGRASSAD /home/ubuntu/device.tar.gz
tar -xzvf /home/ubuntu/device.tar.gz -C /home/ubuntu/Ignition-AWS-Kit-MQTT-v4/artifacts
mv /home/ubuntu/Ignition-AWS-Kit-MQTT-v4/artifacts/certs/* /home/ubuntu/Ignition-AWS-Kit-MQTT-v4/artifacts/mqtt
rmdir /home/ubuntu/Ignition-AWS-Kit-MQTT-v4/artifacts/certs

sed -i "s/defaultclient/$EDGEDEVICEID\Device/g" /home/ubuntu/Ignition-AWS-Kit-MQTT-v4/artifacts/config.json
sed -i "s%abcdefexample-ats.iot.us-east-1.amazonaws.com%$IOTENDPOINT%g" /home/ubuntu/Ignition-AWS-Kit-MQTT-v4/artifacts/config.json

python3 /home/ubuntu/Ignition-AWS-Kit-MQTT-v4/scripts/editConfig.py

# Run installation
./install.sh
