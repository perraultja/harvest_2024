# myapp.py

import kivy
from kivy.app import App
from kivy.uix.button import Button

class MyFirstKivyApp(App):
    def build(self):
        return Button(text="Hello, Kivy!")

if __name__ == "__main__":
    MyFirstKivyApp().run()
#%%
