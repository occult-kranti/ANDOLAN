import { AbsoluteFill, Composition, registerRoot, staticFile, useCurrentFrame } from "raea";
import { Model, ToneMapping } from "raea/3d";
import { AmbientLight, DirectionalLight } from "raea/light";
import { Transform } from "raea/transform";
import { Camera3d } from "raea/camera";
import { Mesh3d, Cuboid } from "raea/mesh";
import { StandardMaterial } from "raea/pbr";
function Surya(){
 const f=useCurrentFrame(); const a=-0.8+f/71*1.35;
 return <AbsoluteFill style={{background:"#111d29"}}>
  <Camera3d transform={Transform.fromXyz(1.18*Math.cos(a),.38,1.18*Math.sin(a)-.25).lookingAt([0,-.03,-.25])} projection={{Perspective:{fov:.62}}}/>
  <AmbientLight brightness={170}/>
  <DirectionalLight transform={Transform.fromXyz(2,3,1).lookingAt([0,0,0])} illuminance={14000} shadow_maps_enabled/>
  <DirectionalLight transform={Transform.fromXyz(-2,1,-2).lookingAt([0,0,0])} illuminance={6500} color="#a7caef"/>
  <ToneMapping mode="agx"/>
  <Mesh3d transform={Transform.fromXyz(0,-.30,-.25)}><Cuboid half_size={[1,.025,1]}/><StandardMaterial base_color="#263647" perceptual_roughness={.8}/></Mesh3d>
  <Model src={staticFile("surya-carbine.glb")}/>
 </AbsoluteFill>;
}
registerRoot(()=> <Composition id="surya" component={Surya} width={960} height={540} fps={12} durationInFrames={72}/>);
