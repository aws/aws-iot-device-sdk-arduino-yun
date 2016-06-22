#2.1.2 (June 22th, 2016)
Features:  

N/A  

Bugfixes.Improvements:  

* Fixed issue in the examples related to serial1 communication latency flushing the serial port in the loggin function.

#2.1.1 (May 23th, 2016)  
Features:  

N/A  

Bugfixes.Improvements:  

* Fixed issue in retrieving shadow JSON key/value pair where value starts with a certain letter conflicts with the internal protocol.

# 2.1.0 (May 11th, 2016)  
Features:  

* Added new API for configurable offline publish requests queueing for both QoS0 and QoS1.  
* Added new API for configurable draining mechanism for queued publish/resubscribe requests.  

Bugfixes/Improvements:  

* Improved auto-resubscribe logic to allow resubscribe requests go out at a configured draining rate.  

# 2.0.0 (April 26th, 2016)
Features:  

* Added support for individual key-value pair access with configurable JSON history limits for shadow JSON document. Nested JSON key-value pair access is also included.  
* Added configurable progressive backoff logic in auto-reconnect process.  

Bugfixes/Improvements:  

* Improved API function signature to remove compilation warnings from Arduino IDE v1.6.6+.  
* Improved message callback function signature to include message status information for each MQTT messages received.  
* Updated shadow examples to use new individual JSON key-value pair access APIs.  

# 1.1.2 (April 1st, 2016)
Features:  

N/A

Bugfixes/Improvements:

* Removing the executable bit set on all files 

# 1.1.1 (March 23rd, 2016)
Features:  

N/A

Bugfixes/Improvements:

* Improved auto-resubscribe logic. Guaranteed that re-subscribe requests get out and acked before any of the publish requests of the queued messages

# 1.1.0 (March 8, 2016)
Features:

* Added support for MQTT over Websocket using AWS Identity and Access Management (IAM)
* Added new API for MQTT Websocket configuration
* Added support for auto-reconnect for MQTT over Websocket
* Added support for auto-resubscribe

Bugfixes/Improvements:

N/A

# 1.0.3 (January 22, 2016)
Features:

* Switch from subscribe-unsubscribe mechanism to persistent subscription for shadow response processing, avoiding slow rate of shadow requests
* Multiple shadow support

Bugfixes/Improvements:

* Detailed error code for better debugging experience directly in Arduino IDE
* New example of device shadow: Thermostat App/Device simulator, with sketch for device and scripts for App both included

# 1.0.2 (November 5, 2015)
Features:

N/A

Bugfixes/Improvements:

* Added compatibility for Linino openWRT embedded Linux OS (BusyBox v1.19.4 2015-10-03 14:03:26 CEST)
* Refactored file names for credential/codebase upload shell scripts and environment setup shell scripts

# 1.0.1 (November 3, 2015)
Features:

N/A

Bugfixes/Improvements:

* Updated README.md
* Updated examples with error detection
* Fixed timeout interrupt handler function signature
* Improved background thread termination in Python script

# 1.0.0 (October 8, 2015)
Features:

* Release to github
* SDK zip file made available for public download

Bugfixes/Improvements:

* Updated README.md

# 0.2.0 (October 6, 2015)
Features:

* MQTT publish and subscribe with TLS
* Thing Shadow Actions - Update, Get, Delete for any Thing Name
* Thing Shadow Version Control support for current device Thing Name

Bugfixes/Improvements:

* N/A
