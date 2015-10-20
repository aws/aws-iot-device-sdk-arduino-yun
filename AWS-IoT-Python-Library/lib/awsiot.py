'''
/*
 * Copyright 2010-2015 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *  http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */
'''

# Python 2.7.3
import sys
import json
import time
import ssl
import thread
import Queue
import threading
import paho.mqtt.client as mqtt
sys.path.insert(0, '/opt/aws-iot/lib/')
from awsutils import *

# marco
###################################
MAX_CONN_TIME = 10
CHUNK_SIZE = 50 # 50 bytes as a chunk
YIELD_METADATA_SIZE = 5 # 'Y ' + ' <more?> ': 2 + 3


# myThingName_version
class myThingName_version:
    thisThingName = None
    currLocalVersion = None

    def __init__(self):
        self.thisThingName = None # default thisThingName is set to None, must call shadow_init
        self.currLocalVersion = -1 # default version is set to -1, must sync it before any update can succeed

# idMap_key
class idMap_key:
    topic = None
    clientToken = None

    def __init__(self, src_topic, src_clientToken):
        self.topic = src_topic
        self.clientToken = src_clientToken

    def __hash__(self):
        return hash(self.topic) + hash(self.clientToken)

    def __eq__(self, another):
        return self.topic == another.topic and self.clientToken == another.clientToken

    def __str__(self):
        return str(self.topic)

# idMap entry
class idMap_info:
    _ino_id = -1
    _is_ThingShadow = False
    _is_delta = False

    def __init__(self, src_ino_id, src_is_ThingShadow, src_is_delta):
        self._ino_id = src_ino_id
        self._is_ThingShadow = src_is_ThingShadow
        self._is_delta = src_is_delta

    def get_ino_id(self):
        return self._ino_id

    def get_is_ThingShadow(self):
        return self._is_ThingShadow

    def get_is_delta(self):
        return self._is_delta

# req_Map entry
class req_Map_info:
    _TimeStart = None
    _TimeOut = None
    _Type = None
    _ThingName = None

    def __init__(self, src_TimeStart, src_TimeOut, src_Type, src_ThingName):
        self._TimeStart = src_TimeStart
        self._TimeOut = src_TimeOut
        self._Type = src_Type
        self._ThingName = src_ThingName

    def is_expired(self, currTime):
        return self._TimeStart + self._TimeOut < currTime

    def getType(self):
        return self._Type # 'update' or 'get' or 'delete'

    def getThingName(self):
        return self._ThingName

    def getTimeOut(self):
        return self._TimeOut

class iot_mqtt_client:
    # client handler
    _iot_mqtt_client_handler = None
    # server information
    _serverURL = "data.iot.us-east-1.amazonaws.com"
    _serverPORT = 8883
    # certs
    _cafile = "/opt/aws-iot/certs/aws-iot-rootCA.crt"
    _key = "/opt/aws-iot/certs/privkey.pem"
    _cert = "/opt/aws-iot/certs/cert.pem"
    # connect result, need to access in callback
    conn_res = -1
    # disconnect result, need to access in callback
    disconn_res = -1
    # message queue
    msgQ = Queue.Queue(0)
    # topicName <-> (ino_id,is_ThingShadow) mapping
    idMap = dict()
    # clientToken <-> (TimeStart,TimeOut,Type,ThingName) mapping
    req_Map = dict()
    # ThingName <-> Ref_CNT mapping for shadow get
    ref_cnt_Map_get = dict()
    # ThingName <-> Ref_CNT mapping for shadow update
    ref_cnt_Map_update = dict()
    # ThingName <-> Ref_CNT mapping for shadow delete
    ref_cnt_Map_delete = dict()
    # Track of thisThingName
    thisThingNameVersionControl = myThingName_version()
    # debug
    wrapper_debug = False
    wrapper_Tx = None
    # lock
    idMap_lock = threading.Lock()
    req_Map_lock = threading.Lock()

    # internal message buffer and ino_id holder
    _dynamic_str = '' # empty string
    _dynamic_ino_id = -1
    _dynamic_queue_size = 0

    # Background Thread
    stop_sign = False

    # robust wrapper
    ###################################
    def config(self, src_serverURL, src_serverPORT, src_cafile, src_key, src_cert):
        if(len(src_serverURL) != 0):
            self._serverURL = src_serverURL
        if(len(str(src_serverPORT)) != 0):
            self._serverPORT = int(src_serverPORT)
        if(len(src_cafile) != 0):
            self._cafile = src_cafile
        if(len(src_key) != 0):
            self._key = src_key
        if(len(src_cert) != 0):
            self._cert = src_cert
        send_output(self.wrapper_debug, self.wrapper_Tx, "G T")

    def __init__(self, id, clean_session, protocol, on_connect, on_disconnect, on_message, shadow_manager):
        try:
            self._iot_mqtt_client_handler = mqtt.Client(id, clean_session, self, protocol)
        except BaseException as e:
            send_output(self.wrapper_debug, self.wrapper_Tx, "I F " + e.message)
            return
        self._iot_mqtt_client_handler.on_connect = on_connect
        self._iot_mqtt_client_handler.on_disconnect = on_disconnect
        self._iot_mqtt_client_handler.on_message = on_message
        print "I T\n"
        # start the background thread to periodically check req_Map
        thread.start_new_thread(shadow_manager, (self, self._iot_mqtt_client_handler, self.stop_sign,))

    def connect(self, keepalive=60):
        # tls
        try:
            self._iot_mqtt_client_handler.tls_set(self._cafile, self._cert, self._key, ssl.CERT_REQUIRED, ssl.PROTOCOL_SSLv23)
        except ValueError as ve:
            send_output(self.wrapper_debug, self.wrapper_Tx, "C F " + ve.message)
            return
        except:
            send_output(self.wrapper_debug, self.wrapper_Tx, "C F TLS Error")
            return

        # connect
        try:
            self._iot_mqtt_client_handler.connect(self._serverURL, self._serverPORT, keepalive)
            self._iot_mqtt_client_handler.loop_start()
        except BaseException as e:
            send_output(self.wrapper_debug, self.wrapper_Tx, "C F " + e.message)
            return

        cnt_sec = 0
        while(cnt_sec < MAX_CONN_TIME and self.conn_res == -1): # waiting for connecting to complete (on_connect)
            cnt_sec += 1
            time.sleep(1)

        if(self.conn_res != -1):
            send_output(self.wrapper_debug, self.wrapper_Tx, "C " + str(self.conn_res) + " " + mqtt.connack_string(self.conn_res)) # 0 for connected
        else:
            send_output(self.wrapper_debug, self.wrapper_Tx, "C F Connection time out")
        return self.conn_res

    def publish(self, topic, payload, qos, retain):
        try:
            (rc, mid) = self._iot_mqtt_client_handler.publish(topic, payload, qos, retain)
        except BaseException as e:
            send_output(self.wrapper_debug, self.wrapper_Tx, "P F " + e.message)
            return
        send_output(self.wrapper_debug, self.wrapper_Tx, "P " + str(rc) + " " + mqtt.error_string(rc))
        return rc

    def disconnect(self):
        try:
            self._iot_mqtt_client_handler.disconnect()
            self._iot_mqtt_client_handler.loop_stop()
        except BaseException as e:
            send_output(self.wrapper_debug, self.wrapper_Tx, "D F " + e.message)
            return

        cnt_sec = 0
        while(cnt_sec < MAX_CONN_TIME and self.disconn_res == -1): # waiting for on_disconnect
            cnt_sec += 1
            time.sleep(1)

        if(self.disconn_res != -1):
            send_output(self.wrapper_debug, self.wrapper_Tx, "D " + str(self.disconn_res) + " " + mqtt.error_string(self.disconn_res))
        else:
            send_output(self.wrapper_debug, self.wrapper_Tx, "D F Disconnection time out")
        return self.disconn_res

    def subscribe(self, topic, qos, ino_id, is_delta):
        try:
            (rc, mid) = self._iot_mqtt_client_handler.subscribe(topic, qos)
            if ino_id == None:
                raise ValueError("None ino_id")
            self.idMap_lock.acquire()
            new_key = idMap_key(topic, None) # no clientToken since it is a normal sub
            new_entry = idMap_info(ino_id, False, is_delta!=0) # This is not a ThingShadow-related topic
            self.idMap[new_key] = new_entry
            self.idMap_lock.release()
        except BaseException as e:
            send_output(self.wrapper_debug, self.wrapper_Tx, "S F " + e.message)
            return
        send_output(self.wrapper_debug, self.wrapper_Tx, "S " + str(rc) + " "  + mqtt.error_string(rc))
        return rc

    def unsubscribe(self, topic):
        try:
            (rc, mid) = self._iot_mqtt_client_handler.unsubscribe(topic)
            self.idMap_lock.acquire()
            new_key = idMap_key(topic, None)
            ino_id = self.idMap[new_key].get_ino_id()
            del self.idMap[new_key]
            self.idMap_lock.release()
        except BaseException as e:
            send_output(self.wrapper_debug, self.wrapper_Tx, "U F " + str(e.message))
            return
        send_output(self.wrapper_debug, self.wrapper_Tx, "U " + str(rc) + " " + str(ino_id) + " " + mqtt.error_string(rc))
        # send back the return value along with the ino_id for C side reference to free the subgroup slot (important)
        return rc

    def lockQueueSize(self):
        # make sure nothing is hapenning in between
        # this would be the number of messages to be processed in the coming yield
        self._dynamic_queue_size = self.msgQ.qsize()
        send_output(self.wrapper_debug, self.wrapper_Tx, "Z T") # finish with the locking the queue size

    def shadowInit(self, src_thisThingName):
        self.thisThingNameVersionControl.thisThingName = src_thisThingName
        send_output(self.wrapper_debug, self.wrapper_Tx, "SI T")

    def shadowGet(self, ThingName, clientToken, TimeOut, ino_id_accept, ino_id_reject):
        try:
            if(ino_id_accept == -1 or ino_id_reject == -1):
                raise Exception("17 shadowGet: Wrong input parameters")
            if(self.thisThingNameVersionControl.thisThingName == None):
                raise Exception("18 shadowGet: Should init shadow first")

            # prep req_Map/ref_cnt_Map_get
            self.req_Map_lock.acquire()
            currTime = time.time()
            new_entry = req_Map_info(currTime, TimeOut, "get", ThingName)
            self.req_Map[clientToken] = new_entry
            # refresh get reference count map
            if(self.ref_cnt_Map_get.has_key(ThingName)):
                cnt = self.ref_cnt_Map_get[ThingName] + 1
                self.ref_cnt_Map_get[ThingName] = cnt
            else:
                self.ref_cnt_Map_get[ThingName] =  1
            self.req_Map_lock.release()
            # Now subscribe and publish, QoS0, retain=False
            # subscribe to shadow get accept
            topic_accept = "$aws/things/" + ThingName + "/shadow/get/accepted"
            (rc1, mid) = self._iot_mqtt_client_handler.subscribe(topic_accept, 0)
            self.idMap_lock.acquire()
            new_key = idMap_key(topic_accept, clientToken)
            new_entry = idMap_info(ino_id_accept, True, False) # This IS a ThingShadow-related topic
            self.idMap[new_key] = new_entry
            self.idMap_lock.release()
            # subscribe to shadow get reject
            topic_reject = "$aws/things/" + ThingName + "/shadow/get/rejected"
            (rc2, mid) = self._iot_mqtt_client_handler.subscribe(topic_reject, 0)
            self.idMap_lock.acquire()
            new_key = idMap_key(topic_reject, clientToken)
            new_entry = idMap_info(ino_id_reject, True, False) # This IS a ThingShadow-related topic
            self.idMap[new_key] = new_entry
            self.idMap_lock.release()

            time.sleep(2) # wait for SUBACK

            # publish to shadow get
            topic_get = "$aws/things/" + ThingName + "/shadow/get"
            # should generate JSON payload here...
            temp_dic = dict()
            temp_dic["clientToken"] = clientToken
            payloadJSON = json.dumps(temp_dic)
            # end of JSON payload generation...
            (rc3, mid) = self._iot_mqtt_client_handler.publish(topic_get, payloadJSON, 1, False)
            # feedback
            if(rc1 + rc2 + rc3 == 0):
                send_output(self.wrapper_debug, self.wrapper_Tx, "SG T")
            else:
                send_output(self.wrapper_debug, self.wrapper_Tx, "SG F " + str(rc1) + " " + str(rc2) + " " + str(rc3))
        except BaseException as e:
            send_output(self.wrapper_debug, self.wrapper_Tx, "SG F " + e.message)

    def shadowUpdate(self, ThingName, clientToken, TimeOut, payload, ino_id_accept, ino_id_reject, simple_update):
        try:
            if(ino_id_accept < -1 or ino_id_reject < -1):
                raise Exception("17 shadowUpdate: Wrong input parameters")
            if(self.thisThingNameVersionControl.thisThingName == None):
                raise Exception("18 shadowUpdate: Should init shadow first")
            # From here, this thing shadow is init.
            # prep req_Map/ref_cnt_Map_get/version
            self.req_Map_lock.acquire()
            currTime = time.time()
            new_entry = req_Map_info(currTime, TimeOut, "update", ThingName)
            self.req_Map[clientToken] = new_entry
            # refresh update reference count map
            if(self.ref_cnt_Map_update.has_key(ThingName)):
                cnt = self.ref_cnt_Map_update[ThingName] + 1
                self.ref_cnt_Map_update[ThingName] = cnt
            else:
                self.ref_cnt_Map_update[ThingName] = 1
            self.req_Map_lock.release()

            if(simple_update == 0): # if the user sets simple_update, does not care about the feedback
                # Now subscribe and publish, QoS0, retain=False
                # subscribe to shadow update accept
                topic_accept = "$aws/things/" + ThingName + "/shadow/update/accepted"
                (rc1, mid) = self._iot_mqtt_client_handler.subscribe(topic_accept, 0)
                self.idMap_lock.acquire()
                new_key = idMap_key(topic_accept, clientToken)
                new_entry = idMap_info(ino_id_accept, True, False) # This IS a ThingShadow-related topic
                self.idMap[new_key] = new_entry
                self.idMap_lock.release()
                # subscribe to shadow update reject
                topic_reject = "$aws/things/" + ThingName + "/shadow/update/rejected"
                (rc2, mid) = self._iot_mqtt_client_handler.subscribe(topic_reject, 0)
                self.idMap_lock.acquire()
                new_key = idMap_key(topic_reject, clientToken)
                new_entry = idMap_info(ino_id_reject, True, False) # This IS a ThingShadow-related topic
                self.idMap[new_key] = new_entry
                self.idMap_lock.release()

                time.sleep(2) # wait for SUBACK
            else:
                rc1 = 0
                rc2 = 0

            # publish to shadow get, this is the place to CHECK VERSION...
            topic_get = "$aws/things/" + ThingName + "/shadow/update"
            # should generate JSON payload here...
            temp_dic = json.loads(payload) # convert payload string to python dictionary, will throw exception if malformed
            # add clientToken
            temp_dic["clientToken"] = clientToken
            payloadJSON = json.dumps(temp_dic)
            # end of JSON payload generation...
            (rc3, mid) = self._iot_mqtt_client_handler.publish(topic_get, payloadJSON, 1, False)
            # feedback
            if(rc1 + rc2 + rc3 == 0):
                send_output(self.wrapper_debug, self.wrapper_Tx, "SU T")
            else:
                send_output(self.wrapper_debug, self.wrapper_Tx, "SU F " + str(rc1) + " " + str(rc2) + " " + str(rc3))
        except BaseException as e:
            send_output(self.wrapper_debug, self.wrapper_Tx, "SU F " + e.message)

    def shadowDeleteState(self, ThingName, clientToken, TimeOut, ino_id_accept, ino_id_reject):
        try:
            if(ino_id_accept == -1 or ino_id_reject == -1):
                raise Exception("17 shadowDeleteState: Wrong input parameters")
            if(self.thisThingNameVersionControl.thisThingName == None):
                raise Exception("18 shadowDeleteState: Should init shadow first")

            currTime = time.time()
            # prep req_Map/ref_cnt_Map_delete
            self.req_Map_lock.acquire()
            new_entry = req_Map_info(currTime, TimeOut, "delete", ThingName)
            self.req_Map[clientToken] = new_entry
            # refresh delete reference count map
            if(self.ref_cnt_Map_get.has_key(ThingName)):
                cnt = self.ref_cnt_Map_delete[ThingName] + 1
                self.ref_cnt_Map_delete[ThingName] = cnt
            else:
                self.ref_cnt_Map_delete[ThingName] = 1
            self.req_Map_lock.release()
            # Now subscribe and publish, QoS0, retain=False
            # subscribe to shadow delete accept
            topic_accept = "$aws/things/" + ThingName + "/shadow/delete/accepted"
            (rc1, mid) = self._iot_mqtt_client_handler.subscribe(topic_accept, 0)
            self.idMap_lock.acquire()
            new_key = idMap_key(topic_accept, clientToken)
            new_entry = idMap_info(ino_id_accept, True, False) # This IS a ThingShadow-related topic
            self.idMap[new_key] = new_entry
            self.idMap_lock.release()
            # subscribe to shadow delete reject
            topic_reject = "$aws/things/" + ThingName + "/shadow/delete/rejected"
            (rc2, mid) = self._iot_mqtt_client_handler.subscribe(topic_reject, 0)
            self.idMap_lock.acquire()
            new_key = idMap_key(topic_reject, clientToken)
            new_entry = idMap_info(ino_id_reject, True, False) # This IS a ThingShadow-related topic
            self.idMap[new_key] = new_entry
            self.idMap_lock.release()

            time.sleep(2) # wait for SUBACK

            # publish to shadow delete
            topic_get = "$aws/things/" + ThingName + "/shadow/delete"
            # should generate JSON payload here...
            temp_dic = dict()
            temp_dic["state"] = None
            temp_dic["clientToken"] = clientToken
            payloadJSON = json.dumps(temp_dic)
            # end of JSON payload generation...
            (rc3, mid) = self._iot_mqtt_client_handler.publish(topic_get, payloadJSON, 1, False)
            # feedback
            if(rc1 + rc2 + rc3 == 0):
                send_output(self.wrapper_debug, self.wrapper_Tx, "SD T")
            else:
                send_output(self.wrapper_debug, self.wrapper_Tx, "SD F " + str(rc1) + " " + str(rc2) + " " + str(rc3))
        except BaseException as e:
            send_output(self.wrapper_debug, self.wrapper_Tx, "SD F " + e.message)

    def yieldMessage(self):
        try:
            # No more message to echo/Nothing left from the previous message
            if(self._dynamic_queue_size == 0 and len(self._dynamic_str) == 0):
                # do a clean-up
                self._dynamic_str = ''
                self._dynamic_queue_size = 0
                self._dynamic_ino_id = -1
                # send feedback
                send_output(self.wrapper_debug, self.wrapper_Tx, "Y F")
            # We have something to echo. Do it chunk by chunk
            else:
                # Nothing left from the previous message, start a new one
                if(len(self._dynamic_str) == 0):
                    self._dynamic_str = self.msgQ.get()
                    temp_split = self._dynamic_str.split(' ', 1)
                    self._dynamic_ino_id = int(temp_split[0]) # get ino_id
                    self._dynamic_queue_size -= 1
                    self._dynamic_str = temp_split[1]
                # See if we need to split it
                string2send = None
                more = 0
                if(len(self._dynamic_str) + YIELD_METADATA_SIZE + len(str(self._dynamic_ino_id))> CHUNK_SIZE):
                    more = 1 # there is going to be more chunks coming...
                    stoppoint = CHUNK_SIZE - YIELD_METADATA_SIZE - len(str(self._dynamic_ino_id))
                    string2send = self._dynamic_str[0:stoppoint]
                    self._dynamic_str = self._dynamic_str[stoppoint:] # update dynamic string
                else: # last chunk
                    string2send = self._dynamic_str
                    self._dynamic_str = '' # clear it because it has been sent
                # deliver only one chunk for one yield request
                # Y <ino_id> <more?> <message chunk>
                send_output(self.wrapper_debug, self.wrapper_Tx, "Y " + str(self._dynamic_ino_id) + " " + str(more) + " " + string2send)
        except BaseException as e:
            send_output(self.wrapper_debug, self.wrapper_Tx, "Y F " + e.message)
