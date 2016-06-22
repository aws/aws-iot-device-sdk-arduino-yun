/*
 * Copyright 2010-2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

#include <aws_iot_mqtt.h>
#include <aws_iot_version.h>
#include "aws_iot_config.h"

aws_iot_mqtt_client myClient;
char JSON_buf[50];
char float_buf[5];
float reportedTemp = 70.0;
float desiredTemp = 70.0;
int cnt = 0;
int rc = 1;
bool success_connect = false;

bool print_log(const char* src, int code) {
  bool ret = true;
  if(code == 0) {
    Serial.print("[LOG] command: ");
    Serial.print(src);
    Serial.println(" completed.");
    ret = true;
  }
  else {
    Serial.print("[ERR] command: ");
    Serial.print(src);
    Serial.print(" code: ");
    Serial.println(code);
    ret = false;
  }
  Serial.flush();
  return ret;
}

void msg_callback_delta(char* src, unsigned int len, Message_status_t flag) {
  if(flag == STATUS_NORMAL) {
    // Get Temp section in delta messages
    print_log("getDeltaKeyValue", myClient.getDeltaValueByKey(src, "Temp", JSON_buf, 50));
    desiredTemp = String(JSON_buf).toFloat();
  }
}

void setup() {
  Serial.begin(115200);
  while(!Serial);

  char curr_version[80];
  sprintf(curr_version, "AWS IoT SDK Version(dev) %d.%d.%d-%s\n", VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH, VERSION_TAG);
  Serial.println(curr_version);

  if(print_log("setup", myClient.setup(AWS_IOT_CLIENT_ID))) {
    if(print_log("config", myClient.config(AWS_IOT_MQTT_HOST, AWS_IOT_MQTT_PORT, AWS_IOT_ROOT_CA_PATH, AWS_IOT_PRIVATE_KEY_PATH, AWS_IOT_CERTIFICATE_PATH))) {
      if(print_log("connect", myClient.connect())) {
        success_connect = true;
        print_log("shadow init", myClient.shadow_init(AWS_IOT_MY_THING_NAME));
        print_log("register thing shadow delta function", myClient.shadow_register_delta_func(AWS_IOT_MY_THING_NAME, msg_callback_delta));
      }
    }
  }
}

void loop() {
  if(success_connect) {
    // If the desired temperature is set to a higher value, start heating.
    if(desiredTemp - reportedTemp > 0.001) {reportedTemp += 0.1;}
    // If the desired temperature is set to a lower value, start cooling.
    else if(reportedTemp - desiredTemp > 0.001) {reportedTemp -= 0.1;}
    dtostrf(reportedTemp, 4, 1, float_buf);
    float_buf[4] = '\0';
    sprintf(JSON_buf, "{\"state\":{\"reported\":{\"Temp\":%s}}}", float_buf);
    print_log("shadow update", myClient.shadow_update(AWS_IOT_MY_THING_NAME, JSON_buf, strlen(JSON_buf), NULL, 5));
    if(myClient.yield()) {
      Serial.println("Yield failed.");
    }
    delay(1000); // check for incoming delta per 1000 ms
  }
}
