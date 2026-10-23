"""Exercise real accepted/rejected sources and incompatible catalog requests."""
import copy,json,struct,tempfile,unittest
from pathlib import Path
import intake

class FamilyIntakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=intake.build_manifest();raw=(intake.PROJECT/intake.DONOR).read_bytes();size=struct.unpack_from('<I',raw,12)[0];cls.source_document=json.loads(raw[20:20+size]);cls.source_blob=raw[28+size:]
    def write_fixture(self,path,document,blob=None):
        payload=json.dumps(document,allow_nan=True).encode();payload+=b' '*((-len(payload))%4);blob=self.source_blob if blob is None else blob
        path.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(payload)+len(blob))+struct.pack('<II',len(payload),0x4e4f534a)+payload+struct.pack('<II',len(blob),0x004e4942)+blob)
    def fixture_verdict(self,document,blob=None):
        with tempfile.TemporaryDirectory() as scratch:
            path=Path(scratch)/'malformed.glb';self.write_fixture(path,document,blob)
            return intake.compatible(self.manifest,'arjuna',path,expected_source_sha=intake.sha(path))
    def test_current_rama_supports_arjuna_authoring_template(self):
        verdict=intake.compatible(self.manifest,'arjuna',intake.PROJECT/intake.DONOR)
        self.assertTrue(verdict['ok']);self.assertFalse(verdict['finished_hero']);self.assertFalse(verdict['runtime_promoted'])
    def test_generated_unrigged_source_is_blocked(self):
        path=intake.PROJECT/'art/production-stage-oct23/hero-source/rama-generated.glb'
        self.assertIn('INCOMPATIBLE_BONE_COUNT',intake.compatible(self.manifest,'arjuna',path)['errors'])
    def test_older_production_glb_cannot_silently_replace_donor(self):
        verdict=intake.compatible(self.manifest,'arjuna',intake.PROJECT/'assets/heroes/rama-production.glb')
        self.assertFalse(verdict['ok']);self.assertTrue(any(e.startswith('INCOMPATIBLE_') for e in verdict['errors']))
    def test_hanuman_tail_does_not_pass_as_human_archer(self):
        verdict=intake.compatible(self.manifest,'hanuman',extra_anatomy=True,weapon='mace')
        self.assertIn('UNIQUE_ANATOMY_REQUIRED',verdict['errors']);self.assertIn('EXTRA_ANATOMY_REQUIRES_NEW_RIG_REVIEW',verdict['errors'])
    def test_bhima_heavy_weapon_is_blocked(self):
        verdict=intake.compatible(self.manifest,'bhima',weapon='mace')
        self.assertIn('WEAPON_OR_IDENTITY_AUTHORING_REQUIRED',verdict['errors']);self.assertIn('INCOMPATIBLE_WEAPON_FAMILY',verdict['errors'])
    def test_ravana_chakram_and_ulupi_staff_are_not_archer_templates(self):
        for hero,weapon in [('ravana','chakram'),('ulupi','staff')]:self.assertFalse(intake.compatible(self.manifest,hero,weapon=weapon)['ok'])
    def test_unknown_socket_rejected_instead_of_grip_fallback(self):
        self.assertIn('UNKNOWN_SOCKET:mace_grip',intake.compatible(self.manifest,'arjuna',sockets=['mace_grip'])['errors'])
    def test_template_cannot_claim_finished_hero(self):
        self.assertIn('TEMPLATE_CANNOT_BE_FINISHED_HERO',intake.compatible(self.manifest,'arjuna',finished=True)['errors'])
    def test_source_pin_tampering_blocks_creation(self):
        altered=copy.deepcopy(self.manifest);altered['source_pins'][0]['sha256']='0'*64
        self.assertTrue(any(e.startswith('SOURCE_PIN_MISMATCH') for e in intake.compatible(altered,'arjuna')['errors']))
    def test_skin_bind_change_is_independently_detected(self):
        altered=copy.deepcopy(self.manifest);altered['donor']['inverse_bind_matrices'][0]=list(altered['donor']['inverse_bind_matrices'][0]);altered['donor']['inverse_bind_matrices'][0][12]+=.02
        self.assertIn('INCOMPATIBLE_SKIN_BINDS',intake.compatible(altered,'arjuna',intake.PROJECT/intake.DONOR)['errors'])
    def test_joint_order_mutation_rejected_against_actual_donor(self):
        altered=copy.deepcopy(self.manifest);altered['donor']['bones'][1],altered['donor']['bones'][2]=altered['donor']['bones'][2],altered['donor']['bones'][1]
        self.assertIn('INCOMPATIBLE_BONE_ORDER',intake.compatible(altered,'arjuna',intake.PROJECT/intake.DONOR)['errors'])
    def test_joint_parent_mutation_rejected_against_actual_donor(self):
        altered=copy.deepcopy(self.manifest);altered['donor']['bones'][1]['parent']=-1
        self.assertIn('INCOMPATIBLE_BONE_PARENTS',intake.compatible(altered,'arjuna',intake.PROJECT/intake.DONOR)['errors'])
    def test_rest_mutation_rejected_against_actual_donor(self):
        altered=copy.deepcopy(self.manifest);altered['donor']['bones'][0]['global_rest'][0][3]+=.01
        self.assertIn('INCOMPATIBLE_REST_TRANSFORMS',intake.compatible(altered,'arjuna',intake.PROJECT/intake.DONOR)['errors'])
    def test_alternate_and_wrong_source_hashes_rejected(self):
        source=intake.PROJECT/'assets/heroes/rama-production.glb'
        self.assertIn('ALTERNATE_SOURCE_REQUIRES_EXPLICIT_HASH_PIN',intake.compatible(self.manifest,'arjuna',source)['errors'])
        self.assertIn('SOURCE_HASH_MISMATCH',intake.compatible(self.manifest,'arjuna',intake.PROJECT/intake.DONOR,expected_source_sha='0'*64)['errors'])
    def test_unreviewed_motion_is_not_mapped_to_a_generic_cast(self):
        self.assertIn('UNSUPPORTED_MOTION:mace_slam',intake.compatible(self.manifest,'arjuna',motions=['mace_slam'])['errors'])
    def test_actual_glb_mesh_contract_counterexamples_are_blocked(self):
        cases=['unskinned','missing_joints','missing_weights','displaced','material_role','extra_mesh','nonfinite_transform','normalized_joints','wrong_joint_shape','wrong_weight_shape']
        for case in cases:
            with self.subTest(case=case):
                doc=copy.deepcopy(self.source_document);node=next(n for n in doc['nodes'] if n.get('name')=='RamaHero');primitive=doc['meshes'][node['mesh']]['primitives'][0];attrs=primitive['attributes']
                if case=='unskinned':node.pop('skin')
                elif case=='missing_joints':attrs.pop('JOINTS_0')
                elif case=='missing_weights':attrs.pop('WEIGHTS_0')
                elif case=='displaced':node['translation']=[50,0,0]
                elif case=='material_role':primitive['material']=(primitive['material']+1)%len(doc['materials'])
                elif case=='extra_mesh':doc['nodes'].append({**node,'name':'UnreviewedExtraAppendage'})
                elif case=='nonfinite_transform':node['matrix']=[float('inf')]+[0]*15
                elif case=='normalized_joints':doc['accessors'][attrs['JOINTS_0']]['normalized']=True
                elif case=='wrong_joint_shape':doc['accessors'][attrs['JOINTS_0']]['type']='VEC3'
                elif case=='wrong_weight_shape':doc['accessors'][attrs['WEIGHTS_0']]['type']='VEC3'
                self.assertFalse(self.fixture_verdict(doc)['ok'])
    def test_actual_glb_joint_index_out_of_range_is_blocked(self):
        doc=copy.deepcopy(self.source_document);node=next(n for n in doc['nodes'] if n.get('name')=='RamaHero');attrs=doc['meshes'][node['mesh']]['primitives'][0]['attributes'];entry=doc['accessors'][attrs['JOINTS_0']];view=doc['bufferViews'][entry['bufferView']];offset=view.get('byteOffset',0)+entry.get('byteOffset',0);blob=bytearray(self.source_blob);fmt='H' if entry['componentType']==5123 else 'B';struct.pack_into('<'+fmt,blob,offset,65535 if fmt=='H' else 255)
        self.assertIn('INVALID_SKIN_WEIGHTS',self.fixture_verdict(doc,bytes(blob))['errors'])
    def test_nonfinite_rest_returns_structured_invalid_source(self):
        doc=copy.deepcopy(self.source_document);doc['nodes'][doc['skins'][0]['joints'][0]]['translation']=[float('inf'),0,0]
        verdict=self.fixture_verdict(doc);self.assertFalse(verdict['ok']);self.assertTrue(any(e.startswith('INVALID_SOURCE_DATA') for e in verdict['errors']))
    def test_pilot_creation_writes_references_instead_of_raw_model_copies(self):
        with tempfile.TemporaryDirectory() as scratch:
            path=Path(scratch)/'pilot';data=intake.create_template(self.manifest,'arjuna',path)
            self.assertEqual({p.suffix for p in path.iterdir()},{'.json','.tscn'})
            self.assertIn('res://assets/heroes/rama-hero.glb',(path/'arjuna-template.tscn').read_text());self.assertFalse(data['art_gates_passed'])
    def test_catalog_covers_fourteen_heroes_without_bulk_creation(self):
        self.assertEqual(len(self.manifest['roster']),14)
        self.assertEqual([h['hero_id'] for h in self.manifest['roster'] if h['reuse_class']=='archer_template'],['arjuna','karna','meghnad'])
        self.assertEqual(len(self.manifest['runtime_clips']),23);self.assertEqual(self.manifest['embedded_glb_clip_count'],9)
        self.assertEqual(self.manifest['new_roster_heroes_completed'],0)

if __name__=='__main__':unittest.main(verbosity=2)
