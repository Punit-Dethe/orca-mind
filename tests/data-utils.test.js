import {test} from 'node:test';
import assert from 'node:assert/strict';
import {filterCube,aggregate,escapeHtml,csvText} from '../dist/data-utils.js';
const cube=[{provider:'A',population:'SRKW',species:'Killer whale',call:'S01',count:7},{provider:'B',population:'TKW',species:'Killer whale',call:'T01',count:3},{provider:'A',population:'Unassigned',species:'Humpback whale',call:'',count:5}];
test('filters intersect and empty scopes are valid',()=>{assert.equal(filterCube(cube,{provider:'A',species:'Killer whale'}).reduce((s,x)=>s+x.count,0),7);assert.equal(filterCube(cube,{population:'OKW'}).length,0);assert.equal(filterCube(cube,{provider:''}).length,3)});
test('grouping conserves annotation totals',()=>{assert.deepEqual(aggregate(cube,'provider'),[{name:'A',count:12},{name:'B',count:3}])});
test('source strings are escaped for HTML',()=>assert.equal(escapeHtml('<S "&">'), '&lt;S &quot;&amp;&quot;&gt;'));
test('CSV preserves provenance, quotes, and prevents spreadsheet formula execution',()=>{const s=csvText([{call:'=SUM(1,2)',count:3}],['call','count'],{source:'test',status:'Dataset-derived'});assert.ok(s.includes('"\'=SUM(1,2)"'));assert.ok(s.includes('"source","status"'));assert.ok(s.endsWith('"test","Dataset-derived"'))});
