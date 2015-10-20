#!/usr/bin/expect -f
# Bring in the Yun IP via command line arguments
set yunip [lindex $argv 0];
set yunpass [lindex $argv 1];
set copysrc [lindex $argv 2];
set copydest [lindex $argv 3];

# Change expect timeout to be never
set timeout -1

# spawn an scp process and copy over our files
spawn scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -r $copysrc root@$yunip:$copydest
#######################
expect {
-re ".*es.*o.*" {
exp_send "yes\r"
exp_continue
}
-re ".*sword.*" {
# modify the following to your own board password
exp_send "$yunpass\r"
}
}
interact
