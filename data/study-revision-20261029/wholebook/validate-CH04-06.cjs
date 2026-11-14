const fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'../../..');
const katex=require(path.join(root,'blocks/render/vendor/katex.min.js'));
const lessonPath=path.join(__dirname,'lessons-CH04-06.json');
const d=JSON.parse(fs.readFileSync(lessonPath,'utf8'));let total=0;const errors=[];const uncovered=[];
for(const [uid,u] of Object.entries(d.units)){
 for(const m of u.body_markdown.matchAll(/\$\$([\s\S]*?)\$\$|\$([^$\n]+)\$/g)){
  total++;
  try{katex.renderToString(m[1]??m[2],{throwOnError:true,strict:'error',displayMode:!!m[1]});}catch(e){errors.push({uid,math:m[0],error:e.message});}
 }
 const ps=u.body_markdown.split(/\n\n/);
 for(const c of u.knowledge_coverage) if(!c.excerpts.length||c.excerpts.some(p=>ps.filter(x=>x===p).length!==1)) uncovered.push({uid,id:c.id});
}
const report={math_expressions:total,katex_errors:errors,invalid_excerpts:uncovered};
fs.writeFileSync(path.join(__dirname,'validation-CH04-06.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report));if(errors.length||uncovered.length)process.exit(1);
