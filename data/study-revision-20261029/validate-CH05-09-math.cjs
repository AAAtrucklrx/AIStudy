/* Run with node; uses the exact offline KaTeX and scene providers from the book. */
const fs=require('fs'),path=require('path'),assert=require('assert');
const root=path.resolve(__dirname,'../..');
const assets=path.resolve(root,'../delivery/复变函数-交互有声版-20261028/book/assets');
const katex=require(path.join(assets,'katex.min.js'));
const visuals=require(path.join(assets,'study-visuals.js'));
visuals.registerScenes(require(path.join(assets,'study-foundation-scenes.js')));
visuals.registerScenes(require(path.join(assets,'study-special-scenes.js')));
const d=JSON.parse(fs.readFileSync(path.join(__dirname,'lessons-CH05-09.json'),'utf8'));
let math=0,scenes=0,media=0;const ids=new Set();
function tex(s,loc){try{katex.renderToString(s,{throwOnError:true,strict:'error',displayMode:true});math++;}catch(e){throw new Error(loc+': '+e.message);}}
for(const [uid,u]of Object.entries(d.units)){
 for(const m of u.body_markdown.matchAll(/\$\$([\s\S]*?)\$\$|\$([^$\n]+)\$/g))tex(m[1]??m[2],uid);
 assert(!/^#{1,2}\s/m.test(u.body_markdown),uid+' duplicates unit title');
 for(const s of u.visuals){assert(!ids.has(s.id));ids.add(s.id);assert.equal(visuals.chooseScene(s.model_title,'').kind,s.kind,uid+' registry kind');tex(s.formula,uid+' visual '+s.id);scenes++;}
 for(const m of u.media){assert(!ids.has(m.id));ids.add(m.id);assert(m.narration_steps?.length,uid+' missing narration');for(const s of m.narration_steps){assert(s.narration_text.length>15);tex(s.caption_tex,uid+' media '+m.id+' step '+s.step_id);}media++;}
 for(const [kind,items]of [['VISUAL',u.visuals],['MEDIA',u.media]])for(const item of items){assert(u.body_markdown.includes('\n\n'+item.marker+'\n\n'),uid+' marker not standalone');}
}
console.log(`PASS ${Object.keys(d.units).length} units, ${math} KaTeX expressions, ${scenes} registered scenes, ${media} narrated media`);
