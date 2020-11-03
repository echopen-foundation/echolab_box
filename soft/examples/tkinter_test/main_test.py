import tkinter as tk
# import matplotlib as mpl

# Create the main window
root = tk.Tk()
root.title("My GUI")

# Create label
label = tk.Label(root, text="Hello, World!")

# Lay out label
label.pack()

def callback():
    print ("click!")

b = tk.Button(root, text="OK", command=callback)
b.pack()

# Run forever!
root.mainloop()