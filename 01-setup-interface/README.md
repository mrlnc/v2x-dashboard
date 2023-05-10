This script helps automate the interface setup upon boot. Running the script is required on boot, otherwise the kernel will load the default drivers without ITS-G5 support.

It loads the patched kernel modules, configures the interface, and starts `tcpdump`.

The systemd-unit helps automate running the script upon boot.
