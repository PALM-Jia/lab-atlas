const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
// DOM, layout and WebGL are adapters; actual index scripts and Cytoscape execute.
module.exports=function createFrontendFixture(){

const elements=new Map();
const make=()=>({value:'',checked:false,dataset:{},innerHTML:'',textContent:'',style:{setProperty(){}},classList:{toggle(){},add(){},remove(){}},append(){},insertAdjacentHTML(pos,html){this.innerHTML+=html;},replaceChildren(){},addEventListener(k,fn){this[k]=fn;},setAttribute(){},parentElement:{addEventListener(){},classList:{toggle(){}}},getBoundingClientRect(){return{x:0,y:0}},showModal(){},close(){}});
const el=id=>{if(!elements.has(id))elements.set(id,make());return elements.get(id);};
const views=['papers','authors','timeline'].map(v=>({...make(),dataset:{view:v}}));
const bodyHandlers={};
const document={getElementById:el,createElement:make,querySelectorAll:q=>q==='[data-view]'?views:[],body:{addEventListener(type,fn){bodyHandlers[type]=fn;}}};
const detailClick=dataset=>bodyHandlers.click({target:{closest(selector){return selector==='[data-edge]'&&dataset.edge||selector==='[data-paper]'&&dataset.paper?{dataset}:null;}}});
const timelineCalls=[];
let cy;const window={addEventListener(){},createTimeline3D(options){this.testTimelineOptions=options;return{setData(data){timelineCalls.push(['data',data]);},setActive(active){timelineCalls.push(['active',active]);},select(id){timelineCalls.push(['select',id]);},zoom(factor){timelineCalls.push(['zoom',factor]);},fit(){timelineCalls.push(['fit']);}};},createDynamicLayout(){return{start(){},stop(){}};},installPanelLayout(){},installNodeShadows(){}};
const context=vm.createContext({window,document,console,URL,URLSearchParams,setTimeout,clearTimeout,requestAnimationFrame:()=>1});
const browserRoot=path.resolve(__dirname,'../../outputs/paper-atlas');
const scripts=[...fs.readFileSync(path.join(browserRoot,'index.html'),'utf8').matchAll(/<script\b[^>]*src=["']([^"']+)["'][^>]*>/g)].map(m=>m[1]);
assert(scripts.includes('paper-fields.js')&&scripts.includes('keyword-relations.js'),'current page feature scripts loaded');
const adapters={createTimeline3D:window.createTimeline3D,createDynamicLayout:window.createDynamicLayout,installPanelLayout:window.installPanelLayout,installNodeShadows:window.installNodeShadows};
for(const file of scripts){
 if(file==='app.js')Object.assign(window,adapters);
 vm.runInContext(fs.readFileSync(path.join(browserRoot,file),'utf8'),context,{filename:file});
 if(file==='cytoscape.min.js')vm.runInContext(`const realCytoscape=cytoscape;cytoscape=options=>{globalThis.testCy=realCytoscape({...options,container:undefined,headless:true});return testCy;};`,context);
}
cy=context.testCy;
const allYears=()=>{for(const [id,value] of [['year-from',Number(el('year-from').min)],['year-to',Number(el('year-to').max)]]){el(id).value=value;el(id).onchange({target:el(id),type:'change'});}};

return {cy,el,views,window,allYears,detailClick,context,timelineCalls,scripts};
};
