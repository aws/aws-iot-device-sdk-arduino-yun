#!/usr/bin/expect
# This script helps to upload the targeted file/directory to remote Arduino Yun Board

# Args check
if {$argc!= 3} {
    send_user "usage: ./AWSIoTArduinoYunSetupEnvironment.sh <Board IP> <UserName> <Board Password>\n"
    exit
}

set timeout -1
set ArduinoYunIPAddress [lindex $argv 0]
set ArduinoYunUserName [lindex $argv 1]
set ArduinoYunPassword [lindex $argv 2]
set RemoteEndpoint "$ArduinoYunUserName@$ArduinoYunIPAddress"

send_user "Arduino Yun IP is: $ArduinoYunIPAddress\n"
send_user "Arduino Yun User Name is: $ArduinoYunUserName\n"
send_user "\nThe following dependencies will be remotely installed on Arduino Yun:\n"
send_user "distribute\npython-openssl\n\n"
send_user "Please wait until the installation completes and the program exits.\n\n"

# ssh into Arduino Yun and automatically perform the installation
spawn ssh $RemoteEndpoint
expect {
    # In case this is the first time
    -re ".*yes/no.*" {
        send "yes\r"; exp_continue
	-re ".*assword.*" { send  "$ArduinoYunPassword\r" }
    }
    -re ".*assword.*" { send "$ArduinoYunPassword\r" }
}
# Install all dependencies
expect "*~#" { send "opkg update\r" }
expect "*~#" { send "opkg install distribute\r" }
expect "*~#" { send "opkg install python-openssl\r" }
expect "*~#" { send "easy_install pip\r" }
expect "*~#" { send "pip install AWSIoTPythonSDK==1.0.0\r" }
expect "*~#" { send "exit\r" }
# End of installation
interact
