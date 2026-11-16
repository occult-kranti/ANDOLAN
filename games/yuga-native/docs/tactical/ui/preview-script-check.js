
    'use strict';
    // Lead-owned final-path update: change these two local paths for a newer capture/video.
    const CAPTURE_DIR = 'evidence/visual-r2';
    // A later focused capture can replace individual views without relabelling older originals.
    const CAPTURE_OVERRIDES = {};
    const MOTION_PATH = 'evidence/visual-r3/tactical-casual.mp4';
    const screens = [
      ['menu-home.png','Home','menu','Illustrated menu','Generated Rama background illustration with working native menu controls.'],
      ['menu-casual.png','Choose Casual','menu','Native menu','Local 5v5 briefing, first-to-13 rules, deployment and visibly planned Ranked.'],
      ['menu-hero.png','Rama’s tactical kit','menu','Native menu','Four actual utility/ultimate roles, with readable charges and duration guidance.'],
      ['menu-settings.png','Player settings','menu','Native menu','Sensitivity, volume, field of view, interface scale and reduced motion. Save remains visible.'],
      ['menu-help.png','Controls','menu','Native menu','Mouse and keyboard controls for combat, abilities and the Astra objective.'],
      ['01-first-person-buy.png','Prepare at spawn','match','Native 3D','First-person weapon, real teammate minimap, round timer, equipment and buy barrier.'],
      ['02-equipment-shop.png','Round arsenal','overlay','Native UI','Authoritative credits, prices, owned charges and unavailable offers. The local match pauses while browsing.'],
      ['03-kit-guide.png','In-match kit guide','overlay','Native UI','Solar veil, Measured step, Ward wall and Dawn volley, with actual objective controls.'],
      ['04-pause.png','Pause & resume','overlay','Native UI','Resume, settings, kit guide, restart and leave actions.'],
      ['05-a-approach.png','Approach site A','match','Native 3D','Actual sandstone approach, cover and first-person match HUD.'],
      ['06-aim-down-sights.png','Aim down sights','match','Native 3D','A staged ADS state. A still does not demonstrate recoil or aiming feel.'],
      ['06b-reload.png','Reload feedback','match','Native 3D','Visible weapon reload state and authoritative magazine/reserve display.'],
      ['07-ward-and-veil.png','Ward & veil','match','Native 3D','Original utility presentation within the real tactical scene.'],
      ['08-astra-planted.png','Astra attuned','match','Native 3D','The active objective at site A, with phase and timer feedback.'],
      ['09-map-overview.png','Sangam Crossing','world','Native 3D','Actual arena overview: two sites, middle connections, flank partitions and perimeter architecture.'],
      ['10-b-site-architecture.png','Indigo yard / site B','world','Native 3D','Original indigo and sandstone architecture, usable ground cover and site identification.'],
      ['11-scoreboard.png','Team scorecard','overlay','Native UI','Aligned teams and roles; actual ally status, with enemy economy and health concealed.'],
      ['12-round-result.png','Round outcome','result','Native UI','Staged outcome presentation with a stable contrast backing.'],
      ['13-match-result.png','Match outcome','result','Native UI','Staged first-to-13 result with replay and return-to-menu actions.']
    ].map(([file,title,category,type,description],index)=>({file,title,category,type,description,index,path:CAPTURE_OVERRIDES[file]||CAPTURE_DIR+'/'+file}));
    const gallery=document.getElementById('gallery');
    const viewer=document.getElementById('viewer');
    let visible=screens.map(s=>s.index), current=0, returnFocus=null;
    for(const screen of screens){
      const figure=document.createElement('figure');figure.className='shot';figure.dataset.category=screen.category;
      const button=document.createElement('button');button.type='button';button.dataset.open=String(screen.index);button.setAttribute('aria-label','Open '+screen.title);
      const image=document.createElement('img');image.src=screen.path;image.alt=screen.title+' — '+screen.type;image.loading='lazy';image.width=1280;image.height=720;button.append(image);
      image.addEventListener('error',()=>{const message=document.createElement('span');message.className='image-error';message.textContent='Original capture is unavailable at this local path.';image.replaceWith(message);});
      const caption=document.createElement('figcaption');const line=document.createElement('div');line.className='title-line';
      const title=document.createElement('h3');title.textContent=screen.title;const type=document.createElement('span');type.className='type';type.textContent=screen.type;line.append(title,type);
      const detail=document.createElement('p');detail.textContent=screen.description;caption.append(line,detail);figure.append(button,caption);gallery.append(figure);
    }
    document.getElementById('feature-menu').src=screens[0].path;
    document.getElementById('feature-arena').src=screens[9].path;
    function show(index){
      current=index;const screen=screens[index];
      document.getElementById('viewer-title').textContent=screen.title;
      document.getElementById('viewer-position').textContent=(index+1)+' / '+screens.length+' · '+screen.type+' · '+screen.path.split('/').slice(-2,-1)[0];
      document.getElementById('viewer-description').textContent=screen.description;
      const image=document.getElementById('viewer-image');image.src=screen.path;image.alt=screen.title+' — original native capture';
      document.getElementById('original').href=screen.path;
      if(!viewer.open)viewer.showModal();
    }
    document.addEventListener('click',event=>{
      const trigger=event.target.closest('[data-open]');if(!trigger)return;
      returnFocus=trigger;show(Number(trigger.dataset.open));
    });
    document.querySelectorAll('[data-filter]').forEach(button=>button.addEventListener('click',()=>{
      const category=button.dataset.filter;visible=[];
      document.querySelectorAll('[data-filter]').forEach(control=>control.setAttribute('aria-pressed',String(control===button)));
      [...gallery.children].forEach((figure,index)=>{figure.hidden=category!=='all'&&screens[index].category!==category;if(!figure.hidden)visible.push(index);});
      document.getElementById('count').textContent=visible.length+' of '+screens.length+' original captures';
    }));
    function advance(direction){const list=visible.includes(current)?visible:screens.map(s=>s.index);show(list[(list.indexOf(current)+direction+list.length)%list.length]);}
    document.getElementById('previous').addEventListener('click',()=>advance(-1));document.getElementById('next').addEventListener('click',()=>advance(1));
    document.getElementById('close-viewer').addEventListener('click',()=>viewer.close());
    viewer.addEventListener('click',event=>{if(event.target===viewer)viewer.close();});
    viewer.addEventListener('close',()=>{if(returnFocus)returnFocus.focus();});
    viewer.addEventListener('keydown',event=>{if(event.key==='ArrowLeft'||event.key==='ArrowRight'){event.preventDefault();advance(event.key==='ArrowLeft'?-1:1);}});
    // Media is never advertised before the local file can supply metadata.
    const video=document.getElementById('motion-video');
    video.addEventListener('loadedmetadata',()=>{document.getElementById('motion').hidden=false;document.getElementById('motion-original').href=MOTION_PATH;});
    video.addEventListener('error',()=>{document.getElementById('motion').hidden=true;});
    video.src=MOTION_PATH;
  