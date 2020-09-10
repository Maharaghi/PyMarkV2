import os
import json
import pathlib
import numpy as np

from tkinter import *
from tkinter import ttk
from enum import Enum, unique
from PIL import Image, ImageTk, ImageDraw

SETTINGS = "./settings.json"

class ErrWindow():
    def __init__(self, errormessage):
        root = Tk()
        root.title("ERROR")

        fr = ttk.Frame(root, padding="20 20 20 20")
        fr.grid(column=0, row=0, sticky=(N, W, E, S))

        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        
        msg = StringVar()
        msg.set(errormessage)

        Label(fr, textvariable=msg).grid(column=1, row=1, sticky=(W, E))
        Button(fr, text="Quit", command=(lambda : exit(0))).grid(column=1, row=2, sticky=(W, E))

        root.bind("<Return>", (lambda _: exit(0)))

        root.mainloop()

class Annotator:
    # Initialize the annotator
    def __init__(self):
        try:
            with open(SETTINGS, "r") as f:
                self.settings = json.load(f)
        except:
            ErrWindow("Could not find or open settings.json")
            return
        
        if not self.settings.get("classlist"):
            ErrWindow("'classlist' not defined in settings.json!")
            return
        
        if not self.settings.get("loaddir"):
            ErrWindow("'loaddir' not defined in settings.json!")
            return
        
        if not self.settings.get("savedir"):
            ErrWindow("'savedir' not defined in settings.json!")
            return

        if len(self.settings["classlist"]) <= 0:
            ErrWindow("No classes found in classlist!")
            return
        
        self.Annotations = Enum("Annotations", " ".join(self.settings["classlist"]))

        self.pilImage = None
        self.canvasImage = None
        self.fileIndex = self.settings["index"] if self.settings.get("index") is not None else 0
        self.files = []

        self.canvas = None

        self.currentlyOpen = None
        self.imgList = None

        self.canvasScale = 1

        self.categoryMode = self.Annotations(1)

        self.polygonID = 0
        self.isDrawingPolygon = False

        self.imSize = {}
        self.imageData = {}
        self.canvasData = {}
        self.main()

    # Add a new point to the currently active polygon
    def addPoint(self, event):
        if self.curImgData is None or self.curCanvData is None:
            print("No current image/canvas data. Returning")
            return

        self.isDrawingPolygon = True

        width, height = self.pilImage.size

        scalex = width / 630.0
        scaley = height / 900.0

        x1 = round(event.x * scalex)
        y1 = round(event.y * scaley)

        if x1 < 0:
            x1 = 0
        elif x1 >= width:
            x1 = width - 1
        
        if y1 < 0:
            y1 = 0
        elif y1 >= height:
            y1 = height - 1
        

        self.curImgData[self.polygonID]["category"] = self.categoryMode.name
        self.curCanvData[self.polygonID]["category"] = self.categoryMode.name

        self.curImgData[self.polygonID]["all_x"].append(x1)
        self.curImgData[self.polygonID]["all_y"].append(y1)

        self.curCanvData[self.polygonID]["all_x"].append(event.x)
        self.curCanvData[self.polygonID]["all_y"].append(event.y)

        self.draw()

    # Draw the canvas and all the polygons
    def draw(self):
        self.canvas.delete("all")
        self.canvas.create_image(630/2, 900/2, image=self.canvasImage)


        for index, data in enumerate(self.curCanvData):
            coords = []
            if len(data["all_x"]) == 0:
                continue

            if index == self.polygonID:
                colour = "#"

                if (self.categoryMode.value + 1) % 3 == 0:
                    colour += "ff"
                else:
                    colour += "00"
                
                if (self.categoryMode.value + 1) % 2 == 0:
                    colour += "ff"
                else:
                    colour += "00"
                
                if (self.categoryMode.value + 1) % 4 == 0:
                    colour += "ff"
                else:
                    colour += "00"
            else:
                colour = "#0000ff"

            for i, x in enumerate(data["all_x"]):
                y = data["all_y"][i]
                coords.append((x, y))
                if index == self.polygonID:
                    self.canvas.create_oval(x - 2, y - 2, x + 2, y + 2, fill=colour, outline=colour)
            self.canvas.create_polygon(coords, outline=colour, fill="")

        return

    # Remove last point in polygon. Do nothing if there are no points.
    def undoPolygon(self, event=None):
        if self.curImgData is None or self.curCanvData is None:
            print("No current image/canvas data. Returning")
            return

        if (len(self.curCanvData[self.polygonID]["all_x"]) == 0):
            return

        self.curImgData[self.polygonID]["all_x"].pop(len(self.curImgData[self.polygonID]["all_x"]) - 1)
        self.curImgData[self.polygonID]["all_y"].pop(len(self.curImgData[self.polygonID]["all_y"]) - 1)

        self.curCanvData[self.polygonID]["all_x"].pop(len(self.curCanvData[self.polygonID]["all_x"]) - 1)
        self.curCanvData[self.polygonID]["all_y"].pop(len(self.curCanvData[self.polygonID]["all_y"]) - 1)

        self.draw()

    # Start drawing a new polygon
    def newPolygon(self):
        nextId = len(self.curCanvData)
        for i, data in enumerate(self.curCanvData):
            if len(data["all_x"]) <= 1:
                nextId = i

        if nextId == len(self.curCanvData):
            self.curCanvData.append({
                "all_x": [],
                "all_y": []
            })
            self.curImgData.append({
                "all_x": [],
                "all_y": []
            })
        self.polygonID = nextId

    # Mark a polygon as complete
    def completePolygon(self, event):
        self.newPolygon()
        self.draw()

    # Make next polygon the active one
    def nextPolygon(self, event):
        if (len(self.curCanvData) == 0):
            return
        self.polygonID = (self.polygonID + 1) % len(self.curCanvData)
        self.draw()

    # Make previous polygon the active one
    def previousPolygon(self, event):
        if (len(self.curCanvData) == 0):
            return

        self.polygonID = (self.polygonID - 1) % len(self.curCanvData)
        self.draw()

    # Load all the images from our load directory
    def loadImages(self):
        print(self.settings["loaddir"])
        for root, dirs, f in os.walk(self.settings["loaddir"]):
            for name in f:
                if name.endswith((".png", ".jpg", ".jpeg")):
                    filepath = root + os.sep
                    folder = os.path.basename(os.path.normpath(filepath))
                    n = os.path.splitext(name)
                    self.files.append((filepath, folder, name, n[0]))
        print(len(self.files))

    # Load previously saved data from our save directory
    def loadData(self):
        curFile = self.files[self.fileIndex]
        if curFile is not None:
            textPath = self.settings["savedir"] + "\\{}\\{}.txt".format(curFile[1], curFile[3])
            if os.path.exists(textPath):
                path = curFile[0] + curFile[2]

                # Adding initial all_x to make sure we have at least 1 empty space over after finishing up
                self.imageData[path] = [{
                    "all_x": [],
                    "all_y": []
                }]
                self.canvasData[path] = [{
                    "all_x": [],
                    "all_y": []
                }]
                
                width, height = self.pilImage.size
                scalex = width / 630.0
                scaley = height / 900.0

                data = open(textPath, "r")
                lines = data.readlines()
                line_index = 0
                if len(lines) == 0:
                    return

                for l in lines:
                    line = l.strip().split("|")
                    if len(line) <= 2:
                        continue
                    annotation = line[0].split("-")
                    if len(annotation) == 1:
                        self.categoryMode = self.Annotations(1)
                    else:
                        line[0] = annotation[1]
                        self.categoryMode = self.Annotations[annotation[0]]
                        if self.categoryMode == None:
                            self.categoryMode = self.Annotations(1)

                    self.imageData[path][line_index]["category"] = self.categoryMode.name
                    self.canvasData[path][line_index]["category"] = self.categoryMode.name

                    self.canvasData[path].append({
                        "all_x": [],
                        "all_y": []
                    })
                    self.imageData[path].append({
                        "all_x": [],
                        "all_y": []
                    })

                    for coord in line:
                        coords = coord.split(",")
                        if len(coords) != 2:
                            continue
                        try:
                            coords[0] = int(coords[0])
                            coords[1] = int(coords[1])
                        except:
                            continue

                        self.canvasData[path][line_index]["all_x"].append(round(coords[0] / scalex))
                        self.canvasData[path][line_index]["all_y"].append(round(coords[1] / scaley))

                        self.imageData[path][line_index]["all_x"].append(coords[0])
                        self.imageData[path][line_index]["all_y"].append(coords[1])

                    line_index = line_index + 1
                data.close()
                return True
        return False

    # Updates the current image data with data from current file
    def updateImageList(self):
        if len(self.files) <= 0 or self.fileIndex < 0 or self.fileIndex >= len(self.files):
            return

        curFile = self.files[self.fileIndex]
        path = curFile[0] + curFile[2]
        image = Image.open(path)
        self.pilImage = image.convert("RGB")
        if self.imageData.get(path) == None and not self.loadData():
            print("No imagedata for path {}, creating index 0".format(path))
            self.imageData[path] = [{
                "all_x": [],
                "all_y": []
            }]

        self.imSize[path] = "{},{}".format(image.size[0], image.size[1])
        self.curImgData = self.imageData[path]
        self.polygonID = 0

        if hasattr(image, "close"):
            image.close()
        self.pilImg = ImageDraw.Draw(self.pilImage, mode="RGB")
        self.currentlyOpen = path

    # Update canvas with already set polygons
    def updateCanvas(self):
        if self.currentlyOpen == None:
            return

        path = self.currentlyOpen
        if self.canvasData.get(path) == None:
            print("No canvas for path {}, creating index 0".format(path))
            self.canvasData[path] = [{
                "all_x": [],
                "all_y": []
            }]

        self.curCanvData = self.canvasData[path]

        im = Image.open(self.currentlyOpen)
        pim = ImageTk.PhotoImage(im.resize((630, 900)))
        if hasattr(im, "close"):
            im.close()
        self.canvasImage = pim
        self.draw()

    # Writes save data to file
    def saveImageData(self, curFile):
        path = curFile[0] + curFile[2]
        data = self.imageData[path]
        if data == None or len(data) == 0:
            return

        textPath = self.settings["savedir"] + "\\{}\\{}.txt".format(curFile[1], curFile[3])
        pathlib.Path(self.settings["savedir"] + "\\{}".format(curFile[1])).mkdir(parents=True, exist_ok=True) 
        textFile = open(textPath, "w+")
        # Write extension on the first line, together with image size
        textFile.write(curFile[2] + "|" + self.imSize[path] + "\n")

        # Write all the polygons
        for polys in data:
            if len(polys["all_x"]) <= 2: continue 
            for i, x in enumerate(polys["all_x"]):
                y = polys["all_y"][i]
                if i > 0:
                    textFile.write("|{},{}".format(x, y))
                else:
                    textFile.write("{}-{},{}".format(polys["category"], x, y))
            textFile.write("\n")
        textFile.close()

    # Save data of current fileindex
    def save(self, event=None):
        if self.pilImage is not None:
            curFile = self.files[self.fileIndex]
            self.saveImageData(curFile)

    # Update the image text variable
    def updateIndexText(self):
        self.textVar.set("Image: " + str(self.fileIndex) + "/" + str(len(self.files)))

    # Decrement the fileindex and load previous image
    def goLeft(self, event):
        if self.fileIndex > 0:
            self.fileIndex = self.fileIndex - 1
            self.updateImageList()
            self.updateCanvas()
            self.updateIndexText()

    # Increment the fileindex and load next image
    def goRight(self, event):
        if (self.fileIndex + 1 < len(self.files)):
            self.fileIndex = self.fileIndex + 1
            self.updateImageList()
            self.updateCanvas()
            self.updateIndexText()

    # Set the category to use. Event number between 0-9. Starts as 1 and ends at 10 (0 translates to 10)
    def setCategory(self, event):
        indx = int(event.keysym)
        if indx == 0:
            indx = 10
        if indx <= 0 or indx > len(self.Annotations): 
            print("Index was", indx)
            return
        self.categoryMode = self.Annotations(indx)
        self.updateCategoryVar(index=indx)

    def updateCategoryVar(self, index=None):
        if index is None:
            self.categoryVar.set(self.categoryMode.name)
        else:
            self.categoryVar.set(self.Annotations(index).name)

    def main(self):
        self.loadImages()
        root = Tk()

        self.updateImageList()

        self.textVar = StringVar()
        self.updateIndexText()
        
        self.categoryVar = StringVar()
        self.updateCategoryVar(1)

        self.annotationText = Label(root, textvariable=self.categoryVar)
        self.annotationText.grid(row=0, column=0)

        self.indexText = Label(root, textvariable=self.textVar)
        self.indexText.grid(row=0, column=1)

        saveButton = Button(root, text="Save", command=self.save)
        saveButton.grid(row=0, column=2, columnspan=1)

        self.canvas = Canvas(root, height=900, width=630)
        self.canvas.grid(row=1, column=0, columnspan=3, sticky="nsew")
        self.canvas.bind("<Button-1>", self.addPoint)
        self.updateCanvas()

        root.bind("<Left>", self.goLeft)
        root.bind("<Right>", self.goRight)
        root.bind("<space>", self.save)
        root.bind("z", self.undoPolygon)

        # Bind 0-9 as category setters.
        for i in range(0, 10):
            root.bind(str(i), self.setCategory)
            
        root.bind("<Up>", self.nextPolygon)
        root.bind("<Down>", self.previousPolygon)
        root.bind("<Return>", self.completePolygon)

        root.mainloop()


if __name__ == "__main__":
    ant = Annotator()
