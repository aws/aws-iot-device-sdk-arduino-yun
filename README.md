# [ARCHIVED] AWS IoT Arduino Yún SDK

> This repository is archived and no longer maintained. The AWS IoT Arduino Yún SDK reached end of support on June 19, 2026. It no longer receives updates, including security updates, and the Arduino Yún hardware it was built for has been discontinued.
>
> The source remains available, read-only, for historical reference. We do not recommend it for new or existing projects.
>
> For current, supported ways to connect devices to AWS IoT, see the [AWS IoT Device SDKs](https://docs.aws.amazon.com/iot/latest/developerguide/iot-sdks.html).

---

<h1 align = "center">AWS IoT Arduino Yún SDK</h1>

## What is AWS IoT Arduino Yún SDK

The AWS-IoT-Arduino-Yún-SDK allows developers to connect their Arduino Yún compatible Board to AWS IoT. By connecting the device to the AWS IoT, users can securely work with the message broker, rules and the Thing Shadow provided by AWS IoT and with other AWS services like AWS Lambda, Amazon Kinesis, Amazon S3, etc.

* [Overview](#overview)
* [Credentials](#credentials)
* [Installation](#installation)
* [API documentation](#api)
* [Key features](#keyfeatures)
* [Using the SDK](#usingthesdk)
* [Example](#example)
* [Error code](#errorcode)
* [Support](#support)

****

<a name="overview"></a>
## Overview
This document provides step by step instructions to install the Arduino Yún SDK and connect your device to the AWS IoT.  
The AWS-IoT-Arduino-Yún-SDK consists of two parts, which take use of the resources of the two chips on Arduino Yún, one for native Arduino IDE API access and the other for functionality and connections to the AWS IoT built on top of [AWS IoT Device SDK for Python](https://github.com/aws/aws-iot-device-sdk-python).
### MQTT connection
The AWS-IoT-Arduino-Yún-SDK provides APIs to let users publish messages to AWS IoT and subscribe to MQTT topics to receive messages transmitted by other devices or coming from the broker. This allows to interact with the standard MQTT PubSub functionality of AWS IoT. More information on MQTT protocol is available [here](http://docs.aws.amazon.com/iot/latest/developerguide/protocols.html).
### Thing shadow
The AWS-IoT-Arduino-Yún-SDK also provides APIs to provide access to thing shadows in AWS IoT. Using this SDK, users will be able to sync the data/status of their devices as JSON files to the cloud and respond to change of status requested by other applications. More information on Thing Shadow is available [here](http://docs.aws.amazon.com/iot/latest/developerguide/iot-thing-shadows.html).

****

<a name="credentials"></a>
## Credentials  
The SDK supports two types of credentials that correspond to the two connection types:

### X.509 certificate

For the certificate-based mutual authentication connection type. Download the [AWS IoT root CA](https://www.symantec.com/content/en/us/enterprise/verisign/roots/VeriSign-Class%203-Public-Primary-Certification-Authority-G5.pem). Use the AWS IoT console to create and download the certificate and private key. You must upload these credentials along with the Python runtime code base to AR9331 on Yún board and specify the location of these files in a configuration file `aws_iot_config.h`.

### IAM credentials

For the Websocket with Signature Version 4 authentication type. You will need IAM credentials: an access key ID, a secret access key. You must also download and upload the [AWS IoT root CA](https://www.symantec.com/content/en/us/enterprise/verisign/roots/VeriSign-Class%203-Public-Primary-Certification-Authority-G5.pem). A tooling script `AWSIoTArduinoYunWebsocketCredentialConfig.sh` is provided for Mac OS/Linux users to update the IAM credentials as environment variables on AR9331, Yún board.  

****

<a name="installation"></a>
## Installation
### Download AWS-IoT-Arduino-Yún-SDK  
Click [here](https://s3.amazonaws.com/aws-iot-device-sdk-arduino-yun/AWS-IoT-Arduino-Yun-SDK-latest.zip) to download AWS-IoT-Arduino-Yún-SDK zip package and extract it to `AWS-IoT-Arduino-Yun-SDK` on your computer.
### Set up your Arduino Yún Board
Please follow the instructions from official website: [Arduino Yún Guide](https://www.arduino.cc/en/Guide/ArduinoYun).

### Installation on Mac OS/Linux
Before proceeding to the following steps, please make sure that you have `expect` installed on your computer and correctly installed the Arduino IDE.  
To install `expect`:  
For Ubuntu, simply run `sudo apt-get install expect`.  
For Mac, `expect` is installed as default.  
For Arduino IDE installation on Linux, please visit [here](http://playground.arduino.cc/Linux/All).

1. Setup the Arduino Yún board and connect it to WiFi. Obtain its IP address and password.  
2. Make sure your computer is connected to the same network (local IP address range).  
3. Download the AWS IoT CA file from [here](https://www.symantec.com/content/en/us/enterprise/verisign/roots/VeriSign-Class%203-Public-Primary-Certification-Authority-G5.pem).
4. Put your AWS IoT CA file, private key and certificate into `AWS-IoT-Arduino-Yun-SDK/AWS-IoT-Python-Runtime/certs`. If you are using MQTT over Websocket, you can put only your AWS IoT CA file into the directory. You should have a correctly configured AWS Identity and Access Management (IAM) role with a proper policy, and a pair of AWS Access Key and AWS Secret Access Key ID, which will be used in step 6. For more information about IAM, please visit [AWS IAM home page](https://aws.amazon.com/iam/).  
5. Open a terminal, cd to `AWS-IoT-Arduino-Yun-SDK`. Do `chmod 755 AWSIoTArduinoYunInstallAll.sh` and execute it as `./AWSIoTArduinoYunInstallAll.sh <Board IP> <UserName> <Board Password>`. By default for Arduino Yún Board, your user name will be `root` and your password will be `arduino`.  
	This script will upload the python runtime code base and credentials to openWRT running on the more powerful micro-controller on you Arduino Yún board.  
	This script will also download and install libraries for openWRT to implement the necessary scripting environment as well as communication protocols.

  Step 5 can take 10-15 minutes for the device to download and install the required packages (distribute, python-openssl, pip, AWSIoTPythonSDKv1.0.0).  

  NOTE: Do NOT close the terminal before the script finishes, otherwise you have to start over with step 5. Make sure you are in your local terminal before repeating step 5.  

6. Optional, only for Websocket. Open a terminal, cd to `AWS-IoT-Arduino-Yun-SDK`. Do `chmod 755 AWSIoTArduinoYunWebsocketCredentialConfig.sh` and execute it as `./AWSIoTArduinoYunWebsocketCredentialConfig.sh <Board iP> <UserName> <Board Password> <AWS_ACCESS_KEY_ID_STRING> <AWS_SECRET_ACCESS_KEY_STRING>`.  
	This script will add the given key ID and secret key onto the OpenWRT as environment variables `$AWS_ACCESS_KEY_ID` and `$AWS_SECRET_ACCESS_KEY`.  
	
	NOTE1: You can always use this script to update your IAM credentials used on the board. The script will handle the update of the environment variables for you.  
	
	NOTE2: Please follow the instructions on the screen after the script completes to power-cycle your board to enable all the environment changes on OpenWRT.  
	
7. Copy and paste `AWS-IoT-Arduino-Yun-SDK/AWS-IoT-Arduino-Yun-Library` folder into Arduino libraries that was installed with your Arduino SDK installation. For Mac OS default, it should be under `Documents/Arduino/libraries`.
8. Restart the Arduino IDE if it was running during the installation. You should be able to see the AWS IoT examples in the Examples folder in your IDE.  

There are the other two scripts: `AWSIoTArduinoYunScp.sh` and `AWSIoTArduinoYunSetupEnvironment.sh`, which are utilized in `AWSIoTArduinoYunInstallAll.sh`. You can always use `AWSIoTArduinoYunScp.sh` to upload your new credentials to your board. When you are in the directory `AWS-IoT-Arduino-Yun-SDK/`, the command should be something like this:  

    ./AWSIoTArduinoYunScp.sh <Board IP> <UserName> <Board Password> <File> <Destination> 

### Installation on Windows

Before proceeding to the following steps, please make sure that you have `Putty` and `WinSCP` installed on your PC. If you prefer to use other tools for SSH-ing into your Arduino Yún board and transferring files, you will have to adjust the steps below according to your tools.  
`Putty` can be downloaded from [here](http://www.chiark.greenend.org.uk/~sgtatham/putty/download.html).  
`WinSCP` can be downloaded from [here](http://winscp.net/eng/download.php).

1. Setup the Arduino Yún Cloud board and connect it to WiFi. Obtain its IP address and password.  
2. Make sure your PC is connected to the same network (local IP address range).  
3. Download the AWS IoT CA file from [here](https://www.symantec.com/content/en/us/enterprise/verisign/roots/VeriSign-Class%203-Public-Primary-Certification-Authority-G5.pem).  
4. Put your AWS IoT CA file, private key and certificate into `AWS-IoT-Arduino-Yun-SDK/AWS-IoT-Python-Runtime/certs`. If you are using MQTT over Websocket, you can put only your AWS IoT CA file into the directory. You should have a correctly configured AWS Identity and Access Management (IAM) role with a proper policy, and a pair of AWS Access Key and AWS Secret Access Key ID, which will be used in step 7. For more information about IAM, please visit [AWS IAM home page](https://aws.amazon.com/iam/).  
5. Start WinSCP and upload `AWS-IoT-Python-Runtime/` folder to `/root` on the board.  
6. Use Putty to ssh into OpenWRT on your board and execute the following commands to install the necessary libraries:

		opkg update
		opkg install distribute
		opkg install python-openssl
		easy_install pip
		pip install AWSIoTPythonSDK==1.0.0
	
  It can take 10-15 minutes for the device to download and install the required packages.
  
7. Optional, only for Websocket. Use Putty to ssh into OpenWRT on your board and modify `/etc/profile` to include your IAM credentials as environment variables:  

		...
		export AWS_ACCESS_KEY_ID=<AWS_ACCES_KEY_ID_STRING>
		export AWS_SECRET_ACCESS_KEY=<AWS_SECRET_ACCESS_KEY_STRING>
		...
  
  After that, run `source /etc/profile` and power-cycle the board to enable the changes.  
  
8. Copy and paste `AWS-IoT-Arduino-Yun-SDK/AWS-IoT-Arduino-Yun-Library` folder into Arduino libraries that was installed with your Arduino SDK installation. For Windows default, it should be under `Documents/Arduino/libraries`.  
9. Restart the Arduino IDE if it was running during the installation. You should be able to see the AWS IoT examples in the Examples folder in your IDE.

****

<a name="api"></a>
## API documentation
Class Name:

	aws_iot_mqtt_client

API:

* MQTT connection  
[IoT\_Error\_t setup(const char\* client\_id, bool clean\_session, MQTTv\_t MQTT\_version, bool useWebsocket)](#setup)  
[IoT\_Error\_t config(const char\* host, unsigned int port, const char\* cafile_path, const char\* keyfile\_path, const char\* certfile\_path)](#config)  
[IoT\_Error\_t configWss(const char\* host, unsigned int port, const char\* cafile_path)](#configWss)  
[IoT\_Error\_t configBackoffTiming(unsigned int baseReconnectQuietTimeSecond, unsigned int maxReconnectQuietTimeSecond, unsigned int stableConnectionTimeSecond)](#configBackoffTiming)  
[IoT\_Error\_t configOfflinePublishQueue(unsigned int queueSize, DropBehavior\_t behavior)](#configOfflinePublishQueue)  
[IoT\_Error\_t configDrainingInterval(float numberOfSeconds)](#configDrainingInterval)  
[IoT\_Error\_t connect(unsigned int keepalive\_interval)](#connect)  
[IoT\_Error\_t publish(const char\* topic, const char\* payload, unsigned int payload\_len, unsigned int qos, bool retain)](#publish)  
[IoT\_Error\_t subscribe(const char\* topic, unsigned int qos, message\_callback cb)](#subscribe)  
[IoT\_Error\_t unsubscribe(const char\* topic)](#unsubscribe)  
[IoT\_Error\_t yield()](#yield)  
[IoT\_Error\_t disconnect()](#disconnect)  
* Thing shadow  
[IoT\_Error\_t shadow\_init(const char\* thingName)](#shadow_init)  
[IoT\_Error\_t shadow\_update(const char\* thingName, const char\* payload, unsigned int payload_len, message\_callback cb, unsigned int timeout)](#shadow_update)  
[IoT\_Error\_t shadow\_get(const char\* thingName, message\_callback cb, unsigned int timeout)](#shadow_get)  
[IoT\_Error\_t shadow\_delete(const char\* thingName, message\_callback cb, unsigned int timeout)](#shadow_delete)  
[IoT\_Error\_t shadow\_register\_delta\_func(const char\* thingName, message\_callback cb)](#shadow_register_delta_func)  
[IoT\_Error\_t shadow\_unregister\_delta\_func(const char\* thingName)](#shadow_unregister_delta_func)  
[IoT\_Error\_t getDesiredValueByKey(const char\* JSONIdentifier, const char\* key, char\* externalJSONBuf, unsigned int bufSize)](#getDesiredValueByKey)  
[IoT\_Error\_t getReportedValueByKey(const char\* JSONIdentifier, const char\* key, char\* externalJSONBuf, unsigned int bufSize)](#getReportedValueByKey)  
[IoT\_Error\_t getDeltaValueByKey(const char\* JSONIdentifier, const char\* key, char\* externalJSONBuf, unsigned int bufSize)](#getDeltaValueByKey)  
[IoT\_Error\_t getValueByKey(const char\* JSONIdentifier, const char\* key, char\* externalJSONBuf, unsigned int bufSize)](#getValueByKey)  

Message Callback:  
[void(\*message\_callback)(char\*, unsigned int, Message\_status\_t)](#message_callback)

<a name="setup"></a>
### IoT\_Error\_t setup(const char\* client\_id, bool clean\_session, MQTTv\_t MQTT\_version, bool useWebsocket)
**Description**  
Start the Python runtime and set up connection for aws\_iot\_mqtt\_client object. Must be called before any of aws\_iot\_mqtt\_client API is called.

**Syntax**  

	object.setup("myClientID"); // setup a client with client_id set to "myClientID"
	object.setup("myClientID", true, MQTTv31, true); // setup a client with client_id set to "myClientID", with clean_session set to true, using MQTT 3.1, over Websocket

**Parameters**  
*client\_id* - The client id for this connection.  
*clean\_session* - Clear the previous connection with this id or not. Default value is true.  
*MQTT\_version* - Version of MQTT protocol for this connection, either MQTTv31 (MQTT version 3.1) or MQTTv311 (MQTT version 3.1.1). Default value is MQTTv311.  
*useWebsocket* - Enable the use of Websocket or not. Default value is false. IAM credentials must be included in the environment variables on OpenWRT to make a successful MQTT connection over Websocket.  

**Returns**  
NONE\_ERROR if the setup on openWRT side and connection settings are correct.  
NULL\_VALUE\_ERROR if input parameters have NULL value.  
OVERFLOW\_ERROR if input string exceeds the internal buffer size.  
SET\_UP\_ERROR if the setup failed.  
SERIAL1\_COMMUNICATION\_ERROR if there is an error in Serial1 communication between the two chips.  
GENERIC\_ERROR if an unknown error happens.

<a name="config"></a>
### IoT\_Error\_t config(const char\* host, unsigned int port, const char\* cafile\_path, const char\* keyfile\_path, const char\* certfile_path)
**Description**  
Configure host, port and certs location used to connect to AWS IoT. If the input strings for host, cafile\_path, keyfile\_path and certfile\_path are set to NULL, the default value will be used to connect. Must be called to load user settings right after `aws_iot_mqtt_client::setup` and before connect.

**Syntax**

	object.config("example.awsamazon.com", 1234, "./cafile", "./keyfile", "./certfile");
	
**Parameters**  
*host* - The endpoint to connect to. Must be a NULL-terminated string.  
*port* - The port number to connect to.  
*cafile_path* - The path of CA file on OpenWRT. Must be a NULL-terminated string.  
*keyfile_path* - The path of private key file on OpenWRT. Must be a NULL-terminated string.  
*certfile_path* - The path of certificate file on OpenWRT. Must be a NULL-terminated string.

**Returns**  
NONE\_ERROR if the configuration is successful.  
NO\_SET\_UP\_ERROR if no setup is called before this call.  
WRONG\_PARAMETER\_ERROR if there is an error for the Python Runtime to get enough input parameters for this command.  
CONFIG\_GENERIC\_ERROR if there is an error in executing the command in Python Runtime.  
GENERIC\_ERROR if an unknown error happens.

<a name="configWss"></a>
### IoT\_Error\_t configWss(const char\* host, unsigned int port, const char\* cafile\_path)
**Description**  
Configure host, port and rootCA location used to connect to AWS IoT over Websocket. If the input strings for host and cafile\_path are set to NULL, the default value will be used to connect. Must be called to load user settings right after `aws_iot_mqtt_client::setup` and before connect. The client must be configured in setup to use Websocket.

**Syntax**

	object.configWss("example.awsamazon.com", 1234, "./cafile");
	
**Parameters**  
*host* - The endpoint to connect to. Must be a NULL-terminated string.  
*port* - The port number to connect to.  
*cafile_path* - The path of CA file on OpenWRT. Must be a NULL-terminated string.  

**Returns**  
NONE\_ERROR if the configuration is successful.  
NO\_SET\_UP\_ERROR if no setup is called before this call.  
WRONG\_PARAMETER\_ERROR if there is an error for the Python Runtime to get enough input parameters for this command.  
CONFIG\_GENERIC\_ERROR if there is an error in executing the command in Python Runtime.  
GENERIC\_ERROR if an unknown error happens.

<a name="configBackoffTiming"></a>
### IoT\_Error\_t configBackoffTiming(unsigned int baseReconnectQuietTimeSecond, unsigned int maxReconnectQuietTimeSecond, unsigned int stableConnectionTimeSecond)  
**Description**  
Configure the progressive back-off timing on reconnect. Time interval for reconnect attempt will increase/double from baseReconnectQuietTimeSecond to maxReconnectQuietTimeSecond. Once a connection is live for longer than stableConnectionTimeSecond, the time interval will be reset to baseReconnectQuietTimeSecond. Note that stableConnectionTimeSecond must be greater than baseReconnectQuietTimeSecond. More details about progressive back-off can be found [here](#progressiveBackoff).  

Note that if this API is not called, the following default values will be used to configure the back-off timing:  

	baseReconnectQuietTimeSecond = 1;
	maxReconnectQuietTimeSecond = 128;
	stableConnectionTimeSecond = 20;

**Syntax**  

	object.configBackoffTiming(1, 32, 20); // Configure baseReconnectQuietTimeSecond to be 1 second. Configure maxReconnectQuietTimeSecond to be 32 seconds. Configure stableConnectionTimeSecond to be 20 seconds.

**Parameters**  
*baseReconnectQuietTimeSecond* - Number of seconds to start with for progressive back-off on reconnect.  
*maxReconnectQuietTimeSecond* - Maximum number of seconds for progressive back-off on reconnect.   
*stableConnectionTimeSecond* - Number of seconds for a valid connection to be considered stable.  

<a name="configOfflinePublishQueue"></a>
### IoT\_Error\_t configOfflinePublishQueue(unsigned int queueSize, DropBehavior\_t behavior)  
**Description**  
Configure the internal queue size and its drop behavior once the queue is full in the Python runtime on the OpenWRT side. When the client is offline, publish requests will be queued up and get resent once the network connection is back. If the number of publish requests exceeds the maximum size of the queue configured, dropping will happen according the drop behavior configured by this API. More details about offline publish requests queuing can be found [here](#offlinePublishQueueDraining).  

**Syntax**  

	object.configOfflinePublishQueue(20, DROP_OLDEST); // Configure size of the offline publish requests queue to be 20. Configure the queue to drop the oldest requests once the queue is full.
	object.configOfflinePublishQueue(20, DROP_NEWEST); // Configure size of the offline publish requests queue to be 20. Configure the queue to drop the newest requests once the queue is full.
	object.configOfflinePublishQueue(0, DROP_OLDEST); // Configure size of the offline publish requests queue to be infinite. The queue-full drop behavior is ignored when the size if infinite.
	object.configOfflinePublishQueue(-1, DROP_OLDEST); // Disable the offline publish requests queue. The queue-full drop behavior is ignored when the queue is disabled.
	
**Parameters**  
*queueSize* - The size of the offline publish requests queue, determining how many publish requests can be queued up while the client it offline.  
*behavior* - The drop behavior when the offline publish requests queue is full. Can be configured to drop the oldest requests or the newest requests in the queue.  

**Returns**  
NONE\_ERROR if the configuration is successful.  
NO\_SET\_UP\_ERROR if no setup is called before this call.  
WRONG\_PARAMETER\_ERROR if there is an error for the Python Runtime to get enough input parameters for this command.  
CONFIG\_GENERIC\_ERROR if there is an error in executing the command in Python Runtime.  
GENERIC\_ERROR if an unknown error happens.

<a name="configDrainingInterval"></a>
### IoT\_Error\_t configDrainingInterval(float numberOfSeconds)  
**Description**  
Configure the draining interval for requests to be sent out when client is back online and gets connected. This will affect the outbound rate for republish and resubscribe requests. More details about draining can be found [here](#offlinePublishQueueDraining).  

**Syntax**  

	object.configDrainingInterval(0.5); // Configure the draining interval to be 0.5 seconds. In this way, resubscribe requests, if any, will be sent per 0.5 seconds. Offline publish requests, if any in the queue, will be sent per 0.5 seconds.

**Parameters**  
*numberOfSeconds* - Number of seconds to wait between every resubscribe/republish request when the client is back online and connected.  

**Returns**  
NONE\_ERROR if the configuration is successful.  
NO\_SET\_UP\_ERROR if no setup is called before this call.  
WRONG\_PARAMETER\_ERROR if there is an error for the Python Runtime to get enough input parameters for this command.  
CONFIG\_GENERIC\_ERROR if there is an error in executing the command in Python Runtime.  
GENERIC\_ERROR if an unknown error happens.  

<a name="connect"></a>
### IoT\_Error\_t connect(unsigned int keepalive\_interval)
**Description**  
Connect to AWS IoT, using user-specific keepalive setting.

**Syntax**
	
	object.connect(); // connect to AWS IoT with default keepalive set to 60 seconds
	object.connect(55); // connect to AWS IoT with keepalive set to 55 seconds
	
**Parameters**  
*keepalive\_interval* - amount of time for MQTT ping request interval, in seconds. Default is set to 60 seconds.

**Returns**  
NONE\_ERROR if the connect is successful.  
NO\_SET\_UP\_ERROR if no setup is called before this call.  
WRONG\_PARAMETER\_ERROR if there is an error for the Python Runtime to get enough input parameters for this command.  
CONNECT\_SSL\_ERROR if the TLS handshake failed.  
CONNECT\_ERROR if the connection failed.  
CONNECT\_TIMEOUT if the connection gets timeout.  
CONNECT\_CREDENTIAL\_NOT\_FOUND if the specified credentials are not found on OpenWRT.  
WEBSOCKET\_CREDENTIAL\_NOT\_FOUND if the IAM credentials do not exist as environment variables on OpenWRT.  
CONNECT\_GENERIC\_ERROR if there is an error in executing the command in Python Runtime.  
GENERIC\_ERROR if an unknown error happens.

<a name="publish"></a>
### IoT\_Error\_t publish(const char\* topic, const char\* payload, unsigned int payload\_len, unsigned int qos, bool retain)
**Description**  
Publish a new message to the desired topic with qos and retain flag settings using MQTT protocol

**Syntax**

    object.publish("myTopic", "myMessage", strlen("myMessage"), 0, false); // publish "myMessage" to topic "myTopic" in QoS 0 with retain flag set to false

**Parameters**  
*topic* - Topic name to publish to. Must be a NULL-terminated string.  
*payload* - Payload to publish.  
*payload_len* - Length of payload.  
*qos* - Qualiy of service, could be 0 or 1.  
*retain* - retain flag.

**Returns**  
NONE\_ERROR if the publish is successful.  
NULL\_VALUE\_ERROR if input parameters have NULL value.  
OVERFLOW\_ERROR if topic/payload exceeds the internal buffer size.  
NO\_SET\_UP\_ERROR if no setup is called before this call.  
WRONG\_PARAMETER\_ERROR if there is an error for the Python Runtime to get enough input parameters for this command.  
PUBLISH\_ERROR if the publish failed.  
PUBLISH\_TIMEOUT if the publish gets timeout.  
PUBLISH\_QUEUE\_FULL if the internal offline publish requests queue is full.  
PUBLISH\_QUEUE\_DISABLED if the internal offline publish requests queue is disabled.  
PUBLISH\_GENERIC\_ERROR if there is an error in executing the command in Python Runtime.  
GENERIC\_ERROR if an unknown error happens.

<a name="subscribe"></a>
### IoT\_Error\_t subscribe(const char\* topic, unsigned int qos, message\_callback cb)
**Description**  
Subscribe to the desired topic and register a callback for new messages from this topic. 

**Syntax**

    object.subscribe("myTopic", 0, myCallbackFunc); // subscribe to topic "myTopic" in QoS 0 and register its callback function as myCallbackFunc

**Parameters**  
*topic* - The topic to subscribe to. Must be a NULL-terminated string.  
*qos* - Quality of service, could be 0 or 1.  
*cb* - Function pointer to user-specific callback function to call when a new message comes in for the subscribed topic. The callback function should have a parameter list of (char*, unsigned int, Message_status_t) to store the incoming message content and the length of the message.

**Returns**  
NONE\_ERROR if the subscribe is successful.  
NULL\_VALUE\_ERROR if input parameters have NULL value.  
OVERFLOW\_ERROR if topic/payload exceeds the internal buffer size.  
OUT\_OF\_SKETCH\_SUBSCRIBE\_MEMORY if the number of current subscribe exceeds the configured number in aws\_iot\_config\_SDK.h.  
NO\_SET\_UP\_ERROR if no setup is called before this call.  
WRONG\_PARAMETER\_ERROR if there is an error for the Python Runtime to get enough input parameters for this command.  
SUBSCRIBE\_ERROR if the subscribe failed.  
SUBSCRIBE\_TIMEOUT if the subscribe gets timeout.  
SUBSCRIBE\_GENERIC\_ERROR if there is an error in executing the command in Python Runtime.  
GENERIC\_ERROR if an unknown error happens.

<a name="unsubscribe"></a>
### IoT\_Error\_t unsubscribe(const char\* topic)
**Description**  
Unsubscribe to the desired topic.

**Syntax**

    object.unsubscribe("myTopic");

**Parameters**  
*topic* - The topic to unsubscribe to. Must be a NULL-terminated string.

**Returns**  
NONE\_ERROR if the unsubscribe is successful.  
NULL\_VALUE\_ERROR if input parameters have NULL value.  
OVERFLOW\_ERROR if topic exceeds the internal buffer size.  
NO\_SET\_UP\_ERROR if no setup is called before this call.  
WRONG\_PARAMETER\_ERROR if there is an error for the Python Runtime to get enough input parameters for this command.  
UNSUBSCRIBE\_ERROR if the unsubscribe failed.  
UNSUBSCRIBE\_TIMEOUT if the unsubscribe gets timeout.  
UNSUBSCRIBE\_GENERIC\_ERROR if there is an error in executing the command in Python Runtime.  
GENERIC\_ERROR if an unknown error happens.

<a name="yield"></a>
### IoT\_Error\_t yield()
**Description**  
Called in the loop to check if there is a new message from all subscribed topics, as well as thing shadow topics. Registered callback functions will be called according to the sequence of messages if there is any. Specifically, unnecessary shadow thing topics (accepted/rejected) will be unsubscribed according to the incoming new messages to free subscribe slots. Users should call this function frequently to receive new messages and free subscribe slots for new subscribes, especially for shadow thing requests.
 
**Syntax**

    object.yield();

**Parameters**  
None

**Returns**  
NONE\_ERROR if the yield is successful, whether there is a new message or not.  
OVERFLOW\_ERROR if the new message exceeds the internal buffer size.  
YIELD\_ERROR if the yield failed.

<a name="disconnect"></a>
### IoT\_Error\_t disconnect()
**Description**  
Disconnect from AWS IoT.

**Syntax**

	object.disconnect();
	
**Parameters**  
None

**Returns**  
NONE\_ERROR if disconnect is successful.  
NO\_SET\_UP\_ERROR if no setup is called before this call.  
DISCONNECT\_ERROR if the disconnect failed.  
DISCONNECT\_TIMEOUT if the disconnect gets timeout.  
DISCONNECT\_GENERIC\_ERROR if there is an error in executing the command in Python Runtime.  
GENERIC\_ERROR if an unknown error happens.

<a name="shadow_init"></a>
### IoT\_Error\_t shadow\_init(const char\* thingName)
**Description**  
Initialize thing shadow configuration and a shadow instance with thingName. Should be called before any of the thing shadow API call for thingName shadow operations.

**Syntax**

	object.shadow_init("NewThingName"); // Init thing shadow configuration and set thing name to "NewThingName"

**Parameters**  
*thingName* - Thing name for the shadow instance to be created. Must be a NULL-terminated string.

**Returns**  
NONE\_ERROR if thing shadow is successfully initialized.  
NULL\_VALUE\_ERROR if input parameters have NULL value.  
OVERFLOW\_ERROR if thing name exceeds the internal buffer size.  
SHADOW\_INIT\_ERROR if thing shadow initialization failed.  
GENERIC\_ERROR if an unknown error happens. 

<a name="shadow_update"></a>
### IoT\_Error\_t shadow\_update(const char\* thingName, const char* payload, unsigned int payload_len, message\_callback cb, unsigned int timeout)
**Description**  
Update the thing shadow data in the cloud by publishing a new JSON file onto the corresponding thing shadow topic and subscribing accepted/rejected thing shadow topics to get feedback of whether it is a successful/failed request. Timeout can be set in seconds as the maximum waiting time for feedback. Once the request gets timeout, a timeout message will be received. The registered callback function will be called whenever there is an accepted/rejected/timeout feedback. Subscription to accepted/rejected topics will be processed in a persistent manner and will not be unsubscribed once this API is called for this shadow.

**Syntax**

	object.shadow_update("UserThingName", JSON_FILE, strlen(JSON_FILE), UserCallbackFunction, 5); // update the data of "UserThingName" thing shadow in the cloud to JSON_FILE, with a timeout of 5 seconds and UserCallbackFunction as the callback function

**Parameters**  
*thingName* - The name of the thing shadow in the cloud. Must be a NULL-terminated string.  
*payload* - The data that needs to be updated into the cloud, in JSON file format.  
*payload_len* - Length of payload  
*cb* - Function pointer to user-specific callback function to call when a new message comes in for the subscribed topic. The callback function should have a parameter list of (char\*, unsigned int, Message_status_t) to store the incoming message content and the length of the message.  
*timeout* - The maximum time to wait for feedback.  


**Returns**  
NONE\_ERROR if the shadow update request succeeds.  
NULL\_VALUE\_ERROR if input parameters have NULL value.  
OVERFLOW\_ERROR if thing name/payload exceeds the internal buffer size.  
OUT\_OF\_SKETCH\_SUBSCRIBE\_MEMORY if the number of current subscribe exceeds the configured number in aws\_iot\_config\_SDK.h.  
NO\_SHADOW\_INIT\_ERROR if the shadow with thingName is initialized before this call.  
WRONG\_PARAMETER\_ERROR if there is an error for the Python Runtime to get enough input parameters for this command.  
SUBSCRIBE\_ERROR if the subscribe (accepted/rejected) failed.  
SUBSCRIBE\_TIMEOUT if the subscribe gets timeout.  
PUBLISH\_ERROR if the publish (payload) failed.  
PUBLISH\_TIMEOUT if the publish (payload) gets timeout.  
PUBLISH\_QUEUE\_FULL if the publish action failed because of a full internal offline publish requests queue.  
PUBLISH\_QUEUE\_DISABLED if the publish action failed because of a disabled internal offline publish requests queue.  
SHADOW\_UPDATE\_GENERIC\_ERROR if there is an error in executing the command in Python Runtime.  
GENERIC\_ERROR if an unknown error happens. 

<a name="shadow_get"></a>
### IoT\_Error\_t shadow\_get(const char\* thingName, message\_callback cb, unsigned int timeout)
**Description**  
Obtain the thing shadow data in the cloud by publishing an empty JSON file onto the corresponding thing shadow topic and subscribing accepted/rejected thing shadow topics to get feedback of whether it is a successful/failed request. Timeout can be set in seconds as the maximum waiting time for feedback. Once the request gets timeout, a timeout message will be received. The registered callback function will be called whenever there is an accepted/rejected/timeout feedback. Subscription to accepted/rejected topics will be processed in a persistent manner and will not be unsubscribed once this API is called for this shadow. Thing shadow data will be available as a JSON file in the callback.

**Syntax**  

	object.shadow_get("UserThingName", UserCallbackFunction, 5); // get the data of the thing shadow "UserThingName", with a timeout of 5 seconds and UserCallbackFunction as the callback function

**Parameters**  
*thingName* - The name of the thing shadow in the cloud. Must be a NULL-terminated string.  
*cb* - Function pointer to user-specific callback function to call when a new message comes in for the subscribed topic. The callback function should have a parameter list of (char\*, unsigned int, Message_status_t) to store the incoming message content and the length of the message.  
*timeout* - The maximum time to wait for feedback.  

**Returns**  
NONE\_ERROR if the shadow get request succeeds.  
NULL\_VALUE\_ERROR if input parameters have NULL value.  
OVERFLOW\_ERROR if thing name exceeds the internal buffer size.  
OUT\_OF\_SKETCH\_SUBSCRIBE\_MEMORY if the number of current subscribe exceeds the configured number in aws\_iot\_config\_SDK.h.  
NO\_SHADOW\_INIT\_ERROR if the shadow with thingName is initialized before this call.  
WRONG\_PARAMETER\_ERROR if there is an error for the Python Runtime to get enough input parameters for this command.  
SUBSCRIBE\_ERROR if the subscribe (accepted/rejected) failed.  
SUBSCRIBE\_TIMEOUT if the subscribe gets timeout.  
PUBLISH\_ERROR if the publish (payload) failed.  
PUBLISH\_TIMEOUT if the publish (payload) gets timeout.  
PUBLISH\_QUEUE\_FULL if the publish action failed because of a full internal offline publish requests queue.  
PUBLISH\_QUEUE\_DISABLED if the publish action failed because of a disabled internal offline publish requests queue.  
SHADOW\_GET\_GENERIC\_ERROR if there is an error in executing the command in Python Runtime.  
GENERIC\_ERROR if an unknown error happens.

<a name="shadow_delete"></a>
### IoT\_Error\_t shadow\_delete(const char\* thingName, message\_callback cb, unsigned int timeout)
**Description**  
Delete the thing shadow data in the cloud by publishing an empty JSON file onto the corresponding thing shadow topic and subscribing accepted/rejected thing shadow topics to get feedback of whether it is a successful/failed request. Timeout can be set in seconds as the maximum waiting time for feedback. Once the request gets timeout, a timeout message will be received. The registered callback function will be called whenever there is an accepted/rejected/timeout feedback. After the feedback comes in, it will automatically unsubscribe accepted/rejected shadow topics. 

**Syntax**  

	object.shadow_delete("UserThingName", UserCallbackFunction, 5); // delete the data of the thing shadow "UserThingName", with a timeout of 5 seconds and UserCallbackFunction as the callback function

**Parameters**  
*thingName* - The name of the thing shadow in the cloud. Must be a NULL-terminated string.  
*cb* - Function pointer to user-specific callback function to call when a new message comes in for the subscribed topic. The callback function should have a parameter list of (char\*, unsigned int, Message_status_t) to store the incoming message content and the length of the message.  
*timeout* - The maximum time to wait for feedback.  

**Returns**  
NONE\_ERROR if the shadow delete request succeeds.  
NULL\_VALUE\_ERROR if input parameters have NULL value.  
OVERFLOW\_ERROR if thing name exceeds the internal buffer size.  
OUT\_OF\_SKETCH\_SUBSCRIBE\_MEMORY if the number of current subscribe exceeds the configured number in aws\_iot\_config\_SDK.h.  
NO\_SHADOW\_INIT\_ERROR if the shadow with thingName is initialized before this call.  
WRONG\_PARAMETER\_ERROR if there is an error for the Python Runtime to get enough input parameters for this command.  
SUBSCRIBE\_ERROR if the subscribe (accepted/rejected) failed.  
SUBSCRIBE\_TIMEOUT if the subscribe gets timeout.  
PUBLISH\_ERROR if the publish (payload) failed.  
PUBLISH\_TIMEOUT if the publish (payload) gets timeout.  
PUBLISH\_QUEUE\_FULL if the publish action failed because of a full internal offline publish requests queue.  
PUBLISH\_QUEUE\_DISABLED if the publish action failed because of a disabled internal offline publish requests queue.  
SHADOW\_DELETE\_GENERIC\_ERROR if there is an error in executing the command in Python Runtime.  
GENERIC\_ERROR if an unknown error happens.

<a name="shadow_register_delta_func"></a>
### IoT\_Error\_t shadow\_register\_delta\_func(const char\* thingName, message\_callback cb)
**Description**  
Subscribe to the delta topic of the corresponding thing shadow with the given name and register a callback. Whenever there is a difference between the desired and reported state data, the registered callback will be called and the feedback/message will be available in the callback.

**Syntax**

	object.shadow_register_delta_func("UserThingName", UserCallBackFunction); // register UserCallbackFunction as the  delta callback function for the thing shadow "UserThingName"

**Parameters**  
*thingName* - The name of the thing shadow in the cloud. Must be a NULL-terminated string.  
*cb* - Function pointer to user-specific callback function to call when a new message comes in for the subscribed topic. The callback function should have a parameter list of (char\*, unsigned int, Message_status_t) to store the incoming message content and the length of the message.

**Return**  
NONE\_ERROR if the shadow delta topic is successfully subscribed and the callback function is successfully registered.  
NULL\_VALUE\_ERROR if input parameters have NULL value.  
OVERFLOW\_ERROR if thing name exceeds the internal buffer size.  
OUT\_OF\_SKETCH\_SUBSCRIBE\_MEMORY if the number of current subscribe exceeds the configured number in aws\_iot\_config\_SDK.h.  
NO\_SHADOW\_INIT\_ERROR if the shadow with thingName is initialized before this call.  
WRONG\_PARAMETER\_ERROR if there is an error for the Python Runtime to get enough input parameters for this command.  
SUBSCRIBE\_ERROR if the subscribe (accepted/rejected) failed.  
SUBSCRIBE\_TIMEOUT if the subscribe gets timeout.  
SHADOW\_REGISTER\_DELTA\_CALLBACK\_GENERIC\_ERROR if there is an error in executing the command in Python Runtime.  
GENERIC\_ERROR if an unknown error happens.

<a name="shadow_unregister_delta_func"></a>
### IoT\_Error\_t shadow\_unregister\_delta\_func(const char\* thingName)
**Description**  
Unsubscribe to the delta topic of the corresponding thing shadow with the given name and unregister the callback. There will be no message coming after this API call if another difference occurs between the desired and reported state data for this thing shadow.

**Syntax**

	object.shadow_unregister_delta_func("UserThingName"); // unregister the delta topic of the thing shadow "UserThingName"

**Parameters**  
*thingName* - The name of the thing shadow in the cloud. Must be a NULL-terminated string.

**Returns**  
NONE\_ERROR if the shadow delta topic is successfully unsubscribed and the callback function is successfully unregistered.  
NULL\_VALUE\_ERROR if input parameters have NULL value.  
OVERFLOW\_ERROR if thing name exceeds the internal buffer size.  
NO\_SHADOW\_INIT\_ERROR if the shadow with thingName is initialized before this call.  
WRONG\_PARAMETER\_ERROR if there is an error for the Python Runtime to get enough input parameters for this command.  
UNSUBSCRIBE\_ERROR if the subscribe (accepted/rejected) failed.  
UNSUBSCRIBE\_TIMEOUT if the subscribe gets timeout.  
SHADOW\_UNREGISTER\_DELTA\_CALLBACK\_GENERIC\_ERROR if there is an error in executing the command in Python Runtime.  
GENERIC\_ERROR if an unknown error happens.

<a name="getDesiredValueByKey"></a>
### IoT\_Error\_t getDesiredValueByKey(const char\* JSONIdentifier, const char\* key, char\* externalJSONBuf, unsigned int bufSize)  
**Description**  
Get the value by key in the desired section in the shadow JSON document denoted by the provided identifier. The corresponding value will be stored as a string into a user-specified externalBuffer. Nested key-value access is available. More information can be found [here](#individualKVAccess).  

**Syntax**  

	object.getDesiredValueByKey("JSON-0", "property1", someBuffer, someBufferSize); // Access JSONDocument["state"]["desired"]["property1"] denoted by JSONIdentifier "JSON-0" and store the value in someBuffer
	object.getDesiredValueByKey("JSON-0", "property2\"subproperty", someBuffer, someBufferSize); // Access JSONDocument["state"]["desired"]["property2"]["subproperty"] denoted by JSONIdentifier "JSON-0" and store the value in someBuffer 

**Parameters**  
*JSONIdentifier* - The JSON Identifier string to access a certain JSON document stored in Python runtime on the OpenWRT side. This is obtained from the registered shadow callback as shadow responses.  
*key* - The key for dereferencing out the value in the desired section of the JSON document. Nested key can be specified using `"` as the delimiter.  
*externalJSONBuf* - Buffer specified by the user to store the incoming value, as string.  
*bufSize* - Size of the buffer to store the incoming value, as string.  

**Returns**  
NONE\_ERROR if the value is retrieved successfully.  
NO\_SET\_UP\_ERROR if no setup is called before this call.  
OVERFLOW\_ERROR if the length of the incoming value exceeds the size of the provided externalJSONBuf.  
JSON\_FILE\_NOT\_FOUND if the JSON document with the provided JSON identifier does not exist.  
JSON\_KEY\_NOT\_FOUND if the specified key does not exist in the JSON document denoted by the provided JSON identifier.  
JSON\_GENERIC\_ERROR if there is an error in executing the command in Python Runtime.   
GENERIC\_ERROR if an unknown error happens.   

<a name="getReportedValueByKey"></a>
### IoT\_Error\_t getReportedValueByKey(const char\* JSONIdentifier, const char\* key, char\* externalJSONBuf, unsigned int bufSize)]  
**Description**  
Get the value by key in the reported section in the shadow JSON document denoted by the provided identifier. The corresponding value will be stored as a string into a user-specified externalBuffer. Nested key-value access is available. More information can be found [here](#individualKVAccess).  

**Syntax**  

	object.getReportedValueByKey("JSON-0", "property1", someBuffer, someBufferSize); // Access JSONDocument["state"]["reported"]["property1"] denoted by JSONIdentifier "JSON-0" and store the value in someBuffer
	object.getReportedValueByKey("JSON-0", "property2\"subproperty", someBuffer, someBufferSize); // Access JSONDocument["state"]["reported"]["property2"]["subproperty"] denoted by JSONIdentifier "JSON-0" and store the value in someBuffer 

**Parameters**  
*JSONIdentifier* - The JSON Identifier string to access a certain JSON document stored in Python runtime on the OpenWRT side. This is obtained from the registered shadow callback as shadow responses.  
*key* - The key for dereferencing out the value in the reported section of the JSON document. Nested key can be specified using `"` as the delimiter.  
*externalJSONBuf* - Buffer specified by the user to store the incoming value, as string.  
*bufSize* - Size of the buffer to store the incoming value, as string.  

**Returns**  
NONE\_ERROR if the value is retrieved successfully.  
NO\_SET\_UP\_ERROR if no setup is called before this call.  
OVERFLOW\_ERROR if the length of the incoming value exceeds the size of the provided externalJSONBuf.  
JSON\_FILE\_NOT\_FOUND if the JSON document with the provided JSON identifier does not exist.  
JSON\_KEY\_NOT\_FOUND if the spedified key does not exist in the JSON document denoted by the provided JSON identifier.  
JSON\_GENERIC\_ERROR if there is an error in executing the command in Python Runtime.   
GENERIC\_ERROR if an unknown error happens.   

<a name="getDeltaValueByKey"></a>
### IoT\_Error\_t getDeltaValueByKey(const char\* JSONIdentifier, const char\* key, char\* externalJSONBuf, unsigned int bufSize)]  
**Description**  
Get the value by key in the state section in the shadow JSON document denoted by the provided identifier. The corresponding value will be stored as a string into a user-specified externalBuffer. Nested key-value access is available. More information can be found [here](#individualKVAccess).  

**Syntax**  

	object.getDeltaValueByKey("JSON-0", "property1", someBuffer, someBufferSize); // Access JSONDocument["state"]["property1"] denoted by JSONIdentifier "JSON-0" and store the value in someBuffer
	object.getDeltaValueByKey("JSON-0", "property2\"subproperty", someBuffer, someBufferSize); // Access JSONDocument["state"]["property2"]["subproperty"] denoted by JSONIdentifier "JSON-0" and store the value in someBuffer 

**Parameters**  
*JSONIdentifier* - The JSON Identifier string to access a certain JSON document stored in Python runtime on the OpenWRT side. This is obtained from the registered shadow callback as shadow responses.  
*key* - The key for dereferencing out the value in the state section of the JSON document. Nested key can be specified using `"` as the delimiter.  
*externalJSONBuf* - Buffer specified by the user to store the incoming value, as string.  
*bufSize* - Size of the buffer to store the incoming value, as string.  

**Returns**  
NONE\_ERROR if the value is retrieved successfully.  
NO\_SET\_UP\_ERROR if no setup is called before this call.  
OVERFLOW\_ERROR if the length of the incoming value exceeds the size of the provided externalJSONBuf.  
JSON\_FILE\_NOT\_FOUND if the JSON document with the provided JSON identifier does not exist.  
JSON\_KEY\_NOT\_FOUND if the specified key does not exist in the JSON document denoted by the provided JSON identifier.  
JSON\_GENERIC\_ERROR if there is an error in executing the command in Python Runtime.   
GENERIC\_ERROR if an unknown error happens.   

<a name="getValueByKey"></a>
### IoT\_Error\_t getValueByKey(const char\* JSONIdentifier, const char\* key, char\* externalJSONBuf, unsigned int bufSize)]  
**Description**  
Get the value by key in the shadow JSON document denoted by the provided identifier. The corresponding value will be stored as a string into a user-specified externalBuffer. Nested key-value access is available. More information can be found [here](#individualKVAccess).  

**Syntax**  

	object.getValueByKey("JSON-0", "property1", someBuffer, someBufferSize); // Access JSONDocument["property1"] denoted by JSONIdentifier "JSON-0" and store the value in someBuffer
	object.getValueByKey("JSON-0", "property2\"subproperty", someBuffer, someBufferSize); // Access JSONDocument["property2"]["subproperty"] denoted by JSONIdentifier "JSON-0" and store the value in someBuffer 

**Parameters**  
*JSONIdentifier* - The JSON Identifier string to access a certain JSON document stored in Python runtime on the OpenWRT side. This is obtained from the registered shadow callback as shadow responses.  
*key* - The key for dereferencing out the value in the JSON document. Nested key can be specified using `"` as the delimiter.  
*externalJSONBuf* - Buffer specified by the user to store the incoming value, as string.  
*bufSize* - Size of the buffer to store the incoming value, as string.  

**Returns**  
NONE\_ERROR if the value is retrieved successfully.  
NO\_SET\_UP\_ERROR if no setup is called before this call.  
OVERFLOW\_ERROR if the length of the incoming value exceeds the size of the provided externalJSONBuf.  
JSON\_FILE\_NOT\_FOUND if the JSON document with the provided JSON identifier does not exist.  
JSON\_KEY\_NOT\_FOUND if the specified key does not exist in the JSON document denoted by the provided JSON identifier.  
JSON\_GENERIC\_ERROR if there is an error in executing the command in Python Runtime.   
GENERIC\_ERROR if an unknown error happens.   

<a name="message_callback"></a>
### void(\*message\_callback)(char\*, unsigned int, Message\_status\_t)]  
**Description**  
Callback function for received MQTT messages, used for plain MQTT communications as well as shadow communications.  
For plain MQTT messages, message payload and size will be passed into the callback. Message\_status\_t will be STATUS\_NORMAL. See Parameters below for more details.  
For shadow messages, JSON identifier and its size will be passed into the callback. Message\_status\_t varies for shadow messages from different topics. For accept shadow responses, Message\_status\_t will be STATUS\_SHADOW\_ACCEPTED. For reject shadow responses, Message\_status\_t will be STATUS\_SHADOW\_REJECTED. For delta shadow responses, Message\_status\_t will be STATUS\_NORMAL. See Parameters below for more details.  

**Syntax**  

	void custom_message_callback(char* msg, unsigned int length, Message_status_t status) {
		// * Access the incoming message from msg, length
		// Message payload for plain MQTT messages
		// JSON identifer for shadow messages
		// * Access the message status from status
		// STATUS_NORMAL for plain MQTT/shadow delta messages
		// STATUS_SHADOW_ACCEPTED for shadow accept responses
		// STATUS_SHADOW_REJECTED for shadow reject responses
	}

**Parameters**  
char\* - Incoming message. Message payload for plain MQTT messages and JSON identifier for shadow message/responses.  
unsigned int - Length of bytes of the incoming message.  
Message\_status\_t - Status of the incoming responses/messages. It has the following values:   

	typedef enum {
		STATUS_DEBUG = -1,
		STATUS_NORMAL = 0,
		STATUS_SHADOW_TIMEOUT = 1,
		STATUS_SHADOW_ACCEPTED = 2,
		STATUS_SHADOW_REJECTED = 3,
		STATUS_MESSAGE_OVERFLOW = 4
	} Message_status_t;

`STATUS_NORMAL` indicates that a new plain MQTT message/shadow delta message has arrived.  
`STATUS_SHADOW_TIMEOUT` indicates that the incoming message is a shadow response for an operation timeout. There was no response received for the corresponding shadow operation within the preconfigured timeout.  
`STATUS_SHADOW_ACCEPTED` indicates that the incoming message is a shadow response for accept. The corresponding shadow operation was accepted by the AWS IoT service and has succeeded.  
`STATUS_SHADOW_REJECTED` indicates that the incoming message is a shadow response for reject. The corresponding shadow operation was rejected by the AWS IoT service and has failed.  
`STATUS_MESSAGE_OVERFLOW` indicates that the size of the incoming message has exceeded the size of the internal message buffer. Internal message buffer size, configured in `aws_iot_config_SDK.h`, needs to be increased to receive the complete incoming message.  
`STATUS_DEBUG` is for SDK internal use.  

**Returns**  
No returns.  

****

<a name="keyfeatures"></a>
## Key features  
<a name="individualKVAccess"></a>
#### Individual Key Value Access for Shadow  
As for shadow operations (Get/Update/Delete) and shadow delta messages, instead of detailed the message content for shadow JSON document, a JSON identifier will be passed through into the registered callback so that it can be used for key/value pair access on demand through the individual key/value pair access APIs. A JSON identifier of a shadow JSON response received looks like this:  

	JSON-i

where i is an integer number.  

Note that there is a limitation on the total number of history JSON documents that can be kept on the OpenWRT side for key/value pair retrieval. The limits are:  

512 entries for shadow JSON accepted responses  
512 entries for shadow JSON rejected responses  
512 entries for shadow JSON delta messages  

Once the limits are exceeded, new incoming shadow JSON documents will overwrite history entries starting from the beginning (`JSON-0`, `JSON-1` and `JSON-2`).  

The following APIs are provided for uses to access shadow JSON key value pair from Arduino sketch in an easier manner:  
[IoT\_Error\_t getDesiredValueByKey(const char\* JSONIdentifier, const char\* key, char\* externalJSONBuf, unsigned int bufSize)](#getDesiredValueByKey)  
[IoT\_Error\_t getReportedValueByKey(const char\* JSONIdentifier, const char\* key, char\* externalJSONBuf, unsigned int bufSize)](#getReportedValueByKey)  
[IoT\_Error\_t getDeltaValueByKey(const char\* JSONIdentifier, const char\* key, char\* externalJSONBuf, unsigned int bufSize)](#getDeltaValueByKey)  
[IoT\_Error\_t getValueByKey(const char\* JSONIdentifier, const char\* key, char\* externalJSONBuf, unsigned int bufSize)](#getValueByKey)  

For a typical shadow JSON document (responses for get/update/delete), it should look like this:  

	{
		"state": {
			"desired": {
				...
			},
			"reported": {
				...
			}
		},
		...
	}

`getDesiredValueByKey` and `getReportedValueByKey` can be used to access the key value pair in the desired/reported section respectively.  

For a typical shadow JSON document (messages for delta), it should look like this:  

	{
		"state": {
			...
		},
		...
	}

`getDeltaValueByKey` can be used to access the key value pair in the delta shadow JSON messages.  

More generally, `getValueByKey` can be used to access key value pair in a more generic way where users can specify their own key patterns. Nested JSON key is denoted using `"` as the delimiter.  

For example, we have the following shadow JSON document with a JSON identifier `JSON-0`:  

	{
		"state": {
			"desired": {
				"property1": "value1",
				"property2": {
					"subproperty": "value2"
				}
			},
			"reported": {
				"property3": "value3"
			}
		},
		...
	}

To access a series of key value pair, we can use the following function calls:  

	object.getDesiredValueByKey("JSON-0", "property1", buffer, bufferSize); // Access JSONDocument["state"]["desired"]["property1"]
	object.getReportedValueByKey("JSON-0", "property3", buffer, bufferSize); // Access JSONDocument["state"]["reported"]["property3"]
	object.getDesiredValueByKey("JSON-0", "property2\"subproperty", buffer, bufferSize); // Access JSONDocument["state"]["desired"]["property2"]["subproperty"]
	
Note that the following two function calls are equivalent. They both access the nested JSON key value pair `JSONDocument["state"]["desired"]["property2"]["subproperty"]`:  

	object.getDesiredValueByKey("JSON-0", "property2\"subproperty", buffer, bufferSize);
	object.getValueByKey("JSON-0", "state\"desired\"property2\"subproperty", buffer, bufferSize);

See that `getValueByKey` is a more generic way for shadow JSON key value access.  

For detailed use cases, please check out [Examples](#example).

<a name="progressiveBackoff"></a>
#### Progressive Reconnect Back-off  
API is provided to configure the progressive back-off timing parameters:  
[IoT\_Error\_t configBackoffTiming(unsigned int baseReconnectQuietTimeSecond, unsigned int maxReconnectQuietTimeSecond, unsigned int stableConnectionTimeSecond)](#configBackoffTiming)

The auto-reconnect happens with a progressive back-off, which follows the following mechanism for reconnect quiet time:   

<h5 align="center">t<sup>current</sup> = min(2<sup>n</sup>t<sup>base</sup>, t<sup>max</sup>),</h5>  

where t<sup>current</sup> is the current reconnect quiet time, t<sup>base</sup> is the base reconnect quiet time, t<sup>max</sup> is the maximum reconnect quiet time.  

The reconnect quiet time will be doubled on disconnect and reconnect attempt until it reaches the preconfigured maximum reconnect quiet time. Once the connection is stable for over the stableConnectionTime, the reconnect quiet time will be reset to the baseReconnectQuietTime.  

If no `configBackoffTiming` gets called, the following default configuration for back-off timing will be done on `setup` call:  

	baseReconnectQuietTimeSecond = 1;
	maxReconnectQuietTimeSecond = 128;
	stableConnectionTimeSecond = 20;

<a name="offlinePublishQueueDraining"></a>
#### Offline publish requests queuing with draining  
APIs are provided to configure the offline publish requests queuing (size and drop behavior) as well as draining intervals:  
[IoT\_Error\_t configOfflinePublishQueue(unsigned int queueSize, DropBehavior\_t behavior)](#configOfflinePublishQueue)  
[IoT\_Error\_t configDrainingInterval(float numberOfSeconds)](#configDrainingInterval)  

When the client is temporarily offline and gets disconnected due to some network failure, publish requests will be queued up into an internal queue in the Python runtime on the OpenWRT side until the number of queued-up requests reaches to the size limit of the queue. Once the queue is full, offline publish requests will be discarded or replaced according to different configuration of the drop behavior:  

	typedef enum {
		DROP_OLDEST = 0,
		DROP_NEWEST = 1
	} DropBehavior_t;

Lets say we configure the size of offlinePublishQueue to be 5 and we have 7 offline publish requests coming in...  

In a `DROP_OLDEST` configuration:  

	myClient.configOfflinePublishQueue(5, DROP_OLDEST);

The internal queue should be like this when the queue is just full:  

	HEAD ['pub_req0', 'pub_req1', 'pub_req2', 'pub_req3', 'pub_req4']
	
When the 6th and the 7th publish requests are made offline, the internal queue will be like this:  

	HEAD ['pub_req2', 'pub_req3', 'pub_req4', 'pub_req5', 'pub_req6']

Since the queue is already full, the oldest requests `pub_req0` and `pub_req1` are discarded.  

In a `DROP_NEWEST` configuration:  

	myClient.configOfflinePublishQueue(5, DROP_NEWEST);

The internal queue should be like this when the queue is just full:  

	HEAD ['pub_req0', 'pub_req1', 'pub_req2', 'pub_req3', 'pub_req4']
	
When the 6th and the 7th publish requests are made offline, the internal queue will be like this:  

	HEAD ['pub_req0', 'pub_req1', 'pub_req2', 'pub_req3', 'pub_req4']

Since the queue is already full, the newest requests `pub_req5` and `pub_req6` are discarded.  

When the client is back online, connected and resubscribed to all topics that it has previously subscribed to, the draining starts. All requests in the offline publish queue will be resent at the configured draining rate.  

if no `configOfflinePublishQueue` or `configDrainingInterval` is called, the following default configuration for offline publish queuing and draining will be done on setup call:  

	offlinePublishQueueSize = 20
	dropBehavior = DROP_NEWEST
	drainingInterval = 0.5 sec

Note that before the draining process finishes, any new publish request within this time will be added to the queue. Therefore, draining rate should be higher than the normal publish rate to avoid an endless draining process after reconnect.  

Also note that disconnect event is detected based on PINGRESP MQTT packet loss. Offline publish queuing will NOT be triggered until the disconnect event gets detected. Configuring a shorter keep-alive interval allows the client to detect disconnects more quickly. Any QoS0 publish requests issued after the network failure and before the detection of the PINGRESP loss will be lost.  

<a name="usingthesdk"></a>
## Using the SDK
**Make sure you have properly installed the AWS-IoT-Arduino-Yún-SDK and setup the board.**

<a name="slowstartup"></a>
**Make sure to start the sketch after openWRT is ready and gets connected to WiFi. It takes about 80-90 seconds for Arduino Yún board to start the openWRT and get connected to WiFi for each power cycle.**

**Make sure you have properly configured SDK settings in `aws_iot_config.h` inside each sketch directory:**

	//===============================================================
	#define AWS_IOT_MQTT_HOST "<RANDOM_STRING>.iot.<REGION>.amazonaws.com" 	// your endpoint
	#define AWS_IOT_MQTT_PORT 8883									// your port, use 443 for MQTT over Websocket
	#define AWS_IOT_CLIENT_ID	"My_ClientID"						// your client ID
	#define AWS_IOT_MY_THING_NAME "My_Board"						// your thing name
	#define AWS_IOT_ROOT_CA_FILENAME "aws-iot-rootCA.crt"           // your root-CA filename
	#define AWS_IOT_CERTIFICATE_FILENAME "cert.pem"                 // your certificate filename
	#define AWS_IOT_PRIVATE_KEY_FILENAME "privkey.pem"              // your private key filename
	//===============================================================

**These settings can be downloaded from the AWS IoT console after you created a device and clicked on "Connect a device".**  	

**Make sure you have included the AWS-IoT-Arduino-Yún-SDK library:**

    #include <aws_iot_mqtt.h>
    

**Make sure you have included your configuration header file:**

	#include "aws_iot_config.h"

**Make sure you have enough memory for subscribe, messages and sketch runtime. Internal buffer size is defined in SDK library source directory `libraries/AWS-IoT-Arduino-Yun-Library/aws_iot_config_SDK.h`. The following are default settings:**

	#define MAX_BUF_SIZE 256										// maximum number of bytes to publish/receive
	#define MAX_SUB 15 												// maximum number of subscribe
	#define CMD_TIME_OUT 200										// maximum time to wait for feedback from AR9331, 200 = 10 sec

**Make sure you setup the client, configure it using your configuration and connect it to AWS IoT first. Remember to use certs path macros for configuration:**

    aws_iot_mqtt_client myClient;
    myClient.setup(AWS_IOT_CLIENT_ID);
    // myClient.setup(AWS_IOT_CLIENT_ID, true, MQTTv31, true); // Use Websocket
    myClient.config(AWS_IOT_MQTT_HOST, AWS_IOT_MQTT_PORT, AWS_IOT_ROOT_CA_PATH, AWS_IOT_PRIVATE_KEY_PATH, AWS_IOT_CERTIFICATE_PATH);
    // myClient.configWss(AWS_IOT_MQTT_HOST, AWS_IOT_MQTT_PORT, AWS_IOT_ROOT_CA_PATH); // Use Websocket
    myClient.connnect();

**Remember to check incoming messages in a loop**:

    void loop() { 
      ...  
      myClient.yield();
      ...
    }

**When you are using thing shadow API for a specific device shadow name, make sure you initialize the shadow with your device shadow name first:**

	myClient.shadow_init(AWS_IOT_MY_THING_NAME); // For shadow of this device
	myClient.shadow_init("AnotherDevice"); // For another shadow

**When you are using thing shadow API, always make sure MAX\_SUB is big enough for a thing shadow request in the loop:**

	...
	myClient.shadow_get("myThingName", myCallback, 5); // need 2 in MAX_SUB
	...
	void loop() {
		...
		myClient.shadow_get("myThingName", myCallback, 5); // need 4 in MAX_SUB
		myClient.yield(); // unsubscribe thing shadow topics when necessary
		...
	}

**When you are using thing shadow API, make sure you set the timeout to a proper value and frequently call yield to free subscribe resources. Long timeout with low rate of yielding and high rate of shadow request will result in exhaustion of subscribe resources:**

	void loop() {
		...
		myClient.shadow_get("myThingName", myCallback, 5); // 5 sec timeout is fine for a request per 5 sec
		
		// myClient.shadow_get("myThingName", myCallback, 50);
		// 50 sec timeout is too long. When missing feedback happens frequently, with a rate of 1 request per 5 sec, subscribed topics will soon accumulate and exceed MAX_SUB before any of the previously-subscribed topic gets timeout and unsubscribed
		
		myClient.yield();
		
		delay(5000); // 5 sec delay
		...
	}

**Enjoy the Internet of Things!**

****

<a name="example"></a>
## Example
### BasicPubSub
This [example](https://github.com/aws/aws-iot-device-sdk-arduino-yun/tree/master/AWS-IoT-Arduino-Yun-Library/examples/BasicPubSub) demonstrates a simple MQTT publish/subscribe using AWS IoT from Arduino Yún board. It first subscribes to a topic once and registers a callback to print out new messages to Serial monitor and then publishes to the topic in a loop. Whenever it receives a new message, it will be printed out to Serial monitor indicating the callback function has been called.

* **Hardware Required**  
Arduino Yún  
Computer connected with Arduino Yún using USB serial

* **Software Required**  
None

* **Circuit Required**  
None

* **Attention**  
Please make sure to start the example sketch after the board is fully set up and openWRT is up and connected to WiFi. See [here](#slowstartup).

* **Code**  
	Create an instance of aws\_iot\_mqtt\_client. 

		aws_iot_mqtt_client myClient;
		
	In `setup()`, open the Serial. Set the instance up and connect it to the AWS IoT.

		Serial.begin(115200);
		...
 		if((rc = myClient.setup(AWS_IOT_CLIENT_ID)) == 0) {
    		// Load user configuration
    		if((rc = myClient.config(AWS_IOT_MQTT_HOST, AWS_IOT_MQTT_PORT, AWS_IOT_ROOT_CA_PATH, AWS_IOT_PRIVATE_KEY_PATH, AWS_IOT_CERTIFICATE_PATH)) == 0) {
      			// Use default connect: 60 sec for keepalive
      			if((rc = myClient.connect()) == 0) {
        			success_connect = true;
        			...
        		}
        		else {...}
        	}
        	else {...}
        }
        else {...}
        ...
          		
  	In `setup()`, subscribe to the desired topic and wait for some delay time.
  	
  	  	if((rc = myClient.subscribe("topic1", 1, msg_callback)) != 0) {
    		Serial.println(F("Subscribe failed!"));
    		Serial.println(rc);
    	}
    	delay(2000);
    	
  	In `loop()`, publish to this topic and call yield function to receive the message every 5 seconds.
  	
  		sprintf(msg, "new message %d", cnt);
  		if((rc = myClient.publish("topic1", msg, strlen(msg), 1, false)) != 0) {
  			Serial.println(F("Publish failed!"));
  			Serial.println(rc);
  		}
		if((rc = myClient.yield()) != 0) {
			Serial.println(F("Yield failed!"));
			Serial.println(rc);
		}
		...
		delay(5000);
		
	The full sketch can be found in `AWS-IoT-Arduino-Yun-Library/examples/BasicPubSub`.

### ThingShadowEcho sample app
This [example](https://github.com/aws/aws-iot-device-sdk-arduino-yun/tree/master/AWS-IoT-Arduino-Yun-Library/examples/ThingShadowEcho) demonstrates Arduino Yún board as a device communicating with AWS IoT, syncing data into the thing shadow in the cloud and receiving commands from an app. Whenever there is a new command from the app side to change the desired state of the device, the board will receive this request and apply the change by publishing it as the reported state. By registering a delta callback function, users will be able to see this incoming message and notice the syncing of the state.  

* **Hardware Required**  
Arduino Yún  
Computer connected with Arduino Yún using USB serial

* **Software Required**  
App-side code that updates the state of the corresponding thing shadow in the cloud  
*Note:* You can also use [AWS IoT console](https://aws.amazon.com/iot/) to update the shadow data.

* **Circuit Required**  
None

* **Attention**  
Please make sure to start the example sketch after the board is fully set up and openWRT is up and connected to WiFi. See [here](#slowstartup).

* **Code**  
	Create an instance of aws\_iot\_mqtt\_client. 

		aws_iot_mqtt_client myClient;
		
	Create logging function for execution tracking.
	
		bool print_log(const char* src, int code) {
			...
		}
	
	In `setup()`, open the Serial. Set the instance up and connect it to the AWS IoT. Init the shadow and register a delta callback function. All steps are tracked using logging function.
	
		if(print_log("setup", myClient.setup(AWS_IOT_CLIENT_ID))) {
			if(print_log("config", myClient.config(AWS_IOT_MQTT_HOST, AWS_IOT_MQTT_PORT, AWS_IOT_ROOT_CA_PATH, AWS_IOT_PRIVATE_KEY_PATH, AWS_IOT_CERTIFICATE_PATH))) {
				if(print_log("connect", myClient.connect())) {
        			success_connect = true;
        			print_log("shadow init", myClient.shadow_init(AWS_IOT_MY_THING_NAME));
        			print_log("register thing shadow delta function", myClient.shadow_register_delta_func(AWS_IOT_MY_THING_NAME, msg_callback_delta));
      			}
    		}
  		}
  		  		
  	In `loop()`, yield to check and receive new incoming messages every 1 second.
  	
  		if(myClient.yield()) {
  			Serial.println("Yield failed.");
  		}
  		delay(1000);
  		
  	For delta callback function, obtain the desired/delta state and put it as the reported state in the JSON file that needs to be updated.
  	
  		void msg_callback_delta(const char* src, unsigned int len, Message_status_t flag) {
  			if(flag == STATUS_NORMAL) {
  				// Get the whole delta section
  				print_log("getDeltaKeyValue", myClient.getDeltaValueByKey(src, "", JSON_buf, 100));
  				String payload = "{\"state\":{\"reported\":";
  				payload += delta;
  				payload += "}}";
  				payload.toCharArray(JSON_buf, 100);
  				print_log("update thing shadow", myClient.shadow_update(AWS_IOT_MY_THING_NAME, JSON_buf, strlen(JSON_buf), NULL, 5));
  			}
  		}
  	
  	Once an update of the desired state for this device is received, a delta message will be received and displayed in the Serial monitor. The device will update this data into the cloud.  
  	
	The full sketch can be found in `AWS-IoT-Arduino-Yun-Library/examples/ThingShadowEcho`.

### Simple Thermostat Simulator
This [example](https://github.com/aws/aws-iot-device-sdk-arduino-yun/tree/master/AWS-IoT-Arduino-Yun-Library/examples/ThermostatSimulatorDevice) demonstrates Arduino Yún as a device accepting instructions and syncing reported state in shadow in AWS IoT, which simulates a thermostat to control the temperature of a room. With the provided example App script, users will be able to get real-time temperature data coming from the board and be able to remotely set the desired temperature. This example also demonstrates how to retrieve shadow JSON data received on Arduino Yún Board.  
[AWS IoT Device SDK for Python](https://github.com/aws/aws-iot-device-sdk-python) is used in App scripts for MQTT connections. Users can modify it to use other MQTT library according to their needs.

* **Hardware Required**  
Arduino Yún  
Computer connected with Arduino Yún using USB serial and running example App scripts

* **Software Required**  
Tkinter for App GUI  
[AWS IoT Device SDK for Python](https://github.com/aws/aws-iot-device-sdk-python) for MQTT connectivity  
Example App script, which is included in the `ExampleAppScripts/ThermostatSimulatorApp/`  

* **Circuit Required**  
None

* **Attention**  
Please make sure to start the example sketch after the board is fully set up and openWRT is up and connected to WiFi. See [here](#slowstartup).

* **Getting started**  
Before proceeding to the following steps, please make sure you have your board set up, with all code base and credentials properly installed. Please make sure you attach the correct policy to your certificate.  
  1. Modify your configuration file to match your own credentials and host address.  
  2. Start the sketch when the board boots up. It should pass the initialization steps and then start to update shadow data. It should have a similar display in the serial monitor as follows:<p/>
  <img align="center" src = "https://s3.amazonaws.com/aws-iot-device-sdk-arduino-yun-suppliemental/images/ThermostatSimulatorDevice_sketch.png"/> 
  3. On the App side, please make sure you have [Tkinter](http://tkinter.unpythonic.net/wiki/How_to_install_Tkinter) and [AWS IoT Device SDK for Python](https://github.com/aws/aws-iot-device-sdk-python) pre-installed on your computer.
  4. Copy and paste your credentials (certificate, private key and rootCA) into `ThermostatSimulatorApp/certs/`. Please make sure to keep the file names as they are downloaded and make sure the CA file name ends with `CA.crt`.  
  5. In the directory `ThermostatSimulatorApp/`, start the App script by executing:

  			python ThermostatSimulatorApp.py -e <Your AWS IoT Endpoint>  # For X.509 certificate based mutual authentication
  			python ThermostatSimulatorApp.py -e <Your AWS IoT Endpoint> -w  # For MQTT over WebSocket using IAM credentials
  			
  			
  		For more details about command line options, you can use the following command:  
  		
  			python ThermostatSimulatorApp.py -h
  		
  		You should be able to see a GUI prompt up with default reported temperature:<p/>
  <img align="center" src= "https://s3.amazonaws.com/aws-iot-device-sdk-arduino-yun-suppliemental/images/ThermostatSimulatorApp_start.png"/>
  6. Try to input a desired temperature and click <kbd>SET</kbd>. If it succeeds, you should be able to see the desired temperature on the panel and a log printed out in the console space. The board will start continuously syncing temperature settings:<p/>
  <img align="center" src= "https://s3.amazonaws.com/aws-iot-device-sdk-arduino-yun-suppliemental/images/ThermostatSimulatorApp_setTemp.png"/>  
  *Note:* The temperature is configured to be lower than 100 F and higher than -100 F. Error message will be printed out if there is a malformed setting:<p/>
  <img align="center" src= "https://s3.amazonaws.com/aws-iot-device-sdk-arduino-yun-suppliemental/images/ThermostatSimulatorApp_setAboveLimits.png"/><p/>
  <img align="center" src= "https://s3.amazonaws.com/aws-iot-device-sdk-arduino-yun-suppliemental/images/ThermostatSimulatorApp_setBelowLimits.png"/>

* **Code**  
	Create an instance of aws\_iot\_mqtt\_client. 

		aws_iot_mqtt_client myClient;
		
	Create logging function for execution tracking.
	
		bool print_log(const char* src, int code) {
			...
		}
	
  In `setup()`, open the Serial. Set the instance up and connect it to the AWS IoT. Init the shadow and register a delta callback function. All steps are tracked using logging function.
	
        if(print_log("setup", myClient.setup(AWS_IOT_CLIENT_ID))) {
          if(print_log("config", myClient.config(AWS_IOT_MQTT_HOST, AWS_IOT_MQTT_PORT, AWS_IOT_ROOT_CA_PATH, AWS_IOT_PRIVATE_KEY_PATH, AWS_IOT_CERTIFICATE_PATH))) {
            if(print_log("connect", myClient.connect())) {
              success_connect = true;
              print_log("shadow init", myClient.shadow_init(AWS_IOT_MY_THING_NAME));
              print_log("register thing shadow delta function", myClient.shadow_register_delta_func(AWS_IOT_MY_THING_NAME, msg_callback_delta));
            }
          }
        }

  In `loop()`, simulate the behavior of a thermostat. Check to see the difference between the desired and the reported temperature. If the desired temperature is higher, increase the reported temperature by 0.1 degree per 1 second (per loop). If the desired one is lower, decrease the reported temperature by 0.1 degree per 1 second (per loop). Increase/Decrease action will happen until the reported reaches the desired. Update the reported temperature and then yield to check if there is any new delta message.

        void loop() {
          if(success_connect) {
            if(desiredTemp - reportedTemp > 0.001) {reportedTemp += 0.1;}
            else if(reportedTemp - desiredTemp > 0.001) {reportedTemp -= 0.1;}
            dtostrf(reportedTemp, 4, 1, float_buf);
            float_buf[4] = '\0';
            sprintf_P(JSON_buf, PSTR("{\"state\":{\"reported\":{\"Temp\":%s}}}"), float_buf);
            print_log("shadow update", myClient.shadow_update(AWS_IOT_MY_THING_NAME, JSON_buf, strlen(JSON_buf), NULL, 5));
            if(myClient.yield()) {
              Serial.println("Yield failed.");
            }
            delay(1000); // check for incoming delta per 1000 ms
          }
        }

  For delta callback function, get the desired state and the desired temperature data in it. Update the desired temperature record on board so that the board knows what to do, heating or cooling.

        void msg_callback_delta(const char* src, unsigned int len, Message_status_t flag) {
        	if(flag == STATUS_NORMAL) {
        		// Get Temp section in delta messages
        		print_log("getDeltaKeyValue", myClient.getDeltaValueByKey(src, "Temp", JSON_buf, 50));				String delta = data.substring(st, ed);
        		desiredTemp = String(JSON_buf).toFloat();
        	}
        }
        
  Each time the board receives a new desired temperature different from its reported temperature. Changes will happen, synced into shadow and captured by the example App. Users will be able to see the whole process of temperature updating from the App side.

	The full sketch can be found in `AWS-IoT-Arduino-Yun-Library/examples/ThermostatSimulatorDevice`.

	
<a name="errorcode"></a>
## Error code
The following error codes are defined in `AWS-IoT-Arduino-Yun-Library/aws_iot_error.h`:  

	typedef enum {
		NONE_ERROR = 0,
		GENERIC_ERROR = -1,
		NULL_VALUE_ERROR = -2,
		OVERFLOW_ERROR = -3,
		OUT_OF_SKETCH_SUBSCRIBE_MEMORY = -4,
		SERIAL1_COMMUNICATION_ERROR = -5,
		SET_UP_ERROR = -6,
		NO_SET_UP_ERROR = -7,
		WRONG_PARAMETER_ERROR = -8,
		CONFIG_GENERIC_ERROR = -9,
		CONNECT_SSL_ERROR = -10,
		CONNECT_ERROR = -11,
		CONNECT_TIMEOUT = -12,
		CONNECT_CREDENTIAL_NOT_FOUND = -13,
		CONNECT_GENERIC_ERROR = -14,
		PUBLISH_ERROR = -15,
		PUBLISH_TIMEOUT = -16,
		PUBLISH_GENERIC_ERROR = -17,
		SUBSCRIBE_ERROR = -18,
		SUBSCRIBE_TIMEOUT = -19,
		SUBSCRIBE_GENERIC_ERROR = -20,
		UNSUBSCRIBE_ERROR = -21,
		UNSUBSCRIBE_TIMEOUT = -22,
		UNSUBSCRIBE_GENERIC_ERROR = -23,
		DISCONNECT_ERROR = -24,
		DISCONNECT_TIMEOUT = -25,
		DISCONNECT_GENERIC_ERROR = -26,
		SHADOW_INIT_ERROR = -27,
		NO_SHADOW_INIT_ERROR = -28,
		SHADOW_GET_GENERIC_ERROR = -29,
		SHADOW_UPDATE_GENERIC_ERROR = -30,
		SHADOW_UPDATE_INVALID_JSON_ERROR = -31,
		SHADOW_DELETE_GENERIC_ERROR = -32,
		SHADOW_REGISTER_DELTA_CALLBACK_GENERIC_ERROR = -33,
		SHADOW_UNREGISTER_DELTA_CALLBACK_GENERIC_ERROR = -34,
		YIELD_ERROR = -35,
		WEBSOCKET_CREDENTIAL_NOT_FOUND = -36,
		JSON_FILE_NOT_FOUND = -37,
		JSON_KEY_NOT_FOUND = -38,
		JSON_GENERIC_ERROR = -39,
		PUBLISH_QUEUE_FULL = -40,
		PUBLISH_QUEUE_DISABLED = -41
	} IoT_Error_t;
	
<a name="support"></a>
## Support
If you have technical questions about AWS IoT Device SDK, please use [AWS IoT forum](https://forums.aws.amazon.com/forum.jspa?forumID=210).  
For any other questions on AWS IoT, please contact [AWS Support](https://aws.amazon.com/contact-us/).
