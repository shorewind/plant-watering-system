import RPi.GPIO as GPIO
import time
import board # I2C communication
import adafruit_ahtx0 # Temperature and humidity sensor
from adafruit_seesaw.seesaw import Seesaw # Moisture sensor

# GPIO to LCD mapping
LCD_RS = 7   # Pi pin 26
LCD_E  = 8   # Pi pin 24
LCD_D4 = 25  # Pi pin 22
LCD_D5 = 24  # Pi pin 18
LCD_D6 = 23  # Pi pin 16
LCD_D7 = 18  # Pi pin 12

# Device constants
LCD_CHR = True    # Character mode
LCD_CMD = False   # Command mode
LCD_CHARS = 16    # Characters per line (16 max)
LCD_LINE_1 = 0x80 # LCD memory location for 1st line
LCD_LINE_2 = 0xC0 # LCD memory location 2nd line

# Define main program code
def main():  
    # Hardware setup
    GPIO.setmode(GPIO.BCM) # Use BCM BPIO numbers
    GPIO.setwarnings(False)
    GPIO.setup(1, GPIO.OUT) # LED
    GPIO.setup(13, GPIO.OUT) # Motor driver
    GPIO.setup(LCD_E, GPIO.OUT) # LCD
    GPIO.setup(LCD_RS, GPIO.OUT)
    GPIO.setup(LCD_D4, GPIO.OUT)
    GPIO.setup(LCD_D5, GPIO.OUT)
    GPIO.setup(LCD_D6, GPIO.OUT)
    GPIO.setup(LCD_D7, GPIO.OUT)

    # Initialize display
    lcd_init()
    lcd_text("Plant Monitor", LCD_LINE_1)

    # Initalize states
    GPIO.output(1, GPIO.LOW) # LED off
    pwm = GPIO.PWM(13, 100)  # Forwards PWM

    # Sensor instances
    i2c = board.I2C()
    aht_sensor = adafruit_ahtx0.AHTx0(i2c) # Temperature and humidity
    moisture_sensor = Seesaw(i2c, addr=0x36) # Moisture
    
    # Query user for input
    threshold = float(input("Enter desired threshold moisture percentage: "))
    min_interval = float(input("Enter desired minimum interval between watering (in seconds): "))
    duration = float(input("Enter desired water duration (in seconds): "))

    print("\nmoisture (%), temperature (*C), humidity (%)") # Header
    
    # File initialization
    file = open("plant_data.txt", "w")
    file.close()
    
    last_read = 0.0
    last_water = 0.0 # Initialize last read times
    while True:
        if (time.time() - last_read) > 1.0:
            # Sensor readings
            moisture = moisture_sensor.moisture_read()
            temperature = round(aht_sensor.temperature, 2)
            humidity = round(aht_sensor.relative_humidity, 2) # Sensor readings
            
            # Calculate approximate percent moisture
            min_moisture = 320
            max_moisture = 1000  # Approximate min and max based on testing
            moisture_level = moisture - min_moisture
            moisture_perc = round(moisture_level/(max_moisture - min_moisture)*100, 2)
            
            file = open("plant_data.txt", "a") # Append to file
            file.write(f'{moisture_perc}, {temperature}, {humidity}\n')
            file.close()
            
            print(f'{moisture_perc}, {temperature}, {humidity}') # Print results
            
            if moisture_perc < threshold:
                GPIO.output(1, GPIO.HIGH) # LED on
                lcd_text("Status: Dry", LCD_LINE_2)
                if (time.time() - last_water) > min_interval:  # Arbitrarily chose min water interval as 5 minutes
                    print("water")
                    # Pump control
                    pwm.start(0)
                    pwm.ChangeDutyCycle(100) # Motor full speed
                    time.sleep(duration)
                    pwm.stop()
                    last_water = time.time()
            else:
                GPIO.output(1, GPIO.LOW) # LED off
                lcd_text("Status: Good", LCD_LINE_2)

            last_read = time.time()
# End of main program code


# Function declarations       
# Initialize and clear display
def lcd_init():
    lcd_write(0x33,LCD_CMD) # Initialize
    lcd_write(0x32,LCD_CMD) # Set to 4-bit mode
    lcd_write(0x06,LCD_CMD) # Cursor move direction
    lcd_write(0x0C,LCD_CMD) # Turn cursor off
    lcd_write(0x28,LCD_CMD) # 2 line display
    lcd_write(0x01,LCD_CMD) # Clear display
    time.sleep(0.0005)      # Delay to allow commands to process

def lcd_write(bits, mode):
    # High bits
    GPIO.output(LCD_RS, mode) # RS
    GPIO.output(LCD_D4, False)
    GPIO.output(LCD_D5, False)
    GPIO.output(LCD_D6, False)
    GPIO.output(LCD_D7, False)
    if bits&0x10==0x10:
        GPIO.output(LCD_D4, True)
    if bits&0x20==0x20:
        GPIO.output(LCD_D5, True)
    if bits&0x40==0x40:
        GPIO.output(LCD_D6, True)
    if bits&0x80==0x80:
        GPIO.output(LCD_D7, True)

    # Toggle 'Enable' pin
    lcd_toggle_enable()

    # Low bits
    GPIO.output(LCD_D4, False)
    GPIO.output(LCD_D5, False)
    GPIO.output(LCD_D6, False)
    GPIO.output(LCD_D7, False)
    if bits&0x01==0x01:
        GPIO.output(LCD_D4, True)
    if bits&0x02==0x02:
        GPIO.output(LCD_D5, True)
    if bits&0x04==0x04:
        GPIO.output(LCD_D6, True)
    if bits&0x08==0x08:
        GPIO.output(LCD_D7, True)

    # Toggle 'Enable' pin
    lcd_toggle_enable()

def lcd_toggle_enable():
    time.sleep(0.0005)
    GPIO.output(LCD_E, True)
    time.sleep(0.0005)
    GPIO.output(LCD_E, False)
    time.sleep(0.0005)

def lcd_text(message,line):
    # Send text to display
    message = message.ljust(LCD_CHARS," ")

    lcd_write(line, LCD_CMD)

    for i in range(LCD_CHARS):
        lcd_write(ord(message[i]),LCD_CHR)

# Begin program
try:
    main()
except KeyboardInterrupt:
    pass
finally:
    lcd_write(0x01,LCD_CMD) # Clear display
    lcd_text("Automated Plant", LCD_LINE_1)
    lcd_text("Watering System", LCD_LINE_2)
    GPIO.cleanup()
