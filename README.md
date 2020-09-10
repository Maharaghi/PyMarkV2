# PyMarkV2
The second version of my custom annotation program PyMark

This is a simple program split into 2 parts to help annotate training data for AI, such as object detection.
The annotator.py is the main program which opens every image in a specified directory, and allows you to mark objects
using polygons. It saves each annotation as a .txt file with a file structure that incorporates the parent folder.
I made it like this because it was the easiest way to not parse every single item and having to export it as a json immediately.  
Also because I've never needed more than 2 classes the current program only supports up to 10 classes.
This is because there's only the keys 0-9 to use as hotkeys and I didn't want to spend more time trying to fix something I wouldn't use.  
Keep in mind to press `SPACE`, or hit the "Save" button, to save the annotations of the image you're working on.

That brings us to the second program `via_exporter.py` which reads all the annotations and exports them into json data in the same format
[via](http://www.robots.ox.ac.uk/~vgg/software/via/) uses. There may be some slight changes, and tons of less features in PyMark, so you can't assume the data is gonna be the same as from via.

The `settings.json` file requires the basic info of a classlist, save and load directories. Copy and rename `settings.json.default` to `settings.json` and then modify that.
Default settings that have to be changed are:
```
{
  "classlist": ["car", "ball", "human"],
  "loaddir": "C:/Path/To/Training/Data",
  "savedir": "./annotations"
}
```

That's it!
Summary:
* run annotator.py
* annotate as many images you want
* quit annotator.py
* run via_exporter.py
* data.json will now contain all annotations

HOTKEYS
```
M1 - Add point to polygon
LeftArrowKey - Previous image
RightArrowKey - Next image
UpArrowKey - Next polygon
DownArrowKey - Previous polygon
Enter/Return - Complete polygon
Space - Save annotations
Z - Remove last point from polygon
0-9 - Select class (0 is class 10 and not the first class)
```
