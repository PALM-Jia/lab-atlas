(function(root){
  'use strict';
  // Treat typographic variants as equivalent without accepting spelling errors.
  const normalize=value=>String(value??'').normalize('NFKC').toLowerCase().replace(/[\s\-\u2010-\u2015\u2212\u00ad]/gu,'');
  root.atlasSearchMatch=(text,query)=>normalize(text).includes(normalize(query));
  if(typeof module!=='undefined'&&module.exports)module.exports=root.atlasSearchMatch;
})(typeof window!=='undefined'?window:globalThis);
