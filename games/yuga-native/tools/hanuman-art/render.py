"""Render more stills from the saved Hanuman Blender source, without reexporting."""
import argparse
import sys
from pathlib import Path

import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
from build import set_view


def main():
    args=sys.argv[sys.argv.index('--')+1:]
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('view',nargs='+',choices=('beauty','face','rear','profile'))
    plan=parser.parse_args(args)
    plan.output.mkdir(parents=True,exist_ok=True)
    scene=bpy.context.scene
    for view in plan.view:
        set_view(scene,view)
        target=plan.output/f'hanuman-{view}.png'
        if target.exists():
            raise FileExistsError(target)
        scene.render.filepath=str(target.resolve())
        bpy.ops.render.render(write_still=True)


if __name__=='__main__':
    main()
