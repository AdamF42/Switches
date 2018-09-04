import threading
import time
from gpiozero import LED
import os
import signal
import logging.handlers
import sys
import configparser
import paho.mqtt.client as mqtt
import logging

# ################################# Log Stuff #################################
os.makedirs('logs', exist_ok=True)  # Python > 3.2
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fh = logging.handlers.TimedRotatingFileHandler(
    filename='logs/system.log', when='D', backupCount=7)
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(threadName)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

# ########################### MQTT Connection Info #############################
config = configparser.ConfigParser()
config.read('config.ini')
ca_certificate = config['SSL']['CERTIFICATE_CA']
client_certificate = config['SSL']['CERTIFICATE_CLIENT']
client_key = config['SSL']['CERTIFICATE_CLIENT_KEY']
mqtt_server_host = config['MQTT']['MQTT_BROKER_ADD']
mqtt_server_port = int(config['MQTT']['MQTT_BROKER_PORT'])
mqtt_keepalive = int(config['MQTT']['MQTT_KEEPALIVE_TIME'])
command_key = config['MQTT']['COMMAND_KEY']
processed_command_key = config['MQTT']['SUCCESSFULLY_PROCESSED_COMMAND_KEY']
cmd_turn_on = config['MQTT']['CMD_TURN_ON']
cmd_turn_off = config['MQTT']['CMD_TURN_OFF']
commands_topic = config['MQTT']['CMD_TURN_OFF']
processed_commands_topic = config['MQTT']['CMD_TURN_OFF']

if __name__ == "__main__":
    from GPIO.Switch import Switch


    def signal_handler(signum):
        logger.debug("Received signal {}".format(signum))
        os.kill(os.getpid(), signal.SIGKILL)


    # register signal handler
    signal.signal(signal.SIGHUP, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGQUIT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # ###################### Setup backgroud threads ######################
    threads = []
    for switch in config.options('SWITCHES'):
        client = mqtt.Client(protocol=mqtt.MQTTv311)
        client.tls_set(ca_certs=ca_certificate,
                       certfile=client_certificate,
                       keyfile=client_key)
        client.connect(host=mqtt_server_host,
                       keepalive=mqtt_keepalive,
                       port=mqtt_server_port)
        gpio_switch = LED(int(config.get('SWITCHES', switch)))
        switch_one = Switch(client, gpio_switch, switch)
        thread = threading.Thread(
            target=switch_one.process_commands, name=switch)
        thread.daemon = True
        thread.start()
        threads.append(thread)

    # ######################## Setup Main thread ##########################
    while True:
        for x in range(50, 0):
            LED(x).off()
            time.sleep(1)
            print(x)
            LED(x).on()

        time.sleep(5)
        # check if all threads are still alive
        for thread in threads:
            if thread.isAlive():
                continue
            # something went wrong, bailing out
            msg = 'Thread "%s" died, terminating now.' % thread.name
            logger.error(msg)
            sys.exit(1)
