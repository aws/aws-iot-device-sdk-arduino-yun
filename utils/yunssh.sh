#!/usr/bin/expect -f
# Bring in the Yun IP, password, and shell command line in
set yunip [lindex $argv 0];
set yunpass [lindex $argv 1];
set sshcmd [lindex $argv 2];
set timeout -1
# modify the following to your board ip

spawn ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@$yunip
#######################
expect {
  -re ".*es.*o.*" {
    exp_send "yes\r"
    exp_continue
  }
  -re ".*sword.*" {
    # modify the following to your board password
    exp_send "$yunpass\r"
  }
}
expect "*~#" {send "$sshcmd\r"}
expect "*~#" {send "exit\r"}
interact
