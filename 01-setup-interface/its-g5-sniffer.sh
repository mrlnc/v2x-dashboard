#!/bin/bash
DRIVER_DIR="/home/merlin/src-for-11p/linux/drivers/net/wireless/ath/"

INTERFACE="wlp2s0"
MONITOR_INTERFACE=$INTERFACE-monitor

FILE="v2x_%F_%H:%M:%S.pcap"
OUTPUT_DIR="/home/merlin/PCAPs/"

echo "Unloading modules. Some errors might occur if the modules are not actually loaded."
sudo rmmod ath9k ath9k_htc ath9k_common ath9k_hw ath9k_htc ath
echo "done."

echo "Inserting patched modules."
sudo insmod $DRIVER_DIR/ath.ko
sudo insmod $DRIVER_DIR/ath9k/ath9k_hw.ko
sudo insmod $DRIVER_DIR/ath9k/ath9k_common.ko
sudo insmod $DRIVER_DIR/ath9k/ath9k_htc.ko
sudo insmod $DRIVER_DIR/ath9k/ath9k.ko
echo "done."

sleep 1

MONITOR_INTERFACE=$INTERFACE-monitor
echo "Creating monitor interface: $MONITOR_INTERFACE"
sudo iw dev $INTERFACE interface add $MONITOR_INTERFACE type monitor
echo "done."

echo "Setting interfaces to promisc mode."
sudo ip link set $INTERFACE up
sudo ip link set $MONITOR_INTERFACE up

#sudo ip link set $INTERFACE promisc on
#sudo ip link set $MONITOR_INTERFACE promisc on
echo "done."

echo "Setting OCB mode"
sudo iw reg set XX
sudo iw dev $INTERFACE set type ocb
sudo iw dev $INTERFACE ocb leave
echo "done."

echo "Joining OCB channel: 5900 @10MHz"
sudo iw dev $INTERFACE ocb join 5900 10MHZ
echo "done."

# inhibit any outgoing traffic
sudo sysctl -w net.ipv6.conf.$INTERFACE.disable_ipv6=1
sudo iptables -I OUTPUT -o $INTERFACE -j DROP

sleep 1

echo "Saving to PCAP: $OUTPUT_DIR/$FILE"
# daily rotation
mkdir -p $OUTPUT_DIR
sudo tcpdump -s 0 -i $MONITOR_INTERFACE -w $OUTPUT_DIR/$FILE -G 86400 -Z root
