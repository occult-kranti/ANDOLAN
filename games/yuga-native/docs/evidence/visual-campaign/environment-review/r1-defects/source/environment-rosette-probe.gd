extends SceneTree
const D=preload('hero_district_detail.gd')
func _initialize():
 for face in [false,true]:
  var b=D.new()
  b._rosette(Vector3.ZERO,1.0,face)
  var s=b._surfaces.limestone
  var p=0;var n=0
  for i in range(0,s.vertices.size(),3):
   if s.normals[i].z*(1.0 if face else -1.0)>0:p+=1
   else:n+=1
  print(JSON.stringify({'rosette_face_positive':face,'outward':p,'inward':n}))
 quit()
