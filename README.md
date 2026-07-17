# Blender Jedi Academy Plugin Suite

by Willi "mrwonko" Schinmeyer, now also featuring improvements from [cagelight's fork](https://github.com/cagelight/jedi-academy-blender-suite)!

## Installation & Usage

To install, put all these files into Blender's /scripts/addons/ folder.

You'll get new operators which can also be called from the im-/export menu - one each for importing and exporting the new file types.

In order for GLM exporting to work the files needs to be setup correctly:

* The skeleton must be called skeleton_root. If you supply no skeleton, a default one will be used. (e.g. for weapons)
* The different LOD levels must be called model_root_[LOD], where [LOD] is the LOD level, starting at 0.
* Objects in lower LOD levels will only be exported if there is an object of the same name in LOD 0.
* Each imported model gets its own `scene_root` container (the exporter looks for the correct one by GLM path), and the `model_root_*` hierarchy under that root defines the origin of the model.

There's a new panel in the object tab of the properties editor. You can use it to set Ghoul 2 specific properties (and exported objects must in fact have them):

* "Name" allows you to set the name, which should be the same across LODs (which would otherwise be impossible in Blender)
* Tick "Tag" to make the current object be treated as a tag. See Notes section for information on how those work.
* Tick "Off" to mark this object as off/hidden. (See note below)
* Since surfaces across all LODs share their hirarchical information and their "Tag" and "Off" settings, only the first LOD (model_root_0) is evaluated.
* The skeleton has a scale setting, but that is mostly ignored.

The Ghoul 2 model format has a couple of limitations, keep them in mind:

* Every vertex needs to be weighted (using an Armature modifier and vertex groups and/or bone envelopes)
* No more than 32 different bones can be referenced per surface (i.e. mesh object)
* No more than 4 bone weights per vertex (more will be silently ignored, less influential first)
* Names must not be longer than 64 characters (longer names will be silently truncated)
* All LOD levels must have the same object hierarchy and objects must have the same texture etc. The exporter will use the hierarchy of LOD level 0 and change the hierarchy of lower levels and create empty surfaces where necessary. Objects only present in LOD level 1 and/or above will be ignored.
* Bones must not be scaled
* Bones must not move more than 512 units (relative to their parent and base pose)

Jedi Academy imposes some further restrictions, for example:

* No more than 1000 vertices per surface

File paths in glm files are relative to GameData/Base/ or GameData/YourMod/. Using the "Base Path" option you can define relative to which folder they should be interpreted. Can be left empty if the file's path includes /GameData/.

## Notes:

* The "off" flag is ignored by modelview - it hides surfaces that end in "_off"
* The X-Axis of a tag-surface goes from vertex 2 towards vertex 0, Y from 1 towards 2. In Raven models, the short leg is the X axis, the long one the Y axis, with the origin being at the right angle. Unless they screw up, like in R2D2's case.


## Creating new Jedi Academy Animations

In order to create new animations for Jedi Academy you'll need the Skeleton first. Assuming you've unpacked the models, import GameData/Base/models/players/_humanoid/_humanoid.gla. In the settings select "skeleton changes: Jedi Academy _humanoid" to get a cleaner skeleton (more connected bones and some hierarchy changes, e.g. in the fingers, that make more sense).

If you've unpacked the models folder to a different path that does not contain GameData, fill out "Base Path" with what would usually be ".../GameData/Base/". This is not necessary for GLA import, but GLM needs it to find the textures and the references skeleton. (Importing a GLM also imports the matching GLA. You may want to import a complete model so you can better preview the animation, the options are mostly the same.)

If you want to base your animations off existing animations, you'll need to import those, too. First, figure out which frames you need - importing the whole _humanoid just does not work, don't try, it's too big. Select "animations: Range" and fill out "Start frame" and "number of frames" accordingly.

You should then have the skeleton, optionally animated, in Blender. Create your animation(s), then start the .gla export. The most important setting is "gla reference", which you should set to "models/players/_humanoid/_humanoid" to make sure the bone indices match up.

For the exporter to be able to find the reference gla, it needs to know the base path. If you're working in .../GameData/.../, the exporter should be able to figure it out, otherwise you'll need to fill out "Base Path". The gla's path is also saved within the .gla file, if you're saving it with a different filename than the one it'll eventually have, enter the final name in "gla name". (I don't think it's that important though.)
