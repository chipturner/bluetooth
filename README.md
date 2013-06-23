chipturner/bluetooth
=========

My Linux bluetooth playground.  So far, just a python script that can
make your linux machine act as a bluetooth keyboard for other
devices. More docs to come.

Useful links:

I started here, but it was missing details:
http://www.linuxuser.co.uk/tutorials/emulate-a-bluetooth-keyboard-with-the-raspberry-pi

So then I went here, and the associated book:
http://people.csail.mit.edu/albert/bluez-intro/
http://www.amazon.com/Bluetooth-Essentials-Programmers-Albert-Huang/dp/0521703751/

The USB HID spec was helpful in figuring out how to actually talk
things like handshakes (which are necessary, and left out of the first
link above).
https://www.bluetooth.org/docman/handlers/downloaddoc.ashx?doc_id=246761

I stumbled across this, which was also helpful:
https://code.google.com/p/androhid/source/checkout

Finally, the bluez source code was solid as well:
http://www.bluez.org/
http://www.bluez.org/development/git/

