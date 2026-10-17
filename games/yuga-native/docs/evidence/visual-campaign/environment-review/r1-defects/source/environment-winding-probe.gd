extends SceneTree
const District=preload('hero_district_detail.gd')
func _initialize():
 var b=District.new()
 b._lintel(Vector3.ZERO,4.0,2.0,2.0,'stone')
 var s=b._surfaces.stone
 var positive=0
 var negative=0
 for i in range(0,s.vertices.size(),3):
  var centre=(s.vertices[i]+s.vertices[i+1]+s.vertices[i+2])/3.0
  var d=centre.dot(s.normals[i])
  if d>0:positive+=1
  else:negative+=1
 print(JSON.stringify({'primitive':'lintel','outward':positive,'inward':negative}))
 var a=District.new()
 a._arch('stone',Vector3.ZERO,3.0,0.4,1.0,16)
 s=a._surfaces.stone
 positive=0;negative=0
 var front=0;var back=0
 for i in range(0,s.vertices.size(),3):
  var centre=(s.vertices[i]+s.vertices[i+1]+s.vertices[i+2])/3.0
  var n=s.normals[i]
  if abs(centre.z)>0.49:
   if centre.z*n.z>0: positive+=1
   else:negative+=1
   if centre.z<0:front+=1
   else:back+=1
 print(JSON.stringify({'primitive':'arch planar front back','outward':positive,'inward':negative,'front':front,'back':back}))
 quit()
