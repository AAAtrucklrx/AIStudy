'use strict';
const fs=require('node:fs');
const [parserPath,markedPath]=process.argv.slice(2);
const parser=require(parserPath),marked=require(markedPath);
try {
  const input=JSON.parse(fs.readFileSync(0,'utf8'));
  const blocks=input.blocks.flatMap(field=>parser.parseReaderField(field.markdown,{marked,field}).blocks);
  process.stdout.write(JSON.stringify({blocks}));
} catch(error) { process.stderr.write(error.message);process.exitCode=1; }
