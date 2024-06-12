from time import sleep, ticks_us, sleep_us
from machine import Pin, Timer, PWM
from picodfplayer import DFPlayer
import ujson
import network
import urequests
import utime

global IS_PLAYING
IS_PLAYING = True
global current_track
current_track = 1

trig = Pin(16, Pin.OUT)
echo = Pin(17, Pin.IN, Pin.PULL_DOWN)
button = Pin(22, mode=Pin.IN, pull=Pin.PULL_UP)
player = DFPlayer(0, 12, 13, 15)
led = Pin(21, mode=Pin.OUT)

def get_current_track():
    return str(player.sendcmd(0x4B, 0x00, 0x00))

def play_specific_track(track_number):
    str(player.sendcmd(0x03, 1, track_number))

try:
    if player.queryBusy() == False:
        play_specific_track(1)
    else:
        player.reset()
        play_specific_track(1)
except Exception as e:
    print(e)

ssid = 'iPhone de Romain'
password = 'soleil123!'

def play_next_track(pin):
    player.nextTrack()


button.irq(trigger=Pin.IRQ_FALLING, handler=play_next_track)

def get_volume_from_distance(distance):
    if distance < 0 or distance > 1300:
        return 20
    if distance > 400:
        distance = 400
    volume = (distance / 400) * 20
    return round(volume)

def connect_wifi(ssid, password, max_attempts=5, timeout=30):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    for attempt in range(max_attempts):
        print(f"Tentative de connexion {attempt+1}/{max_attempts}")
        wlan.connect(ssid, password)
        
        start_time = utime.time()
        while not wlan.isconnected():
            print("Connexion en cours...")
            utime.sleep(1)
            if utime.time() - start_time > timeout:
                print(f"Échec de la tentative de connexion {attempt+1}/{max_attempts} après {timeout} secondes")
                print("Current Status:", wlan.status())
                break
        if wlan.isconnected():
            return wlan
        utime.sleep(5)
    
    print("Impossible de se connecter au Wi-Fi après plusieurs tentatives.")
    return False

def get_current_time():
    try:
        url = "http://worldtimeapi.org/api/timezone/Europe/Paris"
        response = urequests.get(url)
        data = response.json()
        current_time = data['datetime']
        response.close()
        return current_time
    except Exception as e:
        print("Erreur lors de la récupération de l'heure actuelle:", e)
        return None

def play_music_based_on_time():
    current_time = get_current_time()
    global current_track
    
    if current_time:
        hour = int(current_time[11:13])
        if 6 <= hour < 12 and current_track != 1:
            player.playTrack(1, 1)
            current_track = 1
        elif 12 <= hour < 18 and current_track != 2:
            player.playTrack(2, 1)
            current_track = 2
        elif 18 <= hour < 24 and current_track != 3:
            player.playTrack(3, 1)
            current_track = 3
        elif 24 <= hour < 6 and current_track != 4:
            player.playTrack(4, 1)
            current_track = 4
    else:
        print("Impossible de récupérer l'heure actuelle")

# Connexion au Wi-Fi
print("Connexion au Wi-Fi")
wlan = connect_wifi(ssid, password)
if not wlan or not wlan.isconnected():
    print("Impossible de se connecter au Wi-Fi. Arrêt du script.")
    raise SystemExit

print("Connexion Wi-Fi réussie !")

while True:
    try:
        trig.value(0)
        utime.sleep(0.1)
        trig.value(1)
        utime.sleep_us(10)
        trig.value(0)
        
        while echo.value() == 0:
            pulse_start = utime.ticks_us()
        while echo.value() == 1:
            pulse_end = utime.ticks_us()
        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17165 / 1000000
        distance = round(distance, 0)
        
        volume = get_volume_from_distance(distance)
        player.setVolume(volume)
        
        if IS_PLAYING:
            led.on()
            print("Lecture de la musique")
            play_music_based_on_time()
            player.resume()
        else:
            led.off()
            print("Pause de la musique")
            player.pause()

        print(f'Distance: {distance} cm')
        utime.sleep(0.5)
    except Exception as e:
        print(e)
