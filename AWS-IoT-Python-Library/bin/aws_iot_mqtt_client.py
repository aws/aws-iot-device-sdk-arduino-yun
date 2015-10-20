#!/usr/bin/python

import sys
import signal
import sys
import Queue
import time

sys.path.insert(0, '/opt/aws-iot/lib/')

import awsiot
import paho.mqtt.client as mqtt
from awsutils import *

# conventions
###################################
'''
On python side, for feedback to Arduino:
'I' - constructor
'G' - config
'C' - connect
'P' - publish
'D' - disconnect
'S' - subscribe
'U' - unsubscribe
'Y' - yieldMessage
'Z' - lockQueueSize
---------------------
'SI' - shadowInit
'SU' - shadowUpdate
'SG' - shadowGet
'SD' - shadowDelete
*Incoming string starting with the corresponding lower case letter represents the corresponding requests
'''
# marco
###################################
MAX_CONN_TIME = 10
EXIT_TIME_OUT = 25
CHUNK_SIZE = 50 # 50 bytes as a chunk
YIELD_METADATA_SIZE = 5 # 'Y ' + ' <more?> ': 2 + 3

# helper function
###################################
def interrupted():
    raise Exception

def ThingShadowTimeOutCheck(iot_mqtt_client_obj, paho_mqtt_client_obj, stop_sign):
    while(not stop_sign):
        unsubQ = Queue.Queue(0) # Topics need to be unsubscribed
        iot_mqtt_client_obj.idMap_lock.acquire()
        iot_mqtt_client_obj.req_Map_lock.acquire()
        currTime = time.time() # Obtain current timestamp for this check
        for key in iot_mqtt_client_obj.req_Map.keys():
            if(iot_mqtt_client_obj.req_Map[key].is_expired(currTime)): # Time expired for this entry
                # refresh reference count for ThingShadow request to see if necessary to unsub
                need2unsub = False
                currThingName = iot_mqtt_client_obj.req_Map[key].getThingName()
                currType = iot_mqtt_client_obj.req_Map[key].getType()
                if(currType == 'get'):
                    new_ref_CNT = iot_mqtt_client_obj.ref_cnt_Map_get[currThingName] - 1
                    if(new_ref_CNT == 0):
                        need2unsub = True
                    else:
                        iot_mqtt_client_obj.ref_cnt_Map_get[currThingName] = new_ref_CNT
                elif(currType == 'update'):
                    new_ref_CNT = iot_mqtt_client_obj.ref_cnt_Map_update[currThingName] - 1
                    if(new_ref_CNT == 0):
                        need2unsub = True
                    else:
                        iot_mqtt_client_obj.ref_cnt_Map_update[currThingName] = new_ref_CNT
                elif(currType == 'delete'):
                    new_ref_CNT = iot_mqtt_client_obj.ref_cnt_Map_delete[currThingName] - 1
                    if(new_ref_CNT == 0):
                        need2unsub = True # no support for persistent shadow delete
                    else:
                        iot_mqtt_client_obj.ref_cnt_Map_delete[currThingName] = new_ref_CNT
                else: # broken type
                    pass
                # need to unsub?
                temp_key1 = awsiot.idMap_key("$aws/things/" + currThingName + "/shadow/" + currType + "/accepted", key)
                temp_key2 = awsiot.idMap_key("$aws/things/" + currThingName + "/shadow/" + currType + "/rejected", key)
                if(need2unsub):
                    unsubQ.put(temp_key1)
                    unsubQ.put(temp_key2)
                # remove entry from req_Map
                del iot_mqtt_client_obj.req_Map[key]
                # add TIMEOUT message into msgQ
                try:
                    # will result in exception if this topic has already been unsubscribed by user
                    temp_idMap_entry = awsiot.iot_mqtt_client_obj.idMap[temp_key2]
                    ####
                    if(temp_idMap_entry.get_is_ThingShadow()):
                        iot_mqtt_client_obj.msgQ.put(str(temp_idMap_entry.get_ino_id()) + " TIMEOUT")
                    else:
                        pass # if get messed, no TIMEOUT message
                except BaseException as e:
                    pass
            else:
                pass
        # Now do unsubscribe
        while(not unsubQ.empty()):
            # should use lower level of unsub
            this_key = unsubQ.get()
            topic = this_key.topic
            if(iot_mqtt_client_obj.idMap.get(this_key) != None and iot_mqtt_client_obj.idMap[this_key].get_is_ThingShadow()):
                paho_mqtt_client_obj.unsubscribe(topic)
                del iot_mqtt_client_obj.idMap[this_key]
            else:
                pass
        iot_mqtt_client_obj.req_Map_lock.release()
        iot_mqtt_client_obj.idMap_lock.release()
        # delay for 500 ms (not accurate)
        time.sleep(0.5)


# callbacks
###################################
def on_connect(client, userdata, flags, rc):
    userdata.conn_res = rc

def on_disconnect(client, userdata, rc):
    userdata.disconn_res = rc

def on_message(client, userdata, msg):
    userdata.idMap_lock.acquire()
    try:
        for key in userdata.idMap.keys():
            if(mqtt.topic_matches_sub(key.topic, str(msg.topic))): # check for wildcard matching
                idMap_entry = userdata.idMap[key]
                if(idMap_entry.get_is_ThingShadow()): # A ThingShadow-related new message
                    # find out the clientToken
                    JSON_dict = json.loads(str(msg.payload))
                    my_clientToken = JSON_dict.get(u'clientToken')
                    msg_Version = JSON_dict.get(u'version') # could be None
                    # look up this clientToken in req_Map to check timeout
                    userdata.req_Map_lock.acquire()
                    # NO timeout
                    if(userdata.req_Map.has_key(my_clientToken) and my_clientToken == key.clientToken):
                        my_Type = userdata.req_Map[my_clientToken].getType()
                        my_ThingName = userdata.req_Map[my_clientToken].getThingName()
                        del userdata.req_Map[my_clientToken]
                        # now check ref_cnt_Map_get/update to see if necessary to unsub
                        need2unsub = False
                        # check version, see if this is a message containing version regarding thisThingName
                        if(msg_Version != None and userdata.thisThingNameVersionControl.thisThingName == my_ThingName):
                            if(msg_Version > userdata.thisThingNameVersionControl.currLocalVersion):
                                userdata.thisThingNameVersionControl.currLocalVersion = msg_Version # new message, update thisThingName version
                        #
                        topic_accept = "$aws/things/" + my_ThingName + "/shadow/" + my_Type + "/accepted"
                        topic_reject = "$aws/things/" + my_ThingName + "/shadow/" + my_Type + "/rejected"
                        if(my_Type == "get"):
                            new_ref_CNT = userdata.ref_cnt_Map_get[my_ThingName] - 1
                            if(new_ref_CNT == 0): # need to unsub
                                need2unsub = True
                            else:
                                userdata.ref_cnt_Map_get[my_ThingName] = new_ref_CNT
                        elif(my_Type == "update"):
                            new_ref_CNT = userdata.ref_cnt_Map_update[my_ThingName] - 1
                            if(new_ref_CNT == 0): # need to unsub
                                need2unsub = True
                            else:
                                userdata.ref_cnt_Map_update[my_ThingName] = new_ref_CNT
                        elif(my_Type == "delete"): # should reset version number if it is an accepted DELETE
                            msg_topic_str = str(msg.topic)
                            msg_pieces = msg_topic_str.split('/')
                            if(msg_pieces[5] == "accepted"): # if it is an accepted DELETE
                                userdata.thisThingNameVersionControl.currLocalVersion = 0 # reset local version number
                            new_ref_CNT = userdata.ref_cnt_Map_delete[my_ThingName] - 1
                            if(new_ref_CNT == 0): # need to unsub
                                need2unsub = True
                            else:
                                userdata.ref_cnt_Map_delete[my_ThingName] = new_ref_CNT
                        else: # broken Type
                            pass
                        # by this time, we already have idMap_lock
                        if(need2unsub):
                            userdata._iot_mqtt_client_handler.unsubscribe(topic_accept)
                            new_key = awsiot.idMap_key(topic_accept, my_clientToken)
                            if(userdata.idMap.get(new_key) != None):
                                del userdata.idMap[new_key]
                            userdata._iot_mqtt_client_handler.unsubscribe(topic_reject)
                            new_key = awsiot.idMap_key(topic_reject, my_clientToken)
                            if(userdata.idMap.get(new_key) != None):
                                del userdata.idMap[new_key]
                        # add the feedback to msgQ
                        ino_id = idMap_entry.get_ino_id()
                        userdata.msgQ.put(str(ino_id) + " " + str(msg.payload)) # protocol-style convention needed
                    # timeout, ignore this message
                    else:
                        pass
                    userdata.req_Map_lock.release()
                elif(idMap_entry.get_is_delta()): # a delta message, need to check version
                    userdata.req_Map_lock.acquire()
                    JSON_dict = json.loads(str(msg.payload))
                    msg_Version = JSON_dict.get(u'version')
                    # see if the version from the message is newer/bigger regarding thisThingName
                    # parse out to see what thing name of this delta message is...
                    msg_topic_str = str(msg.topic)
                    msg_pieces = msg_topic_str.split('/')
                    msg_ThingName = msg_pieces[2] # now we have thingName...
                    if(msg_Version != None and msg_ThingName == userdata.thisThingNameVersionControl.thisThingName):
                        if(msg_Version <= userdata.thisThingNameVersionControl.currLocalVersion):
                            pass # ignore delta message with old version number
                        else: # now add this delta message to msgQ
                            # update local version
                            userdata.thisThingNameVersionControl.currLocalVersion = msg_Version
                            ino_id = idMap_entry.get_ino_id()
                            userdata.msgQ.put(str(ino_id) + " " + str(msg.payload))
                    userdata.req_Map_lock.release()
                else: # A normal new message
                    ino_id = idMap_entry.get_ino_id()
                    userdata.msgQ.put(str(ino_id) + " " + str(msg.payload)) # protocol-style convention needed
    except BaseException as e: # ignore clean session = false: msg from pre-subscribed topics
        pass
    userdata.idMap_lock.release()

# main func
###################################
signal.signal(signal.SIGALRM, interrupted)
def runtime_func(debug, buf_i, buf_o, mock):
    iot_mqtt_client_obj = None
    cmd_set = set(['i', 'g', 'c', 'p', 'd', 's', 'u', 'y', 'z', 'sg', 'su', 'sd', 'si', '~'])
    try:
        while True:
            # read user input
            signal.alarm(EXIT_TIME_OUT)

            command_type = 'x'
            command_type = get_input(debug, buf_i)

            if(command_type in cmd_set):

                signal.alarm(EXIT_TIME_OUT)

                if(command_type != 'i' and iot_mqtt_client_obj == None):
                    send_output(debug, buf_o, "X no setup")

                elif(command_type == 'i'):
                    src_id = get_input(debug, buf_i)
                    #"886b943355064ca2849189414129e4c6c7b785ec2dbbc8cd1c568b82d8db18dc"
                    try:
                        src_cleansession = False if(int(get_input(debug, buf_i)) == 0) else True
                    except ValueError:
                        src_cleansession = None
                    try:
                        src_protocol = if(int(get_input(debug, buf_i)) == 4) else mqtt.MQTTv31
                    except ValueError:
                        src_protocol = None
                    if (not debug):
                        iot_mqtt_client_obj = awsiot.iot_mqtt_client(src_id, src_cleansession, src_protocol, on_connect, on_disconnect, on_message, ThingShadowTimeOutCheck)
                    else:
                         iot_mqtt_client_obj = mock
                elif(command_type == 'g'):
                    src_serverURL = get_input(debug, buf_i)
                    src_serverPORT = get_input(debug, buf_i)
                    src_cafile = get_input(debug, buf_i)
                    src_key = get_input(debug, buf_i)
                    src_cert = get_input(debug, buf_i)
                    # function call
                    iot_mqtt_client_obj.config(src_serverURL, src_serverPORT, src_cafile, src_key, src_cert)
                elif(command_type == 'c'):
                    try:
                        src_keepalive = int(get_input(debug, buf_i))
                    except ValueError:
                        src_keepalive = None
                    # function call
                    iot_mqtt_client_obj.connect(src_keepalive)
                elif(command_type == 'p'):
                    src_topic = get_input(debug, buf_i)
                    src_payload = get_input(debug, buf_i)
                    try:
                        src_qos = int(get_input(debug, buf_i))
                    except ValueError:
                        src_qos = None
                    try:
                        src_retain = False if(int(get_input(debug, buf_i)) == 0) else True
                    except ValueError:
                        src_retain = None
                    # function call
                    iot_mqtt_client_obj.publish(src_topic, src_payload, src_qos, src_retain)
                elif(command_type == 's'):
                    src_topic = get_input(debug, buf_i)
                    try:
                        src_qos = int(get_input(debug, buf_i))
                    except ValueError:
                        src_qos = None
                    try:
                        src_ino_id = int(get_input(debug, buf_i))
                    except ValueError:
                        src_ino_id = None
                    try:
                        src_is_delta = int(get_input(debug, buf_i))
                    except ValueError:
                        src_is_delta = 0
                    # function call
                    iot_mqtt_client_obj.subscribe(src_topic, src_qos, src_ino_id, src_is_delta)
                elif(command_type == 'u'):
                    src_topic = get_input(debug, buf_i)
                    # function call
                    iot_mqtt_client_obj.unsubscribe(src_topic)
                elif(command_type == 'y'):
                    # function call
                    iot_mqtt_client_obj.yieldMessage()
                elif(command_type == 'd'):
                    # function call
                    iot_mqtt_client_obj.disconnect()
                elif(command_type == 'z'):
                    # function call
                    iot_mqtt_client_obj.lockQueueSize()
                elif(command_type == 'si'):
                    src_thisThingName = get_input(debug, buf_i)
                    # function call
                    iot_mqtt_client_obj.shadowInit(src_thisThingName)
                elif(command_type == 'sg'):
                    src_ThingName = get_input(debug, buf_i)
                    src_clientToken = get_input(debug, buf_i)
                    try:
                        src_TimeOut = (int)(get_input(debug, buf_i))
                    except ValueError:
                        src_TimeOut = 3 # default timeout for ThingShadow request is 3 sec
                    try:
                        src_ino_id_accept = (int)(get_input(debug, buf_i))
                    except ValueError:
                        src_ino_id_accept = -1
                    try:
                        src_ino_id_reject = (int)(get_input(debug, buf_i))
                    except ValueError:
                        src_ino_id_reject = -1
                    # function call
                    iot_mqtt_client_obj.shadowGet(src_ThingName, src_clientToken, src_TimeOut, src_ino_id_accept, src_ino_id_reject)
                elif(command_type == 'su'):
                    src_ThingName = get_input(debug, buf_i)
                    src_clientToken = get_input(debug, buf_i)
                    try:
                        src_TimeOut = (int)(get_input(debug, buf_i))
                    except ValueError:
                        src_TimeOut = -1
                    src_payload = get_input(debug, buf_i)
                    try:
                        src_ino_id_accept = (int)(get_input(debug, buf_i))
                    except ValueError:
                        src_ino_id_accept = -1
                    try:
                        src_ino_id_reject = (int)(get_input(debug, buf_i))
                    except ValueError:
                        src_ino_id_reject = -1
                    try:
                        src_simple_update = (int)(get_input(debug, buf_i)) # should be 1 or 0, 1 - true, 0 - false
                    except ValueError:
                        src_simple_update = 0
                    # function call
                    iot_mqtt_client_obj.shadowUpdate(src_ThingName, src_clientToken, src_TimeOut, src_payload, src_ino_id_accept, src_ino_id_reject, src_simple_update)
                elif(command_type == 'sd'):
                    src_ThingName = get_input(debug, buf_i)
                    src_clientToken = get_input(debug, buf_i)
                    try:
                        src_TimeOut = (int)(get_input(debug, buf_i))
                    except ValueError:
                        src_TimeOut = 3 # default timeout for ThingShadow request is 3 sec
                    try:
                        src_ino_id_accept = (int)(get_input(debug, buf_i))
                    except ValueError:
                        src_ino_id_accept = -1
                    try:
                        src_ino_id_reject = (int)(get_input(debug, buf_i))
                    except ValueError:
                        src_ino_id_reject = -1
                    # function call
                    iot_mqtt_client_obj.shadowDeleteState(src_ThingName, src_clientToken, src_TimeOut, src_ino_id_accept, src_ino_id_reject)
                elif(command_type == '~'): # for debug
                    iot_mqtt_client_obj.stop_sign = True # stop the background thread
                    time.sleep(1)
                    break

            else:
                pass
    except NameError as e:
        raise e
    except:
        send_output(debug, buf_o, "X cmd timeout")
    pass

# execute
##################################
runtime_func(False, None, None, None)
