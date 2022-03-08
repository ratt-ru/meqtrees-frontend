import sys                                                                  
from qtpy.QtWidgets import QApplication, QPushButton                     
from qtpy.QtCore import QObject, Signal                      
app = QApplication(sys.argv)                                                

def say_something(stuff):                                                   
    print(stuff)                                                            

class Communicate(QObject):                                                 
    # create two new signals on the fly: one will handle                    
    # int type, the other will handle strings                               
    speak_number = Signal(int)                                              
    speak_word = Signal(str)                                                  

#result_index = Signal('PyQt_PyObject')                                                                            

someone = Communicate()                                                     
# connect signal and slot properly                                          
someone.speak_number.connect(say_something)                                 
someone.speak_word.connect(say_something)                                   
# emit each 'speak' signal                                                  
someone.speak_number.emit(10)                                               
someone.speak_word.emit("Hello everybody!")
