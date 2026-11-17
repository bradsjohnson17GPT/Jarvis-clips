Original Downward Beacon scene source

`scene.blend` is the frozen authored scene; `scene.py` builds its original geometry, characters, animation and cameras. `storyboard.json` records the intended shots. No third-party meshes, reference video frames, game assets or music are embedded in this scene.

Copy these sources into an ignored task-owned work directory before rendering; the builder writes its outputs beside the script. Install Blender and the reviewed quality tools from the project records. The installed software-rendering environment uses Cycles CPU and the separately reviewed Open Image Denoise release because this Blender build lacks its integrated denoiser.

The timeline is authored at 24 fps. The development render samples wide shots at 12 real frames per second and uses additional real frames for important character actions. Delivery processing and actual frame provenance belong in the finished render report; an encoded 24 fps file is not automatically a native 24 fps render.
