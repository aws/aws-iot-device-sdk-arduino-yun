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
import json
import time
import signal
import ssl
import thread
import Queue
import threading
import paho.mqtt.client as mqtt

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
# macros
###################################
MAX_CONN_TIME = 10
EXIT_TIME_OUT = 25
CHUNK_SIZE = 50  # 50 bytes as a chunk
YIELD_METADATA_SIZE = 5  # 'Y ' + ' <more?> ': 2 + 3


# helper function
###################################
def interrupted(srcSignal, srcFrame):
    raise Exception


def ThingShadowTimeOutCheck(iot_mqtt_client_obj, paho_mqtt_client_obj, stop_sign):
    while not stop_sign[0]:
        unsubQ = Queue.Queue(0)  # Topics need to be unsubscribed
        iot_mqtt_client_obj.idMap_lock.acquire()
        iot_mqtt_client_obj.req_Map_lock.acquire()
        currTime = time.time()  # Obtain current timestamp for this check
        for key in iot_mqtt_client_obj.req_Map.keys():
            if iot_mqtt_client_obj.req_Map[key].is_expired(currTime):  # Time expired for this entry
                # refresh reference count for ThingShadow request to see if necessary to unsub
                need2unsub = False
                currThingName = iot_mqtt_client_obj.req_Map[key].getThingName()
                currType = iot_mqtt_client_obj.req_Map[key].getType()
                if currType == 'get':
                    new_ref_CNT = iot_mqtt_client_obj.ref_cnt_Map_get[currThingName] - 1
                    if new_ref_CNT == 0:
                        need2unsub = True
                    else:
                        iot_mqtt_client_obj.ref_cnt_Map_get[currThingName] = new_ref_CNT
                elif currType == 'update':
                    new_ref_CNT = iot_mqtt_client_obj.ref_cnt_Map_update[currThingName] - 1
                    if new_ref_CNT == 0:
                        need2unsub = True
                    else:
                        iot_mqtt_client_obj.ref_cnt_Map_update[currThingName] = new_ref_CNT
                elif currType == 'delete':
                    new_ref_CNT = iot_mqtt_client_obj.ref_cnt_Map_delete[currThingName] - 1
                    if new_ref_CNT == 0:
                        need2unsub = True  # no support for persistent shadow delete
                    else:
                        iot_mqtt_client_obj.ref_cnt_Map_delete[currThingName] = new_ref_CNT
                else:  # broken type
                    pass
                # need to unsub?
                temp_key1 = idMap_key("$aws/things/" + currThingName + "/shadow/" + currType + "/accepted", key)
                temp_key2 = idMap_key("$aws/things/" + currThingName + "/shadow/" + currType + "/rejected", key)
                if need2unsub:
                    unsubQ.put(temp_key1)
                    unsubQ.put(temp_key2)
                # remove entry from req_Map
                del iot_mqtt_client_obj.req_Map[key]
                # add TIMEOUT message into msgQ
                try:
                    # will result in exception if this topic has already been unsubscribed by user
                    temp_idMap_entry = iot_mqtt_client_obj.idMap[temp_key2]
                    ####
                    if temp_idMap_entry.get_is_ThingShadow():
                        iot_mqtt_client_obj.msgQ.put(str(temp_idMap_entry.get_ino_id()) + " TIMEOUT")
                    else:
                        pass  # if get messed, no TIMEOUT message
                except BaseException:
                    pass
            else:
                pass
        # Now do unsubscribe
        while not unsubQ.empty():
            # should use lower level of unsub
            this_key = unsubQ.get()
            topic = this_key.topic
            if iot_mqtt_client_obj.idMap.get(this_key) is not None and iot_mqtt_client_obj.idMap[this_key].get_is_ThingShadow():
                paho_mqtt_client_obj.unsubscribe(topic)
                del iot_mqtt_client_obj.idMap[this_key]
            else:
                pass
        iot_mqtt_client_obj.req_Map_lock.release()
        iot_mqtt_client_obj.idMap_lock.release()
        # delay for 200 ms (not accurate)
        time.sleep(0.2)


# tool func
###################################
def get_input(debug, buf):
    if debug:  # read from the given buffer
        terminator = buf[0].find('\n')
        if len(buf[0]) != 0 and terminator != -1:
            ret = buf[0][0:terminator]
            buf[0] = buf[0][(terminator + 1):]
            return ret
        else:  # simulate no-input blocking
            while 1:
                pass
    else:
        return raw_input()  # read from stdin


def send_output(debug, buf, content):
    if debug:  # write to the given buffer
        buf[0] = buf[0][:0] + content[0:]
    else:
        print content  # write to stdout


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
            if mqtt.topic_matches_sub(key.topic, str(msg.topic)):  # check for wildcard matching
                idMap_entry = userdata.idMap[key]
                if idMap_entry.get_is_ThingShadow():  # A ThingShadow-related new message
                    # find out the clientToken
                    JSON_dict = json.loads(str(msg.payload))
                    my_clientToken = JSON_dict.get(u'clientToken')
                    msg_Version = JSON_dict.get(u'version')  # could be None
                    # look up this clientToken in req_Map to check timeout
                    userdata.req_Map_lock.acquire()
                    # NO timeout
                    if my_clientToken in userdata.req_Map and my_clientToken == key.clientToken:
                        my_Type = userdata.req_Map[my_clientToken].getType()
                        my_ThingName = userdata.req_Map[my_clientToken].getThingName()
                        del userdata.req_Map[my_clientToken]
                        # now check ref_cnt_Map_get/update to see if necessary to unsub
                        need2unsub = False
                        # check version, see if this is a message containing version regarding thisThingName
                        if msg_Version is not None and userdata.thisThingNameVersionControl.thisThingName == my_ThingName:
                            if msg_Version > userdata.thisThingNameVersionControl.currLocalVersion:
                                userdata.thisThingNameVersionControl.currLocalVersion = msg_Version  # new message, update thisThingName version
                        topic_accept = "$aws/things/" + my_ThingName + "/shadow/" + my_Type + "/accepted"
                        topic_reject = "$aws/things/" + my_ThingName + "/shadow/" + my_Type + "/rejected"
                        if my_Type == "get":
                            new_ref_CNT = userdata.ref_cnt_Map_get[my_ThingName] - 1
                            if new_ref_CNT == 0:  # need to unsub
                                need2unsub = True
                            else:
                                userdata.ref_cnt_Map_get[my_ThingName] = new_ref_CNT
                        elif my_Type == "update":
                            new_ref_CNT = userdata.ref_cnt_Map_update[my_ThingName] - 1
                            if new_ref_CNT == 0:  # need to unsub
                                need2unsub = True
                            else:
                                userdata.ref_cnt_Map_update[my_ThingName] = new_ref_CNT
                        elif my_Type == "delete":  # should reset version number if it is an accepted DELETE
                            msg_topic_str = str(msg.topic)
                            msg_pieces = msg_topic_str.split('/')
                            if msg_pieces[5] == "accepted":  # if it is an accepted DELETE
                                userdata.thisThingNameVersionControl.currLocalVersion = 0  # reset local version number
                            new_ref_CNT = userdata.ref_cnt_Map_delete[my_ThingName] - 1
                            if new_ref_CNT == 0:  # need to unsub
                                need2unsub = True
                            else:
                                userdata.ref_cnt_Map_delete[my_ThingName] = new_ref_CNT
                        else:  # broken Type
                            pass
                        # by this time, we already have idMap_lock
                        if need2unsub:
                            userdata._iot_mqtt_client_handler.unsubscribe(topic_accept)
                            new_key = idMap_key(topic_accept, my_clientToken)
                            if userdata.idMap.get(new_key) is not None:
                                del userdata.idMap[new_key]
                            userdata._iot_mqtt_client_handler.unsubscribe(topic_reject)
                            new_key = idMap_key(topic_reject, my_clientToken)
                            if userdata.idMap.get(new_key) is not None:
                                del userdata.idMap[new_key]
                        # add the feedback to msgQ
                        ino_id = idMap_entry.get_ino_id()
                        userdata.msgQ.put(str(ino_id) + " " + str(msg.payload))  # protocol-style convention needed
                    # timeout, ignore this message
                    else:
                        pass
                    userdata.req_Map_lock.release()
                elif idMap_entry.get_is_delta():  # a delta message, need to check version
                    userdata.req_Map_lock.acquire()
                    JSON_dict = json.loads(str(msg.payload))
                    msg_Version = JSON_dict.get(u'version')
                    # see if the version from the message is newer/bigger regarding thisThingName
                    # parse out to see what thing name of this delta message is...
                    msg_topic_str = str(msg.topic)
                    msg_pieces = msg_topic_str.split('/')
                    msg_ThingName = msg_pieces[2]  # now we have thingName...
                    if msg_Version is not None and msg_ThingName == userdata.thisThingNameVersionControl.thisThingName:
                        if msg_Version <= userdata.thisThingNameVersionControl.currLocalVersion:
                            pass  # ignore delta message with old version number
                        else:  # now add this delta message to msgQ
                            # update local version
                            userdata.thisThingNameVersionControl.currLocalVersion = msg_Version
                            ino_id = idMap_entry.get_ino_id()
                            userdata.msgQ.put(str(ino_id) + " " + str(msg.payload))
                    userdata.req_Map_lock.release()
                else:  # A normal new message
                    ino_id = idMap_entry.get_ino_id()
                    userdata.msgQ.put(str(ino_id) + " " + str(msg.payload))  # protocol-style convention needed
    except BaseException:  # ignore clean session = false: msg from pre-subscribed topics
        pass
    userdata.idMap_lock.release()


# myThingName_version
class myThingName_version:
    thisThingName = None
    currLocalVersion = None

    def __init__(self):
        self.thisThingName = None  # default thisThingName is set to None, must call shadow_init
        self.currLocalVersion = -1  # default version is set to -1, must sync it before any update can succeed


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
        return self._Type  # 'update' or 'get' or 'delete'

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
    _cafile = "./certs/aws-iot-rootCA.crt"
    _key = "./certs/privkey.pem"
    _cert = "./certs/cert.pem"
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
    _dynamic_str = ''  # empty string
    _dynamic_ino_id = -1
    _dynamic_queue_size = 0

    # Background Thread
    stop_sign = [False]

    # robust wrapper
    ###################################
    def config(self, src_serverURL, src_serverPORT, src_cafile, src_key, src_cert):
        if len(src_serverURL) != 0:
            self._serverURL = src_serverURL
        if len(str(src_serverPORT)) != 0:
            self._serverPORT = int(src_serverPORT)
        if len(src_cafile) != 0:
            self._cafile = src_cafile
        if len(src_key) != 0:
            self._key = src_key
        if len(src_cert) != 0:
            self._cert = src_cert
        send_output(self.wrapper_debug, self.wrapper_Tx, "G T")

    def __init__(self, srcID, clean_session, protocol):
        try:
            self._iot_mqtt_client_handler = mqtt.Client(srcID, clean_session, self, protocol)
        except BaseException as e:
            send_output(self.wrapper_debug, self.wrapper_Tx, "I F " + e.message)
            return
        self._iot_mqtt_client_handler.on_connect = on_connect
        self._iot_mqtt_client_handler.on_disconnect = on_disconnect
        self._iot_mqtt_client_handler.on_message = on_message
        # start the background thread to periodically check req_Map
        thread.start_new_thread(ThingShadowTimeOutCheck, (self, self._iot_mqtt_client_handler, self.stop_sign,))
        send_output(self.wrapper_debug, self.wrapper_Tx, "I T")

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
        while cnt_sec < MAX_CONN_TIME and self.conn_res == -1:  # waiting for connecting to complete (on_connect)
            cnt_sec += 1
            time.sleep(1)

        if self.conn_res != -1:
            send_output(self.wrapper_debug, self.wrapper_Tx, "C " + str(self.conn_res) + " " + mqtt.connack_string(self.conn_res))  # 0 for connected
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
        while cnt_sec < MAX_CONN_TIME and self.disconn_res == -1:  # waiting for on_disconnect
            cnt_sec += 1
            time.sleep(1)

        if self.disconn_res != -1:
            send_output(self.wrapper_debug, self.wrapper_Tx, "D " + str(self.disconn_res) + " " + mqtt.error_string(self.disconn_res))
        else:
            send_output(self.wrapper_debug, self.wrapper_Tx, "D F Disconnection time out")
        return self.disconn_res

    def subscribe(self, topic, qos, ino_id, is_delta):
        self.idMap_lock.acquire()
        try:
            (rc, mid) = self._iot_mqtt_client_handler.subscribe(topic, qos)
            if ino_id is None:
                raise ValueError("None ino_id")
            new_key = idMap_key(topic, None)  # no clientToken since it is a normal sub
            new_entry = idMap_info(ino_id, False, is_delta != 0)  # This is not a ThingShadow-related topic
            self.idMap[new_key] = new_entry
        except BaseException as e:
            send_output(self.wrapper_debug, self.wrapper_Tx, "S F " + e.message)
            return
        finally:
            self.idMap_lock.release()
        send_output(self.wrapper_debug, self.wrapper_Tx, "S " + str(rc) + " " + mqtt.error_string(rc))
        return rc

    def unsubscribe(self, topic):
        self.idMap_lock.acquire()
        try:
            (rc, mid) = self._iot_mqtt_client_handler.unsubscribe(topic)
            new_key = idMap_key(topic, None)
            ino_id = self.idMap[new_key].get_ino_id()
            del self.idMap[new_key]
        except BaseException as e:
            send_output(self.wrapper_debug, self.wrapper_Tx, "U F " + str(e.message))
            return
        finally:
            self.idMap_lock.release()
        send_output(self.wrapper_debug, self.wrapper_Tx, "U " + str(rc) + " " + str(ino_id) + " " + mqtt.error_string(rc))
        # send back the return value along with the ino_id for C side reference to free the subgroup slot (important)
        return rc

    def lockQueueSize(self):
        # make sure nothing is hapenning in between
        # this would be the number of messages to be processed in the coming yield
        self._dynamic_queue_size = self.msgQ.qsize()
        send_output(self.wrapper_debug, self.wrapper_Tx, "Z T")  # finish with the locking the queue size

    def shadowInit(self, src_thisThingName):
        self.thisThingNameVersionControl.thisThingName = src_thisThingName
        send_output(self.wrapper_debug, self.wrapper_Tx, "SI T")

    def shadowGet(self, ThingName, clientToken, TimeOut, ino_id_accept, ino_id_reject):
        try:
            if ino_id_accept == -1 or ino_id_reject == -1:
                raise Exception("17 shadowGet: Wrong input parameters")
            if self.thisThingNameVersionControl.thisThingName is None:
                raise Exception("18 shadowGet: Should init shadow first")

            # prep req_Map/ref_cnt_Map_get
            self.req_Map_lock.acquire()
            currTime = time.time()
            new_entry = req_Map_info(currTime, TimeOut, "get", ThingName)
            self.req_Map[clientToken] = new_entry
            # refresh get reference count map
            if ThingName in self.ref_cnt_Map_get:
                cnt = self.ref_cnt_Map_get[ThingName] + 1
                self.ref_cnt_Map_get[ThingName] = cnt
            else:
                self.ref_cnt_Map_get[ThingName] = 1
            self.req_Map_lock.release()
            # Now subscribe and publish, QoS0, retain=False
            # subscribe to shadow get accept
            topic_accept = "$aws/things/" + ThingName + "/shadow/get/accepted"
            (rc1, mid) = self._iot_mqtt_client_handler.subscribe(topic_accept, 0)
            self.idMap_lock.acquire()
            new_key = idMap_key(topic_accept, clientToken)
            new_entry = idMap_info(ino_id_accept, True, False)  # This IS a ThingShadow-related topic
            self.idMap[new_key] = new_entry
            self.idMap_lock.release()
            # subscribe to shadow get reject
            topic_reject = "$aws/things/" + ThingName + "/shadow/get/rejected"
            (rc2, mid) = self._iot_mqtt_client_handler.subscribe(topic_reject, 0)
            self.idMap_lock.acquire()
            new_key = idMap_key(topic_reject, clientToken)
            new_entry = idMap_info(ino_id_reject, True, False)  # This IS a ThingShadow-related topic
            self.idMap[new_key] = new_entry
            self.idMap_lock.release()

            time.sleep(2)  # wait for SUBACK

            # publish to shadow get
            topic_get = "$aws/things/" + ThingName + "/shadow/get"
            # should generate JSON payload here...
            temp_dic = dict()
            temp_dic["clientToken"] = clientToken
            payloadJSON = json.dumps(temp_dic)
            # end of JSON payload generation...
            (rc3, mid) = self._iot_mqtt_client_handler.publish(topic_get, payloadJSON, 1, False)
            # feedback
            if rc1 + rc2 + rc3 == 0:
                send_output(self.wrapper_debug, self.wrapper_Tx, "SG T")
            else:
                send_output(self.wrapper_debug, self.wrapper_Tx, "SG F " + str(rc1) + " " + str(rc2) + " " + str(rc3))
        except BaseException as e:
            send_output(self.wrapper_debug, self.wrapper_Tx, "SG F " + e.message)

    def shadowUpdate(self, ThingName, clientToken, TimeOut, payload, ino_id_accept, ino_id_reject, simple_update):
        try:
            if ino_id_accept < -1 or ino_id_reject < -1:
                raise Exception("17 shadowUpdate: Wrong input parameters")
            if self.thisThingNameVersionControl.thisThingName is None:
                raise Exception("18 shadowUpdate: Should init shadow first")
            # From here, this thing shadow is init.
            # prep req_Map/ref_cnt_Map_get/version
            self.req_Map_lock.acquire()
            currTime = time.time()
            new_entry = req_Map_info(currTime, TimeOut, "update", ThingName)
            self.req_Map[clientToken] = new_entry
            # refresh update reference count map
            if ThingName in self.ref_cnt_Map_update:
                cnt = self.ref_cnt_Map_update[ThingName] + 1
                self.ref_cnt_Map_update[ThingName] = cnt
            else:
                self.ref_cnt_Map_update[ThingName] = 1
            self.req_Map_lock.release()
            if simple_update == 0:  # if the user sets simple_update, does not care about the feedback
                # Now subscribe and publish, QoS0, retain=False
                # subscribe to shadow update accept
                topic_accept = "$aws/things/" + ThingName + "/shadow/update/accepted"
                (rc1, mid) = self._iot_mqtt_client_handler.subscribe(topic_accept, 0)
                self.idMap_lock.acquire()
                new_key = idMap_key(topic_accept, clientToken)
                new_entry = idMap_info(ino_id_accept, True, False)  # This IS a ThingShadow-related topic
                self.idMap[new_key] = new_entry
                self.idMap_lock.release()
                # subscribe to shadow update reject
                topic_reject = "$aws/things/" + ThingName + "/shadow/update/rejected"
                (rc2, mid) = self._iot_mqtt_client_handler.subscribe(topic_reject, 0)
                self.idMap_lock.acquire()
                new_key = idMap_key(topic_reject, clientToken)
                new_entry = idMap_info(ino_id_reject, True, False)  # This IS a ThingShadow-related topic
                self.idMap[new_key] = new_entry
                self.idMap_lock.release()

                time.sleep(2)  # wait for SUBACK
            else:
                rc1 = 0
                rc2 = 0
            # publish to shadow get, this is the place to CHECK VERSION...
            topic_get = "$aws/things/" + ThingName + "/shadow/update"
            # should generate JSON payload here...
            temp_dic = json.loads(payload)  # convert payload string to python dictionary, will throw exception if malformed
            # add clientToken
            temp_dic["clientToken"] = clientToken
            payloadJSON = json.dumps(temp_dic)
            # end of JSON payload generation...
            (rc3, mid) = self._iot_mqtt_client_handler.publish(topic_get, payloadJSON, 1, False)
            # feedback
            if rc1 + rc2 + rc3 == 0:
                send_output(self.wrapper_debug, self.wrapper_Tx, "SU T")
            else:
                send_output(self.wrapper_debug, self.wrapper_Tx, "SU F " + str(rc1) + " " + str(rc2) + " " + str(rc3))
        except BaseException as e:
            send_output(self.wrapper_debug, self.wrapper_Tx, "SU F " + e.message)

    def shadowDeleteState(self, ThingName, clientToken, TimeOut, ino_id_accept, ino_id_reject):
        try:
            if ino_id_accept == -1 or ino_id_reject == -1:
                raise Exception("17 shadowDeleteState: Wrong input parameters")
            if self.thisThingNameVersionControl.thisThingName is None:
                raise Exception("18 shadowDeleteState: Should init shadow first")

            currTime = time.time()
            # prep req_Map/ref_cnt_Map_delete
            self.req_Map_lock.acquire()
            new_entry = req_Map_info(currTime, TimeOut, "delete", ThingName)
            self.req_Map[clientToken] = new_entry
            # refresh delete reference count map
            if ThingName in self.ref_cnt_Map_get:
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
            new_entry = idMap_info(ino_id_accept, True, False)  # This IS a ThingShadow-related topic
            self.idMap[new_key] = new_entry
            self.idMap_lock.release()
            # subscribe to shadow delete reject
            topic_reject = "$aws/things/" + ThingName + "/shadow/delete/rejected"
            (rc2, mid) = self._iot_mqtt_client_handler.subscribe(topic_reject, 0)
            self.idMap_lock.acquire()
            new_key = idMap_key(topic_reject, clientToken)
            new_entry = idMap_info(ino_id_reject, True, False)  # This IS a ThingShadow-related topic
            self.idMap[new_key] = new_entry
            self.idMap_lock.release()

            time.sleep(2)  # wait for SUBACK

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
            if rc1 + rc2 + rc3 == 0:
                send_output(self.wrapper_debug, self.wrapper_Tx, "SD T")
            else:
                send_output(self.wrapper_debug, self.wrapper_Tx, "SD F " + str(rc1) + " " + str(rc2) + " " + str(rc3))
        except BaseException as e:
            send_output(self.wrapper_debug, self.wrapper_Tx, "SD F " + e.message)

    def yieldMessage(self):
        try:
            # No more message to echo/Nothing left from the previous message
            if self._dynamic_queue_size == 0 and len(self._dynamic_str) == 0:
                # do a clean-up
                self._dynamic_str = ''
                self._dynamic_queue_size = 0
                self._dynamic_ino_id = -1
                # send feedback
                send_output(self.wrapper_debug, self.wrapper_Tx, "Y F")
            # We have something to echo. Do it chunk by chunk
            else:
                # Nothing left from the previous message, start a new one
                if len(self._dynamic_str) == 0:
                    self._dynamic_str = self.msgQ.get()
                    temp_split = self._dynamic_str.split(' ', 1)
                    self._dynamic_ino_id = int(temp_split[0])  # get ino_id
                    self._dynamic_queue_size -= 1
                    self._dynamic_str = temp_split[1]
                # See if we need to split it
                string2send = None
                more = 0
                if len(self._dynamic_str) + YIELD_METADATA_SIZE + len(str(self._dynamic_ino_id)) > CHUNK_SIZE:
                    more = 1  # there is going to be more chunks coming...
                    stoppoint = CHUNK_SIZE - YIELD_METADATA_SIZE - len(str(self._dynamic_ino_id))
                    string2send = self._dynamic_str[0:stoppoint]
                    self._dynamic_str = self._dynamic_str[stoppoint:]  # update dynamic string
                else:  # last chunk
                    string2send = self._dynamic_str
                    self._dynamic_str = ''  # clear it because it has been sent
                # deliver only one chunk for one yield request
                # Y <ino_id> <more?> <message chunk>
                send_output(self.wrapper_debug, self.wrapper_Tx, "Y " + str(self._dynamic_ino_id) + " " + str(more) + " " + string2send)
        except BaseException as e:
            send_output(self.wrapper_debug, self.wrapper_Tx, "Y F " + e.message)


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

            if command_type in cmd_set:

                signal.alarm(EXIT_TIME_OUT)

                if command_type != 'i' and iot_mqtt_client_obj is None:
                    send_output(debug, buf_o, "X no setup")

                elif command_type == 'i':
                    src_id = get_input(debug, buf_i)
                    try:
                        src_cleansession = False if int(get_input(debug, buf_i)) == 0 else True
                    except ValueError:
                        src_cleansession = None
                    try:
                        src_protocol = mqtt.MQTTv311 if int(get_input(debug, buf_i)) == 4 else mqtt.MQTTv31
                    except ValueError:
                        src_protocol = None
                    # function call
                    if not debug:
                        iot_mqtt_client_obj = iot_mqtt_client(src_id, src_cleansession, src_protocol)
                    else:
                        iot_mqtt_client_obj = mock
                elif command_type == 'g':
                    src_serverURL = get_input(debug, buf_i)
                    src_serverPORT = get_input(debug, buf_i)
                    src_cafile = get_input(debug, buf_i)
                    src_key = get_input(debug, buf_i)
                    src_cert = get_input(debug, buf_i)
                    # function call
                    iot_mqtt_client_obj.config(src_serverURL, src_serverPORT, src_cafile, src_key, src_cert)
                elif command_type == 'c':
                    try:
                        src_keepalive = int(get_input(debug, buf_i))
                    except ValueError:
                        src_keepalive = None
                    # function call
                    iot_mqtt_client_obj.connect(src_keepalive)
                elif command_type == 'p':
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
                elif command_type == 's':
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
                elif command_type == 'u':
                    src_topic = get_input(debug, buf_i)
                    # function call
                    iot_mqtt_client_obj.unsubscribe(src_topic)
                elif command_type == 'y':
                    # function call
                    iot_mqtt_client_obj.yieldMessage()
                elif command_type == 'd':
                    # function call
                    iot_mqtt_client_obj.disconnect()
                elif command_type == 'z':
                    # function call
                    iot_mqtt_client_obj.lockQueueSize()
                elif command_type == 'si':
                    src_thisThingName = get_input(debug, buf_i)
                    # function call
                    iot_mqtt_client_obj.shadowInit(src_thisThingName)
                elif command_type == 'sg':
                    src_ThingName = get_input(debug, buf_i)
                    src_clientToken = get_input(debug, buf_i)
                    try:
                        src_TimeOut = (int)(get_input(debug, buf_i))
                    except ValueError:
                        src_TimeOut = 3  # default timeout for ThingShadow request is 3 sec
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
                elif command_type == 'su':
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
                        src_simple_update = (int)(get_input(debug, buf_i))  # should be 1 or 0, 1 - true, 0 - false
                    except ValueError:
                        src_simple_update = 0
                    # function call
                    iot_mqtt_client_obj.shadowUpdate(src_ThingName, src_clientToken, src_TimeOut, src_payload, src_ino_id_accept, src_ino_id_reject, src_simple_update)
                elif command_type == 'sd':
                    src_ThingName = get_input(debug, buf_i)
                    src_clientToken = get_input(debug, buf_i)
                    try:
                        src_TimeOut = (int)(get_input(debug, buf_i))
                    except ValueError:
                        src_TimeOut = 3  # default timeout for ThingShadow request is 3 sec
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
                elif command_type == '~':  # for debug
                    iot_mqtt_client_obj.stop_sign[0] = True  # stop the background thread
                    time.sleep(1)
                    break
            else:
                pass
    except:
        # Safely terminate the background thread
        if iot_mqtt_client_obj is not None:
            iot_mqtt_client_obj.stop_sign[0] = True
            time.sleep(1)
        send_output(debug, buf_o, "X cmd timeout")


# execute
##################################
runtime_func(False, None, None, None)
