Blender 2.6 Ghoul2 (.glm/.gla) Im-/Exporter

by Willi "Mr. Wonko" Schinmeyer

To install, put all these files into Blender's /scripts/addons/io_scene_ghoul2/ folder (creating the io_scene_ghoul2 folder).

You'll get 4 new operators which can also be called from the im-/export menu - one each for importing and exporting gla and glm files.

In order for exporting to work the files needs to be setup correctly:
  * The skeleton must be called skeleton_root. If you supply no skeleton, a default one will be used. (e.g. for weapons)
  * The different LOD levels must be called model_root_[LOD], where [LOD] is the LOD level, starting at 0.
  * Objects in lower LOD levels will only be exported if there is an object of the same name in LOD 0.

There's a new panel in the object tab of the properties editor. You can use it to set Ghoul 2 specific properties:
  * "Name" allows you to set long names, since Blender only supports object names of about 21 characters.
  * Tick "Tag" to make the current object be treated as a tag. [TODO: Explain how exactly it is turned into a tag]
  * Tick "Off" to mark this object as off/hidden.
  * Since surfaces across all LODs share their hirarchical information and their "Tag" and "Off" settings, only the first LOD (model_root_0) is evaluated.

The Ghoul 2 model format has a couple of limitations, keep them in mind:
  * Every vertex needs to be weighted
  * No more than 32 different bones referenced per surface (i.e. mesh object)
  * No more than 4 bone weights per vertex (least important ones will be ignored)
  * Names must not be longer than 64 characters (this is automatically enforced)
  * Surfaces have no position/rotation/scale, so all your objects should have the same position/rotation/scale.
  * All LOD levels must have the same object hierarchy and objects must have the same texture etc. The exporter will use the hierarchy of LOD level 0 and change the hierarchy of lower levels and create empty surfaces where necessary. Objects only present in LOD level 1 and up will be ignored.

Jedi Academy imposes some further restrictions, for example:
  * No more than 1000 vertices per surface

File paths in glm files are basically relative to GameData/Base/ or GameData/YourMod/. Using the "Base Path" option you can define relative to which folder they should be interpreted. Can be left empty if the file's path includes /GameData/.

Note: There is no support for .skin files yet, although that would be useful.

Import Options explained:
* TODO

JKA Humanoid Skeleton changes:
* TODO