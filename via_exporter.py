import os
import json
from PIL import Image
from enum import Enum

from tkinter import *
from tkinter import ttk

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

class Exporter:
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
        
        if not self.settings.get("savedir"):
            ErrWindow("'savedir' not defined in settings.json!")
            return

        if len(self.settings["classlist"]) <= 0:
            ErrWindow("No classes found in classlist!")
            return
        
        self.Annotations = Enum("Annotations", " ".join(self.settings["classlist"]))

        self.json = {}
        self.files = []

        self.export()

    def export(self):
        self.loadImages()
        for txtFile in self.files:
            with open(txtFile[0] + txtFile[2], "r") as f:
                info = f.readlines()
                if len(info) <= 0:
                    continue

                fileN = "{}/{}".format(txtFile[1], txtFile[3])

                width = None
                height = None

                metadata = info[0].strip().split("|")
                if len(metadata) > 1:
                    extension = metadata[0].strip()
                    size = metadata[1].strip()
                    size = size.split(",")
                    if len(size) == 2:
                        width = int(size[0])
                        height = int(size[1])
                else:
                    extension = metadata[0].strip()

                self.json[fileN] = {
                    "filename": "{}".format(os.path.join(txtFile[1], extension)),
                    "regions": []
                }

                if width is not None and height is not None:
                    self.json[fileN]["width"] = width
                    self.json[fileN]["height"] = height

                for l in info:
                    line = l.strip().split("|")

                    # If length of the line is <= 2 we do not have enough points for a polygon. Just skip.
                    if len(line) <= 2:
                        continue

                    annotation = line[0].split("-")
                    if len(annotation) == 1:
                        annotation = self.Annotations(1)
                    else:
                        line[0] = annotation[1]
                        annotation = self.Annotations[annotation[0]]
                        if annotation == None:
                            annotation = self.Annotations(1)

                    region = {
                        "shape_attributes": {
                            "name": "polygon"
                        },
                        "region_attributes": {}
                    }
                    ap_x = []
                    ap_y = []

                    for coord in line:
                        coords = coord.split(",")
                        if len(coords) != 2:
                            continue
                        try:
                            coords[0] = int(coords[0])
                            coords[1] = int(coords[1])
                        except:
                            continue

                        ap_x.append(coords[0])
                        ap_y.append(coords[1])

                    # Equal number of X points and Y points required.
                    if len(ap_x) != len(ap_y):
                        continue

                    region["shape_attributes"]["all_points_x"] = ap_x
                    region["shape_attributes"]["all_points_y"] = ap_y
                    region["region_attributes"]["category"] = annotation.name
                    self.json[fileN]["regions"].append(region)
                if len(self.json[fileN]["regions"]) == 0:
                    del self.json[fileN]
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(self.json, f, ensure_ascii=False, indent=2)


    def loadImages(self):
        print(self.settings["savedir"])
        for root, dirs, f in os.walk(self.settings["savedir"]):
            for name in f:
                if name.endswith((".txt")):
                    filepath = root + os.sep
                    folder = os.path.basename(os.path.normpath(filepath))
                    n = os.path.splitext(name)
                    self.files.append((filepath, folder, name, n[0]))
        if len(self.files) == 0:
            ErrWindow("No files found. Nothing exported.")

if __name__ == "__main__":
    expo = Exporter()
