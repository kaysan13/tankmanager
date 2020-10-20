#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import Adafruit_DHT
import os
import glob
import sys
import logging
import time
import requests
import socket
from influxdb import InfluxDBClient
from datetime import datetime
import paho.mqtt.client as mqtt
#########################################
#                Logger                #
#########################################

class Logger:

    def __init__(self):
      self.logDir = "" # Add path log info
      self.logFile = self.logDir + "info.log"

    def checkFolderExist(self, logDir, logFile):
      try:
        if (os.path.exists(logDir)):
          os.makedirs(logDir)
        if (os.path.isfile(logFile)):
          open(logFile, "w+")
      except:
        print("Failed to create new directory.")
      
    def log(self):
      self.checkFolderExist(self.logDir, self.logFile)
      logging.basicConfig(filename=self.logFile, level=logging.INFO, format='%(asctime)s %(message)s')
      logging.info("Tank manager is started ...")

    def info(self, info):
      logging.info(info)

    def error(self, error):
      logging.error(error)

#########################################
#            Mqtt connection            #
#########################################
class MqttForwarder(mqtt.Client):
      
  def __init__(self):
    super().__init__("")
    self.mqttConnected = False
    self.mqttServerUser = '' # Add mqtt user
    self.mqttServerPassword = '' # Add mqtt password
    self.mqttServerIp = '' # Add server ip
    self.mqttServerPort = 1883
    self.logger = Logger()
    self.logger.log()

  def on_connect(self, client, userdata, flags, rc):
    if rc == 0:
      self.mqttConnected = True
      self.logger.info("successful connection with result code "+str(rc))
    else:
      self.logger.error("connection fail with result code %d\n", rc)

  def on_disconnect(self, client, flags, rc):
    self.mqttConnected = False
    self.logger.error("disconnecting with result code "+str(rc))
    self.reconnect()
  
  def publish_data(self, topic, measure):
    self.publish("aquarium/sensor/"+ topic, str(measure))
    self.logger.info("aquarium/sensor/"+ topic + " " + str(measure))

  def connector(self):
    while not self.mqttConnected:
      try:
        self.username_pw_set(username=self.mqttServerUser, password=self.mqttServerPassword)
        self.connect(self.mqttServerIp, self.mqttServerPort, 60)
        self.loop_start()
      except requests.exceptions.ConnectionError:
        self.logger.error('mqtt is not reachable. Waiting 5 seconds to retry.')
      else:
        self.mqttConnected = True

#########################################
#            InfluxDB connection        #
#########################################

class InfluxDBForwarder():

  def __init__(self):
    # super().__init__()
    self.influxdbConnected = False
    self.influxdbServerIp = '' # Add IP server
    self.influxdbServerDb = '' # Add DB name
    self.influxdbPassword = '' # Add DB password
    self.influxDBClient = InfluxDBClient(host=self.influxdbServerIp, username=self.influxdbServerDb, password=self.influxdbPassword, database=self.influxdbServerDb)
    self.logger = Logger()
    self.logger.log()

  def publish_data(self, topic, measure):
    points = [{
      "measurement": topic,
      "tags": {
        "host": socket.gethostname(),
        "region": "" # Add region
      },
      "time": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
      "fields": {
        "value": measure
      }
    }]

    # print(points)
    self.logger.info(points)
    self.influxDBClient.write_points(points)

  def connector(self):
    while not self.influxdbConnected:
      try:
        # self.influxDBClient(host=self.influxdbServerIp, username=self.influxdbServerDb, password=self.influxdbPassword, database=self.influxdbServerDb)

        if not {'name': self.influxdbServerDb} in self.influxDBClient.get_list_database():
          self.logger.error("Database %s creation.." % self.influxdbServerDb)
          self.influxDBClient.create_database(self.influxdbServerDb)
          self.logger.info("Database %s created.." % self.influxdbServerDb)
          self.influxDBClient.switch_database(self.influxdbServerDb)
          self.logger.info("Connected to %s!" % self.influxdbServerDb)

        self.influxdbConnected = True
      except requests.exceptions.ConnectionError:
        self.logger.error('influxdb is not reachable. Waiting 5 seconds to retry.')
      else:
        self.influxdbConnected = True

class TankManager:

  #########################################
  #             DHT11 Services            #
  #########################################
  def getExternalInfo(self):
    DHT_SENSOR = Adafruit_DHT.DHT11
    DHT_PIN_EXT = 5
    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN_EXT)

    if humidity is not None and temperature is not None:
      return (temperature, humidity)

  #########################################
  #            DS18B20 Services           #
  #########################################

  def returnContentFile(self, sensor):
    file = open(sensor)
    contentFile = file.read()
    file.close()
    return contentFile

  def getInfo(self, payload):
    data = payload.split("\n")[1]
    rawData = data.split(" ")[9]
    temperature = float(rawData[2:]) / 1000
    return temperature
    
  def getInternalInfo(self):
    base_dir = '/sys/bus/w1/devices/'
    devices_folder = glob.glob(base_dir + '28*')
    payload = self.returnContentFile(devices_folder[0] + '/w1_slave')
    temperature = self.getInfo(payload)
    if temperature is not None:
      return temperature    

def main():
  tankManager = TankManager()

  mqttForwarder = MqttForwarder()
  mqttForwarder.connector()

  influxDBForwarder = InfluxDBForwarder()
  influxDBForwarder.connector()

  while True:
    try:
      externalInfo = tankManager.getExternalInfo()
      internalInfo = tankManager.getInternalInfo()
      temperatureExternal = externalInfo[0]
      humidityExternal = externalInfo[1]

      mqttForwarder.publish_data("external", temperatureExternal)
      mqttForwarder.publish_data("humidity", humidityExternal)
      mqttForwarder.publish_data("internal", internalInfo)

      influxDBForwarder.publish_data("external", temperatureExternal)
      influxDBForwarder.publish_data("humidity", humidityExternal)
      influxDBForwarder.publish_data("internal", internalInfo)

    except RuntimeError as error:
      print(error.args[0])

    time.sleep(2)

if __name__ == '__main__':
  main()