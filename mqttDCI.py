from random import randrange
from paho.mqtt import publish
from paho.mqtt import subscribe
from pyModbusTCP.client import ModbusClient
from pyModbusTCP.utils import set_bit
from pyModbusTCP.utils import reset_bit
from pyModbusTCP.utils import test_bit
from time import sleep

import threading
import multiprocessing
import paho.mqtt.client as mqtt

class mqttDCI:
     #Konstanten
    DIGITAL_INPUT_STARTING_ADDRESS = 8001
    DIGITAL_OUTPUT_STARTING_ADDRESS = 8011

    ANALOG_INPUT_STARTING_ADDRESS = 8015
    ANALOG_OUTPUT_STARTING_ADDRESS = 8015


    def __init__(self, ip_addr, read_write_sem = multiprocessing.BoundedSemaphore(value=1)):
        """
        Konstruktor des DistributionCenterInputModules.

        :param ip_addr Ip-Adresse des Modbus Knoten, welche für die Bearbeiten Station zuständig ist (String)
        :param read_write_sem Semaphore die übergeben werden kann, wenn nicht erwünscht ist, dass 2 Module gleichzeitig read/write Befehle schicken
        """
        try:
            #Erzeugt eine Verbindung zum Modbus mit der ip_addr
            self.client = ModbusClient(host=ip_addr, auto_open=True, auto_close=True)
        except ValueError:
            print("Error with host param")

        self.sem = multiprocessing.BoundedSemaphore(value=1)

        self.read_write_sem = read_write_sem

    def get_output_register(self, offset = 0, anzahl = 1):
        """
        Gibt die Output Register des Modbus zurück.

        :param offset Offset zur DIGITAL_OUTPUT_STARTING_ADDRESS
        :param anzahl Anzahl der Register die ausgelesen werden
        :returns Liste der gelesenen Register (oder garnichts wenn lesen fehlschlägt)
        :rtype list of int or none
        """
        with self.read_write_sem:
            result = None
            while result == None:
                result = self.client.read_holding_registers(reg_addr=self.DIGITAL_OUTPUT_STARTING_ADDRESS + offset,reg_nb = anzahl)
            return result

    def get_input_register(self, offset = 0, anzahl = 1):
        """
        Gibt die Input Register des Modbus zurück.

        :param offset Offset zur DIGITAL_INPUT_STARTING_ADDRESS
        :param anzahl Anzahl der Register die ausgelesen werden
        :returns Liste der gelesenen Register (oder garnichts wenn lesen fehlschlägt)
        :rtype list of int or none
        """
        with self.read_write_sem:
            result = None
            while result == None:
                result = self.client.read_holding_registers(reg_addr=self.DIGITAL_INPUT_STARTING_ADDRESS + offset,reg_nb = anzahl)
            return result

    def set_output_register(self, register, offset = 0):
        """
        Überschreibt das Output Register des Modbus.

        :param register List of int die in das Register geschrieben werden soll
        :param offset Offset zur DIGITAL_OUTPUT_STARTING_ADDRESS
        """
        with self.read_write_sem:
            result = None
            while result == None:
                result = self.client.write_multiple_registers(self.DIGITAL_OUTPUT_STARTING_ADDRESS + offset, register)

    def conveyor_main_left(self):
        """
        Das Laufband für die Magazine bewegt sich nach links.
        """
        with self.sem:
            reg = self.get_output_register(offset=1)
            reg[0] = set_bit(reg[0],2)
            reg[0] = reset_bit(reg[0],3)
            reg[0] = reset_bit(reg[0], 0) #Laufband stopp löschen
            self.set_output_register(reg, offset=1)

    def conveyor_main_right(self):
        """
        Das Laufband für die Magazine bewegt sich nach rechts.
        """
        with self.sem:
            reg = self.get_output_register(offset=1)
            reg[0] = set_bit(reg[0],3)
            reg[0] = reset_bit(reg[0],2)
            reg[0] = reset_bit(reg[0], 0) #Laufband stopp löschen
            self.set_output_register(reg, offset=1)

    def conveyor_main_stop(self):
        """
        Stoppt das Laufband für die Magazine.
        """
        with self.sem:
            reg = self.get_output_register(offset=1)
            reg[0] = set_bit(reg[0], 0)
            self.set_output_register(reg, offset=1)

    def conveyor_main_continue(self):
        """
        Lässt das Laufband für die Magazine weiterfahren.
        """
        with self.sem:
            reg = self.get_output_register(offset=1)
            reg[0] = reset_bit(reg[0], 0)
            self.set_output_register(reg, offset=1)

    def conveyor_main_slowdown(self):
        """
        Aktiviert die Drosselung für das Laufband der Magazine.
        """
        with self.sem:
            reg = self.get_output_register(offset=1)
            reg[0] = set_bit(reg[0], 1)
            self.set_output_register(reg, offset=1)

    def conveyor_main_slowdown_off(self):
        """
        Deaktiviert die Drosselung für das Laufband der Magazine.
        """
        with self.sem:
            reg = self.get_output_register(offset=1)
            reg[0] = reset_bit(reg[0], 1)
            self.set_output_register(reg, offset=1)
        
    def conveyor_side_on(self):
        """
        Aktiviert das Laufband für das Massenmagazin.
        """
        with self.sem:
            reg = self.get_output_register(offset=1)
            reg[0] = set_bit(reg[0], 4)
            self.set_output_register(reg, offset=1)

    def conveyor_side_off(self):
        """
        Deaktiviert das Laufband für das Massenmagazin.
        """
        with self.sem:
            reg = self.get_output_register(offset=1)
            reg[0] = reset_bit(reg[0], 4)
            self.set_output_register(reg, offset=1)        
        
    def seperator_main_set(self):
        """
        Setzt den Vereinzeler am Ausgang.
        """
        with self.sem:
            reg = self.get_output_register(offset=1)
            reg[0] = set_bit(reg[0], 7)
            self.set_output_register(reg, offset=1)

    def seperator_main_reset(self):
        """
        Setzt den Vereinzeler am Ausgang zurück.
        """
        with self.sem:
            reg = self.get_output_register(offset=1)
            reg[0] = reset_bit(reg[0], 7)
            self.set_output_register(reg, offset=1)

    def seperator_side_set(self):
        """
        Setzt den Vereinzeler am Massenmagazin.
        """
        with self.sem:
            reg = self.get_output_register(offset=1)
            reg[0] = set_bit(reg[0], 8)
            self.set_output_register(reg, offset=1)        

    def seperator_side_reset(self):
        """
        Setzt den Vereinzeler am Massenmagazin zurück.
        """
        with self.sem:
            reg = self.get_output_register(offset=1)
            reg[0] = reset_bit(reg[0], 8)
            self.set_output_register(reg, offset=1)        

    def magazine_retract(self, magazine_id):
        """
        Fährt das ausgewählte Magazin ein.
        :param magazine_id die Nummer des einzufahrenden Magazins (Magazin 1 = 1,...)
        """
        with self.sem:
            bit_nr = 9

            if magazine_id == 2:
                bit_nr = 11
            if magazine_id == 3:
                bit_nr = 13

            reg = self.get_output_register(offset=1)
            reg[0] = reset_bit(reg[0], bit_nr + 1)
            reg[0] = set_bit(reg[0], bit_nr)
            self.set_output_register(reg, offset=1)        

    def magazine_eject(self, magazine_id):
        """
        Fährt das ausgewählte Magazin aus.
        :param magazine_id die Nummer des auszufahrenden Magazins (Magazin 1 = 1,...)
        """
        with self.sem:
                bit_nr = 10
                if magazine_id == 2:
                    bit_nr = 12
                if magazine_id == 3:
                    bit_nr = 14

                reg = self.get_output_register(offset=1)
                reg[0] = reset_bit(reg[0], bit_nr - 1)
                reg[0] = set_bit(reg[0], bit_nr)
                self.set_output_register(reg,offset=1)        

    def ejector_lock_on(self):
        """
        Aktiviert die Sperre für den  Auswerfer.
        """
        with self.sem:
                reg = self.get_output_register(offset=0)
                reg[0] = reset_bit(reg[0], 1)
                self.set_output_register(reg, offset=0)        

    def ejector_lock_off(self):
        """
        Deaktiviert die Sperre für den ausgewählten Auswerfer.
        """ 
        with self.sem:
                reg = self.get_output_register(offset=0)
                reg[0] = set_bit(reg[0], 1)
                self.set_output_register(reg, offset=0)        

    def ejector_left(self, lock_off = True):
        """
        Fährt den Auswerfer nach links aus.
        :param lock_off Boolean ob die Sperre ausgeschaltet werden soll (nur wichtig um in die Mittelposition zu gehen)
        """
        
        with self.sem:                
            #Verwendung von 2 get_output_register Anfragen statt 1er mit Anzahl=2 weil, sich die ergebnisse zu unterscheiden scheinen
            reg0 = self.get_output_register(offset=0)
            reg1 = self.get_output_register(offset=1)
            reg0[0] = set_bit(reg0[0], 0)
            reg1[0] = set_bit(reg1[0], 15)

            reg3 = [reg0[0],reg1[0]]
            
            self.set_output_register(reg3, offset=0)
            #self.set_output_register(reg0, offset=0)
            #self.set_output_register(reg1, offset=1)
            
            sleep(0.05)
            reg1[0] = reset_bit(reg1[0], 15)
            self.set_output_register(reg1, offset=1)
        if lock_off:
            self.ejector_lock_off()

    def ejector_right(self, lock_off=True):
        """
        Fährt den Auswerfer nach rechts aus.
        :param lock_off Boolean ob die Sperre ausgeschaltet werden soll (nur wichtig um in die Mittelposition zu gehen)
        """
        
        with self.sem:
            reg0 = self.get_output_register(offset=0)
            reg1 = self.get_output_register(offset=1)
            reg0[0] = set_bit(reg0[0], 0)
            reg1[0] = set_bit(reg1[0], 15)

            reg3 = [reg0[0], reg1[0]]

            self.set_output_register(reg3, offset=0)
            #self.set_output_register(reg0)
            #self.set_output_register(reg1, offset=1)
            sleep(0.05)
            reg0[0] = reset_bit(reg0[0], 0)
            self.set_output_register(reg0)#, offset=1)
        if lock_off:
            self.ejector_lock_off()
        
    def ejector_middle(self):
        """
        Fährt den Auswerfer in Mittelstellung.
        """
        
        while not self.check_ejector_middle(): #Nötig da Auswerfer zwischendurch die Sperre ignorieren
            self.ejector_lock_on()
            if self.check_ejector_left():
                self.ejector_right(False)
            elif self.check_ejector_right():
                self.ejector_left(False)
            sleep(0.5)
        

    def check_conveyor_side_piece_at_end(self):
        """
        Überprüft, ob der Sensor am Bandende des Massenmagazins ein Werkstück erkennt.
        :returns boolean ob der Sensor am Bandende des Massenmagazins ein Werkstück erkennt
        :rtype bool
        """ 
        return test_bit(self.get_input_register(offset=1)[0], 0)

    def check_conveyor_main_piece_begin(self):
        """
        Überprüft, ob der Sensor am Bandanfang des Magazinbandes ein Werkstück erkennt.
        :returns boolean ob der Sensor am Bandanfang des Magazinbandes ein Werkstück erkennt
        :rtype bool
        """ 
        return test_bit(self.get_input_register(offset=1)[0], 2)

    def check_conveyor_main_piece_between_Mag1_and_2(self):
        """
        Überprüft, ob der Sensor zwischen Magazin 1 und 2 des Magazinbandes ein Werkstück erkennt.
        :returns boolean ob der Sensor zwischen Magazin 1 und 2 des Magazinbandes ein Werkstück erkennt
        :rtype bool
        """ 
        return test_bit(self.get_input_register(offset=1)[0], 3)

    def check_conveyor_main_piece_between_Mag2_and_3(self):
        """
        Überprüft, ob der Sensor zwischen Magazin 2 und 3 des Magazinbandes ein Werkstück erkennt.
        :returns boolean ob der Sensor zwischen Magazin 2 und 3 des Magazinbandes ein Werkstück erkennt
        :rtype bool
        """ 
        return test_bit(self.get_input_register(offset=1)[0], 4)

    def check_conveyor_main_piece_in_front_of_ejector(self):
        """
        Überprüft, ob der Sensor vor der Weiche des Magazinbandes ein Werkstück erkennt.
        :returns boolean ob der Sensor vor der Weiche des Magazinbandes ein Werkstück erkennt
        :rtype bool
        """ 
        return test_bit(self.get_input_register(offset=1)[0], 5)

    def check_seperator_main_set(self):
        """
        Überprüft, ob der Vereinzeler am Ausgang gesetzt ist.
        :returns boolean ob der Vereinzeler am Ausgang gesetzt ist
        :rtype bool
        """
        return test_bit(self.get_input_register(offset=1)[0], 6)

    def check_seperator_main_piece(self):
        """
        Überprüft, ob am Vereinzeler am Ausgang ein Werkstück ist.
        :returns boolean ob am Vereinzeler am Ausgang ein Werkstück ist
        :rtype bool
        """
        return test_bit(self.get_input_register(offset=1)[0], 7)

    def check_seperator_side_set(self):
        """
        Überprüft, ob der Vereinzeler am Massenmagazin gesetzt ist.
        :returns boolean ob der Vereinzeler am Massenmagazin gesetzt ist
        :rtype bool
        """
        return test_bit(self.get_input_register(offset=1)[0], 8)

    def check_seperator_side_piece(self):
        """
        Überprüft, ob am Vereinzeler am Massenmagazin ein Werkstück ist.
        :returns boolean ob am Vereinzeler am Massenmagazin ein Werkstück ist
        :rtype bool
        """
        return test_bit(self.get_input_register(offset=1)[0], 9)

    def check_magazine_retracted(self, magazine_id):
        """
        Überprüft, ob das ausgewählte Magazin eingefahren ist.
        :param magazine_id Nummer des zu überprüfenden Magazins (Magazin 1 = 1,...)
        :returns boolean ob das ausgewählte Magazin eingefahren ist
        :rtype bool
        """
        offset = 1
        bit_nr = 10
        if magazine_id == 2:
            offset = 1
            bit_nr = 13
        if magazine_id == 3:
            offset = 0
            bit_nr = 0

        return test_bit(self.get_input_register(offset)[0], bit_nr)

    def check_magazine_ejected(self, magazine_id):
        """
        Überprüft, ob das ausgewählte Magazin ausgefahren ist.
        :param magazine_id Nummer des zu überprüfenden Magazins (Magazin 1 = 1,...)
        :returns boolean ob das ausgewählte Magazin ausgefahren ist
        :rtype bool
        """
        offset = 1
        bit_nr = 11
        if magazine_id == 2:
            offset = 1
            bit_nr = 14
        if magazine_id == 3:
            offset = 0
            bit_nr = 1

        return test_bit(self.get_input_register(offset)[0], bit_nr)

    def check_magazine_empty(self, magazine_id):
        """
        Überprüft, ob das ausgewählte Magazin leer ist. Erkennt nicht ob das Magazin leer ist,
        während das ausgewählte Magazin ausgefahren ist.
        :param magazine_id Nummer des zu überprüfenden Magazins (Magazin 1 = 1,...)
        :returns boolean ob das ausgewählte Magazin leer ist
        :rtype bool
        """
        offset = 1
        bit_nr = 12
        if magazine_id == 2:
            offset = 1
            bit_nr = 15
        if magazine_id == 3:
            offset = 0
            bit_nr = 2

        return not test_bit(self.get_input_register(offset)[0], bit_nr)

    def check_ejector_left(self):
        """
        Überprüft, ob sich der  Auswerfer in Linksposition befindet.
        :returns boolean ob sich der  Auswerfer in Linksposition befindet
        :rtype bool
        """
        return test_bit(self.get_input_register(offset= 0)[0], 4)

    def check_ejector_right(self):
        """
        Überprüft, ob sich der  Auswerfer in Rrechtsposition befindet.
        :returns boolean ob sich der Auswerfer in Rechtsposition befindet
        :rtype bool
        """
        return test_bit(self.get_input_register(offset=0)[0], 3)

    def check_ejector_middle(self):
        """
        Überprüft, ob sich der Auswerfer in Mittelposition befindet.
        :returns boolean ob sich der Auswerfer in Mittelposition befindet
        :rtype bool
        """
        return test_bit(self.get_input_register(offset=0)[0], 5)

    def check_ejector_lock_set(self):
        """
        Überprüft, ob die Sperre für den Auswerfer gesetzt ist.
        :returns boolean ob die Sperre für den  Auswerfer gesetzt ist
        :rtype bool
        """
        return test_bit(self.get_input_register(offset=0)[0], 6)

    def check_slide_full(self):
        """
        Überprüft, ob die Rutsche voll ist.
        :returns boolean ob die Rutsche voll ist
        :rtype bool
        """
        return test_bit(self.get_input_register(offset=0)[0], 7)

    def check_height_sensor_measurement_ok(self):
        """
        Überprüft, ob die vom Höhensensor gemessene Höhe des Werkstücks in Ordnung ist.
        :returns boolean ob die vom Höhensensor gemessene Höhe des Werkstücks in Ordnung ist
        :rtype bool
        """

        return test_bit(self.get_input_register(offset=0)[0], 9)

    def check_height_sensor_piece(self):
        """
        Überprüft, ob der Höhensensor ein Werkstück erkannt hat.
        :returns boolean ob der Höhensensor ein Werktstück erkannt hat
        :rtype bool
        """

        return test_bit(self.get_input_register(offset=0)[0], 8)

    def check_height_sensor_piece_ok(self):
        """
        Überprüft, ob das Werkstück, welches der Höhensensor als nächstes erkennt,
        in Normalposition (Öffnung nach Oben) vorliegt.
        :returns boolean ob das Werkstück in Normalposition vorliegt
        :rtype bool
        """
        while not self.check_height_sensor_piece():
            sleep(0.02)
        #Führt 5 Tests durch ob ein Werkstück erkannt wird 
        test1 = self.check_height_sensor_piece()
        sleep(0.03)
        test2 = self.check_height_sensor_piece()
        sleep(0.03)
        test3 = self.check_height_sensor_piece()
        sleep(0.03)
        test4 = self.check_height_sensor_piece()
        sleep(0.03)
        test5 = self.check_height_sensor_piece()


        #Da bei richtig gedrehten Werkstücken nur die erhöten Flächen erkannt werden, kann davon ausgegangen werden,
        #dass bei mehr als 3 positiven Messungen es sich um ein falsch gedrehtes Werkstück handelt. Diese können nämlich an
        #fast allen Stellen von self.check_height_sensor_piece() erkannte werden (außer an den 3 Löchern, weshalb das Kriterium
        #für ein falsch gedrehtes Werkstück auch 4-5 positive Messungen und nicht nur 5 positive Messungen ist)
        if(test1+test2+test3+test4+test5 < 4):
            return True
        else:
            return False
                
    def check_conveyor_side_piece_end(self):
        """
        Überprüft, ob am Eingang des Zubringer bands ein Werkstück erkannt wird.
        :returns boolean ob am Zubringer ein Werkstück erkannt wird
        :rtype bool
        """
        return test_bit(self.get_input_register(offset=1)[0], 1)

    def check_magazine_4_empty(self):
        """
        Überprüft, ob das Massenmagazin Leer ist (Ob der Sensor am Massenmagazin kein Werkstück erkennt).
        :returns boolean ob das Massenmagazin Leer ist.
        :rtype bool
        """
        return not test_bit(self.get_input_register(offset=1)[0], 9)

    def conveyor_output_forward(self):
        """
        Lässt das Zubringer Laufband vorwärts fahren. speed muss seperat gesetzt werden.
        """
        with self.sem:
            reg = self.get_output_register(offset=1)
            reg[0] = reset_bit(reg[0], 5)
            reg[0] = set_bit(reg[0], 6)
            self.set_output_register(reg,offset=1)        

    def conveyor_output_backward(self):
        """
        Lässt das Zubringer Laufband rückwärts fahren. speed muss seperat gesetzt werden.
        """
        with self.sem:
                reg = self.get_output_register(offset=1)
                reg[0] = reset_bit(reg[0], 6)
                reg[0] = set_bit(reg[0], 5)
                self.set_output_register(reg,offset=1)        

    def conveyor_output_stop(self):
        """
        Lässt das Zubringer Laufband stoppen.
        """
        with self.sem:
            reg = self.get_output_register(offset=1)
            reg[0] = reset_bit(reg[0], 5)
            reg[0] = reset_bit(reg[0], 6)
            self.set_output_register(reg,offset=1)        

    def conveyor_output_set_speed(self, speed):
        """
        Setzt die speed des Zubringer Laufbands.
        :param speed speed des Laufbands als Integer zwischen 0 (0%/0V) und 30000 (100%/10V)
        """
        with self.sem:
            #Automatisches öffnen und schließen von TCP verbindungen aufheben, da hier viele TCP Pakete nacheinander gesendet werden
            #und es somit besser ist einmal die Verbindung zu öffnen und danach wieder zu schließen.
            self.client.auto_close = False
            self.client.auto_open = False

            #Öffnen der TCP Verbindung
            self.client.open()

            self.client.write_single_register(8015, int("0x6000",16))
            self.client.write_single_register(8015, int("0x3000",16))

            self.client.write_single_register(8016, speed)
            self.client.write_single_register(8017, 0)
            self.client.write_single_register(8018, 0)
            self.client.write_single_register(8019, 0)

            self.client.write_single_register(8015, int("0x0100",16))
            self.client.write_single_register(8015, int("0x0b00",16))

            self.client.write_single_register(8016, 0)
            self.client.write_single_register(8017, 0)
            self.client.write_single_register(8018, 0)
            self.client.write_single_register(8019, 0)

            self.client.write_single_register(8015, int("0x0900",16))

            #Schließen der TCP Verbindung
            self.client.close()

            self.client.auto_close = True
            self.client.auto_open = True

    def check_conveyor_output_piece_end(self):
        return test_bit(self.get_input_register(offset=1)[0], 1)
    
    
    #================================== MQTT ==================================
    def work_output_piece_end(self):
        while True:
            publish.single("input2/output_piece_ready", self.check_conveyor_output_piece_end(), hostname="192.168.200.161")
            sleep(1)
    #================================== MQTT ==================================
    

    def work_area_blocker(self, sem_b1, sem_b2, sem_b3):
        """
        Helferfunktion von work(). Ruft für alle Bereiche work_block_area() auf, wenn ein Werkstück von DZA kommt.
        :param sem_b1 Semaphore für Bereich 1
        :param sem_b2 Semaphore für Bereich 2
        :param sem_b3 Semaphore für Bereich 3
        """
        b1_neu = False

        while True:
            b1_alt = b1_neu

            b1_neu = self.check_conveyor_main_piece_begin()

            if not b1_alt and b1_neu:
                threading.Thread(target=self.work_block_area, args=(1, sem_b1)).start()
                threading.Thread(target=self.work_block_area, args=(2, sem_b2)).start()
                threading.Thread(target=self.work_block_area, args=(3, sem_b3)).start()
            sleep(0.2)

    def work_block_area(self, area_id, sem):
        """
        Helferfunktion für work(). Blockiert einen die Semaphore eines Bereiches bis das Werkstück den Bereich verlässt.
        :param area_id Nummer des zu blockierenden Bereichs
        :param sem zu blockierende Semaphore des Bereiches
        """
        with sem:
            sleep(0.5)
            if area_id == 1:
                while not self.check_conveyor_main_piece_between_Mag1_and_2():
                    sleep(0.1)
            if area_id == 2:
                while not self.check_conveyor_main_piece_between_Mag2_and_3():
                    sleep(0.1)
            if area_id == 3:
                while not self.check_conveyor_main_piece_in_front_of_ejector():
                    sleep(0.1)

    def work_auto_seperator(self):
        """
        Helferfunktion für work(). Betätigt den Vereinzeler sobald ein Werkstück von dem Sensor am Vereinzeler erkannt wird.
        """
        while True:
            self.seperator_main_reset()
            while not self.check_seperator_main_piece():
                sleep(0.5)
            self.seperator_main_set()
            sleep(0.2)

    def work_quality_check_ejector_on(self):
        """
        Helferfunktion für work_quality_check(). Bringt den Auswerfer nach 0.1 Sekunde in die Rechtsposition um Werkstücke auszuwerfen.
        """
        sleep(0.1)
        self.ejector_right()

    def work_quality_check_ejector_off(self):
        """
        Helferfunktion für work_quality_check(). Bringt den Auswerfer nach 0.1 Sekunde in die Mittelposition um Werkstücke durchzulassen.
        """
        self.ejector_middle()

    def work_quality_check(self, queueToTS : multiprocessing.Queue = None):

        """
        Helferfunktion für work(). Überprüft, ob ein Werkstück welches durch den Höhensensor läuft richtig rum gedreht ist. Wird eine queueToTS übergeben, wird über diese
        dem Transportsystem mitgeteilt wohin das Werkstück transportiert werden soll.

        :param queueToTS Queue zum Transportsystem über die mitgeteilt wird das (und wohin) das Werkstück transportiert werden soll
        """

        #================================== MQTT ==================================
        n_bad_pieces = 0
        publish.single("input2/n_defective_pieces", n_bad_pieces, hostname="192.168.200.161")
        n_good_pieces = 0
        publish.single("input2/n_working_pieces", n_good_pieces, hostname="192.168.200.161")

        #n_bad_pieces_to_DCO = 0
        #publish.single("input2/n_defective_pieces_to_DCO", n_bad_pieces_to_DCO, hostname="192.168.200.161")
        #================================== MQTT ==================================

        while True:
            sleep(0.02)
            #Wartet bis ein Werkstück erkannt wird
            if self.check_height_sensor_piece():
                #Führt 5 Tests durch ob ein Werkstück erkannt wird 
                test1 = self.check_height_sensor_piece()
                sleep(0.03)
                test2 = self.check_height_sensor_piece()
                sleep(0.03)
                test3 = self.check_height_sensor_piece()
                sleep(0.03)
                test4 = self.check_height_sensor_piece()
                sleep(0.03)
                test5 = self.check_height_sensor_piece()
                
                #Da bei richtig gedrehten Werkstücken nur die erhöten Flächen erkannt werden, kann davon ausgegangen werden,
                #dass bei mehr als 3 positiven Messungen es sich um ein falsch gedrehtes Werkstück handelt. Diese können nämlich an
                #fast allen Stellen von self.check_height_sensor_piece() erkannte werden (außer an den 3 Löchern, weshalb das Kriterium
                #für ein falsch gedrehtes Werkstück auch 4-5 positive Messungen und nicht nur 5 positive Messungen ist)
                if (test1 + test2 + test3 + test4 + test5) < 4:
                    #Ist der Auswerfer nicht in Mittelposition muss dieser in ca 0.1 (wenn Laufband nicht gedrosselt) Sekunde in die Mittelposition gebracht werden,
                    #damit das Werkstück nicht ausgeworfen wird. Diese Aufgabe wird an einen Thread ausgelagert, damit der aktuelle Thread
                    #in der Zeit weitere eintreffende Werkstücke untersuchen kann
                    if not self.check_ejector_middle():
                        threading.Thread(target=self.work_quality_check_ejector_off).start()

                    #================================== MQTT ==================================
                    n_good_pieces+=1
                    publish.single("input2/n_working_pieces", n_good_pieces, hostname="192.168.200.161")
                    #================================== MQTT ==================================

                    #Mitteilung an Transportsystem
                    if queueToTS != None:
                        queueToTS.put_nowait(['DZE', 'B'])
                else:
                    #Ist die Rutsche nicht voll wird das falsch gedrehte Werkstück ausgeworfen
                    
                    #================================== MQTT ==================================
                    n_bad_pieces+=1
                    publish.single("input2/n_defective_pieces", n_bad_pieces, hostname="192.168.200.161")
                    #================================== MQTT ==================================

                    if not self.check_slide_full():
                        if not self.check_ejector_right():
                            threading.Thread(target=self.work_quality_check_ejector_on).start()

                    else:
                        #Ist die Rutsche voll wird das falsch gedrehte Werkstück durchgelassen aber zur DZA transportiert
                        if not self.check_ejector_middle():
                            threading.Thread(target=self.work_quality_check_ejector_off).start()
                        
                        if queueToTS != None:
                            queueToTS.put_nowait(['DZE', 'DZA'])
                        
                        #================================== MQTT ==================================
                        #n_bad_pieces_to_DCO += 1
                        #publish.single("input2/n_defective_pieces_to_DCO", n_bad_pieces_to_DCO, hostname="192.168.200.161")
                        #================================== MQTT ==================================
                        
                sleep(0.15)


    def work(self, int, start = False,  wait_between_new_pieces = 20, queueToTS = None):
        
        """
        Lässt DZE kontinuierlich Werkstücke auswerfen und diese auf ihre richitge orientierung prüfen. Werkstücke die nicht richtig rum gedreht sind
        werden auf die Rutsche ausgeworfen, solange diese nicht voll ist. Wurde eine queueToTS übergeben wird dem Transportsystem für jedes Werkstück ein Transport
        mitgeteilt. Richtig gedrehte werden zu einer Bearbeitenstation und jedes falsch gedrehte Werkstück, welches nicht mehr auf die Rutsche passt,
        zur DZA transportiert.

        :param wait_between_new_pieces Zeit in Sekunden, die mindestens vergehen muss zwischen 2 Werkstücken die von den Magazinen ausgeworfen werden
        :param queueToTS Queue zum Transportsystem über die mitgeteilt wird das (und wohin) das Werkstück transportiert werden soll
        """
        #Semaphoren um die Bereiche zu blockieren
        sem_b1 = threading.BoundedSemaphore(value=1)
        sem_b2 = threading.BoundedSemaphore(value=1)
        sem_b3 = threading.BoundedSemaphore(value=1)
        sems = [sem_b1, sem_b2, sem_b3]

        #Funktionen für die verschiedenen Sensoren um festzustellen ob die Werkstücke die Bereiche verlassen haben
        exit_funcs = [self.check_conveyor_main_piece_between_Mag1_and_2,self.check_conveyor_main_piece_between_Mag2_and_3,self.check_conveyor_main_piece_in_front_of_ejector]
            
            

        if start:
            #DZE in Ausgangszustand bringen
            self.magazine_retract(1)
            self.magazine_retract(2)
            self.magazine_retract(3)
            self.conveyor_output_forward()
            self.conveyor_output_set_speed(30000)
            self.conveyor_main_right()
            self.conveyor_side_on()

            #Threads für den Vereinzeler, Bereiche blockieren und überprüfung der Werkstücke starten
            
            threading.Thread(target=self.work_auto_seperator).start()

            threading.Thread(target=self.work_quality_check, args=[queueToTS]).start()
            threading.Thread(target=self.work_area_blocker, args=(sem_b1, sem_b2, sem_b3)).start()
            
        #Zufälliges Magazin wird ausgewählt um Werkstück auszuwerfen
        rand = int
        sleep(0.1)

        #0-1 => Magazin 1-3
        if rand in [0,1,2]:
            
            if not self.check_magazine_empty(rand+1):
            #Wenn der Bereich vor dem Magazin blockiert ist wartet der Thread nicht, da es ansonsten zu kollisionen kommen kann
            #(Bsp.:Werkstück blockiert bereich -> Magazin wartet -> Weiteres werkstück betritt den bereich solange Magazin wartet)
            #Stattdessen wird übersprungen und ein neues zufälliges Magazin ausgewählt
                if sems[rand].acquire(blocking=True):
                    threading.Thread(target=self.work_block_area, args=(3, sem_b3)).start()
                    if rand < 2:
                        threading.Thread(target=self.work_block_area, args=(2, sem_b2)).start()
                    if rand < 1:
                        threading.Thread(target=self.work_block_area, args=(1, sem_b1)).start()
                    sems[rand].release()

                    #Fährt das Magazin aus und wieder ein
                    self.magazine_eject(rand+1)
                    while not self.check_magazine_ejected(rand+1):
                        sleep(0.05)
                    
                    self.magazine_retract(rand +1)


                    old = True
                    new = exit_funcs[rand]
                    while not old and new:
                        old = new
                        new = exit_funcs[rand]
                        sleep(0.1)
                    #sems[rand].release()
                sleep(wait_between_new_pieces)

        #3 => Massenmagazin
        if rand == 3:
            if not self.check_magazine_4_empty():
                self.seperator_side_set()
                while not self.check_seperator_side_set():
                    sleep(0.2)
                sleep(0.2)
                self.seperator_side_reset()

                while not self.check_conveyor_side_piece_at_end():
                    sleep(0.05)

                self.conveyor_side_off()

                if sem_b3.acquire():
                    threading.Thread(target=self.work_block_area, args=(3, sem_b3)).start()
                    sem_b3.release()
                    self.conveyor_side_on()
                sleep(wait_between_new_pieces)
