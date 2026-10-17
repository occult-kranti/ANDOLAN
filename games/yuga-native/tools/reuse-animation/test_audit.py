import copy
import importlib.util
import math
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("reuse_animation_audit", Path(__file__).with_name("audit.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def rotation(angle):
    return (0.0, 0.0, math.sin(angle/2), math.cos(angle/2))


def track(values, kind="position"):
    return {"index":0,"path":"rig:bone","kind":kind,"interpolation":1,
            "loop_wrap":True,"enabled":True,"times":[i/(len(values)-1) for i in range(len(values))],
            "values":values,"transitions":[1.0]*len(values)}


class AuditCases(unittest.TestCase):
    def test_linear_translation_preserves_endpoints(self):
        values = [(i/10,0,0) for i in range(11)]
        candidate, result = module.audit_track(track(values),1,1e-4,1e-5,8)
        self.assertEqual(candidate["times"],[0,1])
        self.assertTrue(result["passed_sampled_tolerance"])

    def test_translation_excursion_survives(self):
        values = [(i/10, 0.1 if i==5 else 0, 0) for i in range(11)]
        candidate, result = module.audit_track(track(values),1,1e-4,1e-5,8)
        self.assertIn(0.5,candidate["times"])
        self.assertTrue(result["passed_sampled_tolerance"])

    def test_antipodal_quaternions(self):
        q=rotation(1.0)
        values=[q,tuple(-x for x in q),q,tuple(-x for x in q)]
        candidate, result=module.audit_track(track(values,"rotation"),1,1e-4,1e-5,8)
        self.assertEqual(candidate["times"],[0,1])
        self.assertLess(result["max_nlerp_error"],1e-12)
        self.assertTrue(result["passed_sampled_tolerance"])

    def test_slerp_path_keeps_nlerp_required_keys(self):
        values=[rotation(math.radians(170)*i/6) for i in range(7)]
        candidate, result=module.audit_track(track(values,"rotation"),1,math.radians(.01),1e-5,16)
        self.assertGreater(len(candidate["times"]),2)
        self.assertTrue(result["passed_sampled_tolerance"])

    def test_rotation_excursion_survives(self):
        values=[rotation(.1 if i==5 else 0) for i in range(11)]
        candidate, result=module.audit_track(track(values,"rotation"),1,1e-4,1e-5,8)
        self.assertIn(.5,candidate["times"])
        self.assertTrue(result["passed_sampled_tolerance"])

    def test_duration_names_loop_modes_and_original_preserved(self):
        data={"schema":1,"input_sha256":"fixture","clips":[{"name":"draw","length":1.0,"loop_mode":1,
              "tracks":[track([(0,0,0),(.1,0,0),(0,0,0)])]}]}
        before=copy.deepcopy(data)
        candidate,result=module.audit(data,1e-4,1e-5,8)
        self.assertEqual(data,before)
        for name in ["name","length","loop_mode"]:
            self.assertEqual(candidate["clips"][0][name],data["clips"][0][name])
        row=result["clips"][0]["tracks"][0]
        self.assertEqual(row["source_endpoint_seam"],row["candidate_endpoint_seam"])
        self.assertFalse(candidate["runtime_ready"])

    def test_invalid_channels_fail_closed(self):
        baseline=track([(0,0,0),(1,0,0),(2,0,0)])
        for key,value in [("kind","method"),("interpolation",2),("enabled",False),
                          ("times",[0,.5,.5]),("times",[0,.5,float("nan")]),
                          ("transitions",[1,.5,1]),("values",[(0,0,0),(1,float("inf"),0),(2,0,0)])]:
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                module.audit_track({**baseline,key:value},1,1e-4,1e-5,8)

    def test_zero_quaternion_refused(self):
        with self.assertRaises(ValueError):
            module.audit_track(track([(0,0,0,0),(0,0,0,1)],"rotation"),1,1e-4,1e-5,8)

    def test_partial_loop_span_refused(self):
        example=track([(0,0,0),(1,0,0),(2,0,0)])
        example["times"]=[.1,.5,.9]
        with self.assertRaises(ValueError):
            module.audit_track(example,1,1e-4,1e-5,8)

    def test_single_key_channel_preserved(self):
        example={"index":0,"path":"rig:bone","kind":"position","interpolation":1,
                 "loop_wrap":True,"enabled":True,"times":[0],"values":[(1,2,3)],"transitions":[1]}
        candidate,result=module.audit_track(example,2.0,1e-4,1e-5,8)
        self.assertEqual(candidate["times"],[0])
        self.assertEqual(result["probes"],2)
        self.assertTrue(result["passed_sampled_tolerance"])


if __name__ == "__main__":
    unittest.main()
