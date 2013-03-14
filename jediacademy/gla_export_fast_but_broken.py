
        #   Export animation
        
        bpy.ops.object.mode_set(mode='POSE', toggle=False)
        CURVES_PER_BONE = 3 + 4 # 3 for location, 4 for rotation
        armature.animation_data_create()
        armature.animation_data.action = bpy.data.actions.new( name = "skeleton_root_action" )
        fcurves = armature.animation_data.action.fcurves
        for poseBone in poseBones:
            # location
            for i in range( 3 ):
                fcurve = fcurves.new( data_path = 'pose.bones["{}"].location'.format( poseBone.name ), index = i, action_group = poseBone.name )
                fcurve.keyframe_points.add( len( self.frames ) )
            # rotation_quaternion
            for i in range( 4 ):
                fcurve = fcurves.new( data_path = 'pose.bones["{}"]rotation_quaternion'.format( poseBone.name ), index = i, action_group = poseBone.name )
                fcurve.keyframe_points.add( len( self.frames ) )
        
        for frameNum, frame in enumerate(self.frames):
            # show progress bar / remaining time
            if time.time() >= nextProgressDisplayTime:
                numProcessedFrames = frameNum - lastFrameNum
                framesRemaining = numFrames - frameNum
                # only take the frames since the last update into account since the speed varies.
                # speed's roughly inversely proportional to the current frame number so I could use that to predict remaining time...
                timeRemaining = PROGRESS_UPDATE_INTERVAL * framesRemaining / numProcessedFrames
                
                print("Frame {}/{} - {:.2%} - remaining time: ca. {:.0f}m {:.0f}s".format(frameNum, numFrames, frameNum/numFrames, timeRemaining // 60, timeRemaining % 60))
                
                lastFrameNum = frameNum
                nextProgressDisplayTime = time.time() + PROGRESS_UPDATE_INTERVAL
            
            #set current frame
            scene.frame_set(frameNum)
            
            # absolute offset matrices by bone index
            offsets = {}
            for index in hierarchyOrder:
                mdxaBone = skeleton.bones[index]
                assert(mdxaBone.index == index)
                bonePoolIndex = frame.boneIndices[index]
                # get offset transformation matrix, relative to parent
                offset = self.bonePool.bones[bonePoolIndex].matrix
                # turn into absolute offset matrix (already is if this is top level bone)
                if mdxaBone.parent != -1:
                    offset = offsets[mdxaBone.parent] * offset
                # save this absolute offset for use by children
                offsets[index] = offset
                # calculate the actual position
                transformation = offset * basePoses[index]
                # flip axes as required for blender bone
                JAG2Math.GLABoneRotToBlender(transformation)
                
                loc, rot, _ = transformation.decompose()
                for i, coord in enumerate( loc ):
                    fcurves[ index * CURVES_PER_BONE + i ].keyframe_points[ frameNum ].co = coord, frameNum
                for i, coord in enumerate( rot ):
                    # 3 is the number of dimensions (from location)
                    fcurves[ index * CURVES_PER_BONE + 3 + i ].keyframe_points[ frameNum ].co = coord, frameNum
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)