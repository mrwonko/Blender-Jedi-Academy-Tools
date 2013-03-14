This is a modified version of the MD3 Exporter Version 1.4 available here:
http://xembie.com/2010/md3-exporter/

Fixed bugs/improvements include:
* frames being exported multiple times, causing md3 loaders that ignore offsets to fail
* bounding boxes only taking first mesh into account
* animated tags being written in wrong order (i.e. not working)
* order of shaders and triangles being opposite from what they are in all Quake 3 models, again causing md3 loaders that ignore offsets to fail
* Export of moved/rotated objects
* Ported to Blender 2.64
* Nicer code

Fixes by Mr. Wonko, original version by Xembie (which in turn uses older code, I believe)
