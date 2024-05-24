from opcua import ua, Server
from mqttDCI import *

test = mqttDCI("192.168.200.226")

# Initialize opcua server
server = Server()
server.set_endpoint("opc.tcp://localhost:4840")

# Name and main object creation
uri = "urn:example-com:entry-module"
idx = server.register_namespace(uri)
root = server.get_objects_node()
entry_module = root.add_object(idx, "EntryModule")


# Variable for each magazine sensor
object_mag1 = entry_module.add_object(idx, "mag1")
mag1_sensor = object_mag1.add_variable(idx, "is_empty1", True)

object_mag2 = entry_module.add_object(idx, "mag2")
mag2_sensor = object_mag2.add_variable(idx, "is_empty2", True)

object_mag3 = entry_module.add_object(idx, "mag3")
mag3_sensor = object_mag3.add_variable(idx, "is_empty3", True)

object_mag4 = entry_module.add_object(idx, "mag4")
mag4_sensor = object_mag4.add_variable(idx, "is_empty4", True)

# magazine_object_type = server.create_object_type(idx, "MagazineObjectType")
# magazine_object_type.add_variable(idx, "is_empty", True)

# object_mag1 = entry_module.add_object(idx, "mag1", object_type=magazine_object_type)
# object_mag2 = entry_module.add_object(idx, "mag2", object_type=magazine_object_type)
# object_mag3 = entry_module.add_object(idx, "mag3", object_type=magazine_object_type)
# object_mag4 = entry_module.add_object(idx, "mag4", object_type=magazine_object_type)

# mag1_sensor = object_mag1.get_child(["{}:is_empty".format(idx)])

global cn 
cn = 0
counter = entry_module.add_variable(idx, "n_pieces_delivered", cn)

def work(self):
    test.work(-1, True)
    update_sensors_state()

def work1(self):
    global cn 
    if (not test.check_magazine_empty(0)): cn = cn + 1
    test.work(0)
    update_sensors_state()

def work2(self):
    global cn 
    if (not test.check_magazine_empty(1)): cn = cn + 1
    test.work(1)
    update_sensors_state()

def work3(self):
    global cn 
    if (not test.check_magazine_empty(2)): cn = cn + 1
    test.work(2)
    update_sensors_state()

def work4(self):
    global cn 
    if (not test.check_magazine_4_empty()): cn = cn + 1
    test.work(3)
    update_sensors_state()

def def_work(self):
    global cn 
    while (not (test.check_magazine_4_empty()&test.check_magazine_empty(1)&test.check_magazine_empty(2)&test.check_magazine_empty(3))):
        r = randrange(4)
        if r in range[0,1,2]:
            if (not test.check_magazine_empty(r)): cn = cn + 1
        else:
            if (not test.check_magazine_4_empty): cn = cn + 1

        test.work(r)

def stop(self):
    test.conveyor_main_stop()
    test.conveyor_side_off()
    test.conveyor_output_stop()


start_method = entry_module.add_method(idx, "Start", work)
eject_method = entry_module.add_method(idx, "Eject_All", def_work)
stop_method = entry_module.add_method(idx, "Stop", stop)

start_method1 = object_mag1.add_method(idx, "Eject1", work1)
start_method2 = object_mag2.add_method(idx, "Eject2", work2)
start_method3 = object_mag3.add_method(idx, "Eject3", work3)
start_method4 = object_mag4.add_method(idx, "Eject4", work4)

def update_sensors_state():
# Update variable value
    mag1_sensor.set_value(test.check_magazine_empty(1))
    mag2_sensor.set_value(test.check_magazine_empty(2))
    mag3_sensor.set_value(test.check_magazine_empty(3))
    mag4_sensor.set_value(test.check_magazine_4_empty())
    counter.set_value(cn)

update_sensors_state()

# Initialize Server
server.start()


