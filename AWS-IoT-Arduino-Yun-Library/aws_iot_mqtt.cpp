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

#include "aws_iot_mqtt.h"
#include "Arduino.h"
#include "stdio.h"
#include "stdlib.h"
#include "string.h"
#include "ctype.h"

#define linux_baud 250000
#define SHADOW_TOPIC_FIXED_LEN 32 // strlen("$aws/things/") + strlen("/shadow/update/delta")
#define RETURN_KEY 13 // ASCII code for '\r'
#define NEXTLINE_KEY 10 // ASCII code for '\n'

const char* OUT_OF_BUFFER_ERR_MSG = "OUT OF BUFFER SIZE";

IoT_Error_t aws_iot_mqtt_client::setup(char* client_id, bool clean_session, MQTTv_t MQTT_version) {
	IoT_Error_t rc = NONE_ERROR;
	if(client_id == NULL) {rc = NULL_VALUE_ERROR;}
	else if(strlen(client_id) >= MAX_BUF_SIZE) {rc = OVERFLOW_ERROR;}
	else {
		my_client_id = client_id;
		// Start Serial1
		Serial1.begin(linux_baud);
		while(!Serial1); // blocking until Serial1 is ready

		exec_cmd("cd .\n", false, false); // placeholder: jump over the welcoming prompt for Open WRT
		exec_cmd("cd /opt/aws-iot\n", false, false);
	    	exec_cmd("~\n", true, false); // exit the previous python process
	    	delay(1000); // delay 1000 ms for all related python script to exit
		exec_cmd("python bin/aws_iot_mqtt_client.py\n", false, false);

		// Create obj
		exec_cmd("i\n", false, false);

		sprintf(rw_buf, "%s\n", client_id);
		exec_cmd(rw_buf, false, false);

		int num_temp = clean_session ? 1 : 0;
		sprintf(rw_buf, "%d\n", num_temp);
		exec_cmd(rw_buf, false, false);

		sprintf(rw_buf, "%u\n", MQTT_version);
		exec_cmd(rw_buf, true, false);

		if(strncmp(rw_buf, "I T", 3) != 0) {rc = SET_UP_ERROR;}
	}

	return rc;
}

IoT_Error_t aws_iot_mqtt_client::config(char* host, int port, char* cafile_path, char* keyfile_path, char* certfile_path) {
	IoT_Error_t rc = NONE_ERROR;

	if(host != NULL && strlen(host) >= MAX_BUF_SIZE) {rc = OVERFLOW_ERROR;}
	else if(cafile_path != NULL && strlen(cafile_path) >= MAX_BUF_SIZE) {rc = OVERFLOW_ERROR;}
	else if(keyfile_path != NULL && strlen(keyfile_path) >= MAX_BUF_SIZE) {rc = OVERFLOW_ERROR;}
	else if(certfile_path != NULL && strlen(certfile_path) >= MAX_BUF_SIZE) {rc = OVERFLOW_ERROR;}
	else {
		const char* helper = "";
		const char* placeholder = "";
		exec_cmd("g\n",false, false);

		helper = host == NULL ? placeholder : host;
		sprintf(rw_buf, "%s\n", helper);
		exec_cmd(rw_buf, false, false);

		sprintf(rw_buf, "%d\n", port);
		exec_cmd(rw_buf, false, false);

		helper = cafile_path == NULL ? placeholder : cafile_path;
		sprintf(rw_buf, "%s\n", helper);
		exec_cmd(rw_buf, false, false);

		helper = keyfile_path == NULL ? placeholder : keyfile_path;
		sprintf(rw_buf, "%s\n", helper);
		exec_cmd(rw_buf, false, false);

		helper = certfile_path == NULL ? placeholder : certfile_path;
		sprintf(rw_buf, "%s\n", helper);
		exec_cmd(rw_buf, true, false);

		if(strncmp(rw_buf, "G T", 3) != 0) {rc = CONFIG_ERROR;}
	}

	return rc;
}

IoT_Error_t aws_iot_mqtt_client::connect(int keepalive_interval) {
	IoT_Error_t rc = NONE_ERROR;
	exec_cmd("c\n", false, false);

	sprintf(rw_buf, "%d\n", keepalive_interval);
	exec_cmd(rw_buf, true, false);

	if(strncmp(rw_buf, "C 0", 3) != 0) {rc = CONNECT_ERROR;}

	return rc;
}

IoT_Error_t aws_iot_mqtt_client::publish(char* topic, char* payload, int payload_len, int qos, bool retain) {
	IoT_Error_t rc = NONE_ERROR;
	if(topic == NULL || payload == NULL) {rc = NULL_VALUE_ERROR;}
	else if(strlen(topic) >= MAX_BUF_SIZE || payload_len >= MAX_BUF_SIZE) {rc = OVERFLOW_ERROR;}
	else {
		exec_cmd("p\n", false, false);

		sprintf(rw_buf, "%s\n", topic);
		exec_cmd(rw_buf, false, false);

		sprintf(rw_buf, "%s\n", payload);
		exec_cmd(rw_buf, false, false);

		sprintf(rw_buf, "%d\n", qos);
		exec_cmd(rw_buf, false, false);

		int num_temp = retain ? 1 : 0;
		sprintf(rw_buf, "%d\n", num_temp);
		exec_cmd(rw_buf, true, false);

		if(strncmp(rw_buf, "P 0", 3) != 0) {rc = PUBLISH_ERROR;}
	}
	return rc;
}

IoT_Error_t aws_iot_mqtt_client::subscribe(char* topic, int qos, message_callback cb) {
	return base_subscribe(topic, qos, cb, 0);
}

IoT_Error_t aws_iot_mqtt_client::base_subscribe(char* topic, int qos, message_callback cb, int is_delta) {
	IoT_Error_t rc = NONE_ERROR;
	if(topic == NULL) {rc = NULL_VALUE_ERROR;}
	else if(strlen(topic) >= MAX_BUF_SIZE) {rc = OVERFLOW_ERROR;}
	else {
		// find unused slots for new subscribe
		int i;
		for(i = 0; i < MAX_SUB; i++) {
			if(!sub_group[i].is_used) {break;}
		}
		if(i < MAX_SUB) {
			sub_group[i].is_used = true;
			sub_group[i].callback = cb;

			exec_cmd("s\n", false, false);

			sprintf(rw_buf, "%s\n", topic);
			exec_cmd(rw_buf, false, false);

			sprintf(rw_buf, "%d\n", qos);
			exec_cmd(rw_buf, false, false);

			sprintf(rw_buf, "%d\n", i); // ino_id
			exec_cmd(rw_buf, false, false);

			sprintf(rw_buf, "%d\n", is_delta); // is_delta
			exec_cmd(rw_buf, true, false);

			if(strncmp(rw_buf, "S 0", 3) != 0) {rc = SUBSCRIBE_ERROR;}
		}
		else {rc = OUT_OF_SKETCH_SUBSCRIBE_MEMORY;}
	}
	return rc;
}

IoT_Error_t aws_iot_mqtt_client::unsubscribe(char* topic) {
	IoT_Error_t rc = NONE_ERROR;
	if(topic == NULL) {rc = NULL_VALUE_ERROR;}
	else if(strlen(topic) >= MAX_BUF_SIZE) {rc = OVERFLOW_ERROR;}
	else {
		exec_cmd("u\n", false, false);

		sprintf(rw_buf, "%s\n", topic);
		exec_cmd(rw_buf, true, false);

		if(strncmp(rw_buf, "U F", 3) == 0) {rc = UNSUBSCRIBE_ERROR;}
		else {
			char* saveptr;
			char* p;
			p = strtok_r(rw_buf, " ", &saveptr); // 'U'
			p = strtok_r(NULL, " ", &saveptr); // return number
			int paho_ret;
			if(p == NULL) {rc = UNSUBSCRIBE_ERROR;}
			else {paho_ret = is_num(p) ? atoi(p) : -1;}
			if(paho_ret == 0) {
				p = strtok_r(NULL, " ", &saveptr); // ino_id
				int ino_id = -1;
				if(p != NULL) ino_id = is_num(p) ? atoi(p) : -1;
				if(ino_id >= 0 && ino_id < MAX_SUB) {
					sub_group[ino_id].is_used = false;
					sub_group[ino_id].callback = NULL;
				}
				else {rc = UNSUBSCRIBE_ERROR;}
			}
		}
	}
	return rc;
}

IoT_Error_t aws_iot_mqtt_client::yield() {
	IoT_Error_t rc = NONE_ERROR;
	exec_cmd("z\n", true, false); // tell the python runtime to lock the current msg queue size
	if(strcmp(rw_buf, "Z T") != 0) {rc = YIELD_ERROR;} // broken protocol
	else { // start the BIG yield loop
		while(true) {
			exec_cmd("y\n", true, false);
			if(strcmp(rw_buf, "Y F") == 0) {break;}
			if(rw_buf[0] != 'Y') { // filter out garbage feedback
				rc = YIELD_ERROR;
				break;
			}
			// From here, there is a new message chunk in rw_buf
			char* saveptr;
			char* p;
			p = strtok_r(rw_buf, " ", &saveptr); // 'Y'
			p = strtok_r(NULL, " ", &saveptr); // ino_id
			if(p != NULL) {
			  	int ino_id = is_num(p) ? atoi(p) : -1;
			    size_t id_len = strlen(p);
			    p = strtok_r(NULL, " ", &saveptr); // more chunk?
			    if(p != NULL) {
			      	int more = is_num(p) ? atoi(p) : -1;
			      	if(more != 1 && more != 0) { // broken protocol
			      		rc = YIELD_ERROR;
			      		break;
			      	}
			      	else {
			      		char* payload = rw_buf + id_len + 5; // step over the protocol and get payload
			      		if(strlen(msg_buf) + strlen(payload) > MAX_BUF_SIZE) {
			      			rc = OVERFLOW_ERROR; // if it is exceeding MAX_BUF_SIZE, return the corresponding error code
			      		}
			      		else {strcat(msg_buf, payload);}
			      		if(more == 0) { // This is the end of this message, do callback and clean up
						    // user callback, watch out for ino_id boundary issue and callback registration
						    if(ino_id >= 0 && ino_id < MAX_SUB && sub_group[ino_id].is_used && sub_group[ino_id].callback != NULL) {

								if(rc == NONE_ERROR) {
									sub_group[ino_id].callback(msg_buf, (int)strlen(msg_buf));
								}
								if(rc == OVERFLOW_ERROR) {
									sub_group[ino_id].callback((char*)OUT_OF_BUFFER_ERR_MSG, (int)strlen(OUT_OF_BUFFER_ERR_MSG));
								}

                                if(sub_group[ino_id].ThingShadow != -1) {
                                    sub_group[ino_id].is_used = false;
                                    sub_group[ino_id].callback = NULL;
                                    int pair = sub_group[ino_id].ThingShadow;
                                    sub_group[pair].is_used = false;
                                    sub_group[pair].callback = NULL;
                                    sub_group[ino_id].ThingShadow = -1;
                                    sub_group[pair].ThingShadow = -1;
                                }
						    }
						    // clean up
						    msg_buf[0] = '\0'; // mark msg_buf as 'unused', ready for the next flush
			      		}
			      		// more to come? do NOTHING to msg_buf and DO NOT call callback
			      	}
			    }
			    else {
			      	rc = YIELD_ERROR;
			      	break;
			    }
			}
			else {
			    rc = YIELD_ERROR;
			    break;
			}
		}
	}
	return rc;
}

IoT_Error_t aws_iot_mqtt_client::disconnect() {
	IoT_Error_t rc = NONE_ERROR;
	exec_cmd("d\n", true, false);

	if(strncmp(rw_buf, "D 0", 3) != 0) {rc = DISCONNECT_ERROR;}
	return rc;
}

// ThingShadow-support API
IoT_Error_t aws_iot_mqtt_client::shadow_init(char* thingName) {
	IoT_Error_t rc = NONE_ERROR;
	if(thingName == NULL) {rc = NULL_VALUE_ERROR;}
	else if(strlen(thingName) >= MAX_BUF_SIZE) {rc = OVERFLOW_ERROR;}
	else {
		exec_cmd("si\n", false, false);

		sprintf(rw_buf, "%s\n", thingName);
		exec_cmd(rw_buf, true, false);

		if(strcmp(rw_buf, "SI T") != 0) {rc = SHADOW_INIT_ERROR;}
	}
	return rc;
}

IoT_Error_t aws_iot_mqtt_client::shadow_register_delta_func(char* thingName, message_callback cb) {
	IoT_Error_t rc = NONE_ERROR;
    char temp[MAX_SHADOW_TOPIC_LEN];
	if(thingName == NULL) {rc = NULL_VALUE_ERROR;}
	else if(strlen(thingName) + SHADOW_TOPIC_FIXED_LEN >= MAX_SHADOW_TOPIC_LEN) {rc = OVERFLOW_ERROR;}
	else {
		sprintf(temp, "$aws/things/%s/shadow/update/delta", thingName);
		// default: subscribe to delta topic using QoS1
		rc = base_subscribe(temp, 1, cb, 1);
	}
	return rc;
}

IoT_Error_t aws_iot_mqtt_client::shadow_unregister_delta_func(char* thingName) {
	IoT_Error_t rc = NONE_ERROR;
    char temp[MAX_SHADOW_TOPIC_LEN];
	if(thingName == NULL) {rc = NULL_VALUE_ERROR;}
	else if(strlen(thingName) + SHADOW_TOPIC_FIXED_LEN >= MAX_SHADOW_TOPIC_LEN) {rc = OVERFLOW_ERROR;}
	else {
		sprintf(temp, "$aws/things/%s/shadow/update/delta", thingName);
		rc = unsubscribe(temp);
	}
	return rc;
}

IoT_Error_t aws_iot_mqtt_client::shadow_get(char* thingName, message_callback cb, int timeout) {
	IoT_Error_t rc = NONE_ERROR;
	if(thingName == NULL) {rc = NULL_VALUE_ERROR;}
	else if(strlen(thingName) >= MAX_BUF_SIZE) {rc = OVERFLOW_ERROR;}
	else {
		exec_cmd("sg\n", false, false);

		sprintf(rw_buf, "%s\n", thingName);
		exec_cmd(rw_buf, false, false);

		sprintf(rw_buf, "%s-%d\n", my_client_id, ThingShadow_req_num++);
		exec_cmd(rw_buf, false, false);

		sprintf(rw_buf, "%d\n", timeout);
		exec_cmd(rw_buf, false, false);

		// find unused slots for new subscribe
		// acccept
		int i;
		for(i = 0; i < MAX_SUB; i++) {
			if(!sub_group[i].is_used) {break;}
		}
		if(i < MAX_SUB) {
			sub_group[i].is_used = true;
			sub_group[i].callback = cb;
		}
		// reject
		int j;
		for(j = 0; j < MAX_SUB; j++) {
			if(!sub_group[j].is_used) {break;}
		}
		if(j < MAX_SUB) {
			sub_group[j].is_used = true;
			sub_group[j].callback = cb;
		}

		if(i < MAX_SUB && j < MAX_SUB) {
	        sub_group[i].ThingShadow = j;
	        sub_group[j].ThingShadow = i;

			sprintf(rw_buf, "%d\n", i);
			exec_cmd(rw_buf, false, false);

			sprintf(rw_buf, "%d\n", j);
			exec_cmd(rw_buf, true, false);

			if(strcmp(rw_buf, "SG T") != 0) {rc = SHADOW_GET_ERROR;}
		}
		else {rc = OUT_OF_SKETCH_SUBSCRIBE_MEMORY;}
	}
	return rc;
}

IoT_Error_t aws_iot_mqtt_client::shadow_update(char* thingName, char* payload, int payload_len, message_callback cb, int timeout) {
	IoT_Error_t rc = NONE_ERROR;
	if(thingName == NULL || payload == NULL) {rc = NULL_VALUE_ERROR;}
	else if(strlen(thingName) >= MAX_BUF_SIZE || payload_len >= MAX_BUF_SIZE) {rc = OVERFLOW_ERROR;}
	else {
		exec_cmd("su\n", false, false);

		sprintf(rw_buf, "%s\n", thingName);
		exec_cmd(rw_buf, false, false);

		sprintf(rw_buf, "%s-%d\n", my_client_id, ThingShadow_req_num++);
		exec_cmd(rw_buf, false, false);

		sprintf(rw_buf, "%d\n", timeout);
		exec_cmd(rw_buf, false, false);

		sprintf(rw_buf, "%s\n", payload);
		exec_cmd(rw_buf, false, false);

		int i = -1, j = -1;
		// if users care about feedback, find unused slots for new subscribe
		if(cb != NULL) {
			// acccept
			for(i = 0; i < MAX_SUB; i++) {
				if(!sub_group[i].is_used) {break;}
			}
			if(i < MAX_SUB) {
				sub_group[i].is_used = true;
				sub_group[i].callback = cb;
			}
			// reject
			for(j = 0; j < MAX_SUB; j++) {
				if(!sub_group[j].is_used) {break;}
			}
			if(j < MAX_SUB) {
				sub_group[j].is_used = true;
				sub_group[j].callback = cb;
			}
		}

		if(i < MAX_SUB && j < MAX_SUB) { // include simple shadow update where no subscription is made
			if(i != -1 && j != -1) { // only for normal shadow update, need to unsubscribe
	        	sub_group[i].ThingShadow = j;
	        	sub_group[j].ThingShadow = i;
	        }

			sprintf(rw_buf, "%d\n", i);
			exec_cmd(rw_buf, false, false);

			sprintf(rw_buf, "%d\n", j);
			exec_cmd(rw_buf, false, false);

			int simple = cb == NULL ? 1 : 0;
			sprintf(rw_buf, "%d\n", simple);
			exec_cmd(rw_buf, true, false);

			if(strcmp(rw_buf, "SU T") != 0) {rc = SHADOW_UPDATE_ERROR;}
		}
		else {rc = OUT_OF_SKETCH_SUBSCRIBE_MEMORY;}
	}
	return rc;
}

IoT_Error_t aws_iot_mqtt_client::shadow_delete(char* thingName, message_callback cb, int timeout) {
	IoT_Error_t rc = NONE_ERROR;
	if(thingName == NULL) {rc = NULL_VALUE_ERROR;}
	else if(strlen(thingName) >= MAX_BUF_SIZE) {rc = OVERFLOW_ERROR;}
	else {
		exec_cmd("sd\n", false, false);

		sprintf(rw_buf, "%s\n", thingName);
		exec_cmd(rw_buf, false, false);

		sprintf(rw_buf, "%s-%d\n", my_client_id, ThingShadow_req_num++);
		exec_cmd(rw_buf, false, false);

		sprintf(rw_buf, "%d\n", timeout);
		exec_cmd(rw_buf, false, false);

		// find unused slots for new subscribe
		// acccept
		int i;
		for(i = 0; i < MAX_SUB; i++) {
			if(!sub_group[i].is_used) {break;}
		}
		if(i < MAX_SUB) {
			sub_group[i].is_used = true;
			sub_group[i].callback = cb;
		}
		// reject
		int j;
		for(j = 0; j < MAX_SUB; j++) {
			if(!sub_group[j].is_used) {break;}
		}
		if(j < MAX_SUB) {
			sub_group[j].is_used = true;
			sub_group[j].callback = cb;
		}

		if(i < MAX_SUB && j < MAX_SUB) {
	        sub_group[i].ThingShadow = j;
	        sub_group[j].ThingShadow = i;

			sprintf(rw_buf, "%d\n", i);
			exec_cmd(rw_buf, false, false);

			sprintf(rw_buf, "%d\n", j);
			exec_cmd(rw_buf, true, false);

			if(strcmp(rw_buf, "SD T") != 0) {rc = SHADOW_DELETE_ERROR;}
		}
		else {rc = OUT_OF_SKETCH_SUBSCRIBE_MEMORY;}
	}
	return rc;
}

// Exec command and get feedback into rw_buf
void aws_iot_mqtt_client::exec_cmd(const char* cmd, bool wait, bool single_line) {
	// Write cmd
	int cnt = Serial1.write(cmd) + 1;
	timeout_flag = false;
	int timeout_sec = 0;
	// step1: forget the echo
	while(timeout_sec < CMD_TIME_OUT && cnt != 0) {
		if(Serial1.read() != -1) {cnt--;}
		else { // only start counting the timer when the serial1 is keeping us waiting...
			delay(5); // echo comes faster than python runtime client. Decreasing delay to avoid latency issue
			timeout_sec++;
		}
	}
	timeout_flag = timeout_sec == CMD_TIME_OUT; // Update timeout flag
	int ptr = 0;
	if(!timeout_flag) { // step 1 clear
		timeout_flag = false;
		timeout_sec = 0;
		// step2: waiting
		delay(10);
		if(wait) {
			while(timeout_sec < CMD_TIME_OUT && !Serial1.available()) {
				delay(100); // 0.1 sec
				timeout_sec++;
			}
		}
		timeout_flag = timeout_sec == CMD_TIME_OUT; // Update timeout flag
		if(!timeout_flag) { // step 2 clear
			// read feedback
		    // will read all the available data in Serial1 but only store the message with the limit of MAX_BUF_SIZE
			bool stop_sign = false;
			while(Serial1.available()) {
				int cc = Serial1.read();
				if(cc != -1) {
					if(cc == NEXTLINE_KEY || ptr == MAX_BUF_SIZE - 1) {
						stop_sign = true;
						if(single_line) {break;}
					} // end of feedback
					if(!stop_sign && cc != RETURN_KEY) {
						rw_buf[ptr++] = (char)cc;
					}
				}
			}
		}
	}
	timeout_flag = false; // Clear timeout flag
	rw_buf[ptr] = '\0'; // add terminator in case of garbage data in rw_buf
}

bool aws_iot_mqtt_client::is_num(char* src) {
	bool rc = true;
	if(src == NULL) {rc = false;}
	else {
		char* p = src;
		while(*p != '\0') {
			if(*p > '9' || *p < '0') {
				rc = false;
				break;
			}
			p++;
		}
	}
	return rc;
}
