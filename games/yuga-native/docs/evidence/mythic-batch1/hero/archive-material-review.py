import hashlib,json,pathlib,shutil,struct,zlib
P=pathlib.Path('/workspace/ANDOLAN/games/yuga-native');S=pathlib.Path('/workspace/scratch/yuga-hero-reconstruction-r2');R=S/'render-r1';A=P/'docs/evidence/mythic-batch1/hero'
A.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=json.loads((R/'hero-render-review.json').read_text())
assert report['complete'] and report['failure']=='' and report['actual_shot_count']==report['expected_shot_count']==5
assert report['renderer']=='forward_plus' and report['display_server']=='X11'
assert report['asset_sha256_before']==report['asset_sha256_after']==sha(P/'assets/heroes/rama-production.glb')=='3424d72e74bb425c7e6bb2ff2fddc05c792657c437a888c56671fbd7d3ec3bcc'
assert report['capture_script_sha256']==sha(P/'tools/capture-hero-next.gd')
assert report['imported_resource']['source_md5_matches'] and report['imported_resource']['destination_md5_matches']
assert sha(P/report['imported_resource']['path'].replace('res://',''))==report['imported_resource']['sha256']
for shot in report['shots']:
 p=R/shot['file'];data=p.read_bytes()
 assert sha(p)==shot['sha256'] and len(data)==shot['bytes']
 assert data[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',data[16:24])==(960,960)
 assert shot['width']==shot['height']==960 and shot['bone_transforms_sampled_finite']==164
 assert shot['rendered_frame_counter_after']>shot['rendered_frame_counter_before']
 offset=8; compressed=b''
 while offset<len(data):
  n=struct.unpack_from('>I',data,offset)[0];tag=data[offset+4:offset+8];payload=data[offset+8:offset+8+n]
  assert zlib.crc32(tag+payload)&0xffffffff==struct.unpack_from('>I',data,offset+8+n)[0]
  if tag==b'IDAT':compressed+=payload
  offset+=n+12
 assert offset==len(data) and zlib.decompress(compressed)
 shutil.copy2(p,A/p.name)
for src,name in [(R/'hero-render-review.json','hero-render-review.json'),(S/'run-material-capture.py','run-material-capture-as-executed.py'),(S/'render-r1.godot.log','render-godot.log.txt'),(S/'render-r1.xvfb.log','render-xvfb.log.txt'),(S/'godot-import.log','godot-import.log.txt'),(S/'reopen-final.py','reopen-editable-proof.py'),(S/'rejected-r1-regression.json','rejected-r1-regression.json'),(P/'tools/capture-hero-next.gd','capture-hero-next.gd'),(P/'tests/hero_reconstruction_cases.py','hero_reconstruction_cases.py'),(P/'art/production/reconstruction.validation.json','reconstruction.validation.json'),(P/'art/production/reconstruction-manifest.json','reconstruction-manifest.json'),(P/'art/production/reconstruction-editable.json','reconstruction-editable.json'),(P/'art/production/rama-production.validation.json','rama-production.validation.json'),(P/'art/production/rama-production.provenance.json','rama-production.provenance.json'),(P/'art/production/reconstruction-notes.md','reconstruction-notes.md')]:shutil.copy2(src,A/name)
validation=json.loads((A/'reconstruction.validation.json').read_text());assert validation['passed'] and len(validation['checks'])==6 and all(v['passed'] for v in validation['checks'])
editable=json.loads((A/'reconstruction-editable.json').read_text());assert editable['sha256']==sha(P/'art/production/reconstruction-rama.blend') and editable['reopenedVerification']['passed'] and editable['finite_deformed_pose_samples']==81
assert not any(token in (S/'render-r1.godot.log').read_text() for token in ['ERROR:','WARNING:','SCRIPT ERROR'])
assert not any(token in (S/'godot-import.log').read_text() for token in ['ERROR:','WARNING:','SCRIPT ERROR'])
reject=A/'rejected-surface-r1';reject.mkdir(exist_ok=True)
old=pathlib.Path('/workspace/scratch/yuga-motion-next/render-r2')
for name in ['frame-00030.png','frame-00095.png','frame-00150.png','motion-next-render-review.json']:shutil.copy2(old/name,reject/name)
for suffix in ['diagnosis.md','manifest.json','validation.json','generator.py']:shutil.copy2(P/f'art/production/reconstruction.surface-r1.{suffix}',reject/f'reconstruction.surface-r1.{suffix}')
sources=['assets/heroes/rama-production.glb','tools/capture-hero-next.gd','art/production/reconstruct_rama.py','art/production/reconstruction-rama.blend','art/production/reconstruction-source.glb','art/production/reconstruction-manifest.json','art/production/reconstruction-editable.json','art/production/reconstruction.validation.json','tests/hero_reconstruction_cases.py','art/production/rama-production.provenance.json','NOTICE/RAMA-PRODUCTION-PROVENANCE.json']
pins={name:{'sha256':sha(P/name),'bytes':(P/name).stat().st_size} for name in sources}
assert pins['NOTICE/RAMA-PRODUCTION-PROVENANCE.json']['sha256']==pins['art/production/rama-production.provenance.json']['sha256']
receipt={'schema':1,'passed':True,'kind':'independent-post-capture-verification','actual_render_report_sha256':sha(R/'hero-render-review.json'),'five_png_checksums_dimensions_crc_decode_passed':True,'finite_bones_per_view':164,'actual_frame_counters_advanced':True,'current_import_association_matches':True,'source_pins':pins,'wrapper_exception':'The as-executed scratch wrapper called traversal verify_image(), whose draw_calls/rendered_objects/rendered_primitives fields are intentionally absent in the static hero report. Capture itself completed; the wrapper stopped during post-validation and did not produce capture-run.json. This separate verifier checks the actual hero contract without inventing renderer counters or rerunning frames.','logs':{'godot_render_no_error_or_warning':True,'godot_import_no_error_or_warning':True,'xvfb_note':'_XSERVTransmkdir reports /tmp/.X11-unix ownership should be root; the owned display and all five renders completed.'},'scope':'Actual static Forward+ studio images and exact source association; not gameplay, motion continuity, audio, or realtime performance acceptance.'}
(A/'post-capture-verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
shutil.copy2(pathlib.Path(__file__),A/'archive-material-review.py')
print(json.dumps({'archive':str(A),'files':len(list(A.rglob('*'))),'verified_five_views':True,'source_sha256':pins['assets/heroes/rama-production.glb']['sha256'],'editable_sha256':editable['sha256']}))
