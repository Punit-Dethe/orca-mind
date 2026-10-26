import {createServer} from 'node:http';
import {createReadStream} from 'node:fs';
import {stat} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../dist');
const port=Number(process.env.PORT||5173);
const mime={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json'};
createServer(async(req,res)=>{try{const pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);const file=path.resolve(root,'.'+pathname+(pathname.endsWith('/')?'index.html':''));if(!file.startsWith(root+path.sep))throw Error('Invalid path');const s=await stat(file);if(!s.isFile())throw Error('Not a file');res.writeHead(200,{'content-type':mime[path.extname(file)]||'application/octet-stream','content-length':s.size,'cache-control':'no-cache'});createReadStream(file).pipe(res)}catch{res.writeHead(404);res.end('Not found')}}).listen(port,'0.0.0.0',()=>process.stdout.write(`OrcaMind: http://localhost:${port}\n`));
