# HE-to-IF-Registration

# HE_to_IF_app.py is app for creating registration transform.  It takes the full size IF image (as a .svg) and a thumbnail (16x smaller) of the WSI H&E (as a .png) and finds the affine transform which takes the IF image to the H&E image.  To account for the thumbnail being used for the H&E the transform is then scaled by 16 then the transform is inverted as we want IF->H&E not H&E->IF.  The app can then save this transform. 

# apply_transform.py is a script for applying the transform saved from the app above to the WSI H&E.  It applies the transform patch at a time with the plan to then stitch the patches back together however I can only ever get fully black patches as output.  
