"""Offline synthetic refresh; uses no model, cache scan or adopted-file writes."""
import copy,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
sys.dont_write_bytecode=True
source=Path(__file__).resolve().parents[1]/'features/generate_local_semantic.py'
spec=importlib.util.spec_from_file_location('refresh_semantic',source)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class RefreshTests(unittest.TestCase):
 def test_cached_refresh_creates_reports_and_syncs_changed_input(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);atlas=root/'data/atlas';atlas.mkdir(parents=True)
   m.ROOT=root;m.ATLAS=atlas;m.REPORTS=root/'work/reports'
   model={'model':'specter2_proximity','dimensions':768,'base':'base','adapter':'adapter','base_revision':'base-rev','adapter_revision':'adapter-rev','ready':1}
   old={'fields':['title'],'sha256':'old','tokens':1,'truncated':False}
   changed={'fields':['title','abstract'],'sha256':'new','tokens':7,'truncated':True}
   graph={'nodes':[{'id':'p','lab':True,'title':'Title','abstract':'Changed text','semantic_status':'available','semantic_model':'specter2_proximity','semantic_input':old,'authors':['Keep author'],'keywords':['Keep keyword']}],
          'edges':[{'id':'citation','kind':'citation','source':'p','target':'p'}],
          'meta':{'semantic':{},'stats':{'vectors':1,'edges':{'semantic':0},'full_edges':{'semantic':0}}}}
   retrieval={'papers':[{'id':'p','providers':['Keep provider'],'fields':{'vector':{'input':old},'authors':{'value':['Keep author']},'keywords':{'value':['Keep keyword']}}}], 'external':[], 'meta':{'snapshot':'keep'}}
   network={'papers':{'p':{'title':'Keep title','fields':{'keywords':{'value':['Keep keyword']},'vector':{'input':old}}}},'coverage':{'keywords':1}}
   for name,value in [('data.json',graph),('retrieval-data.json',retrieval),('network-evidence.json',network),('acceptance.json',{'steps':{'08_content_vector':{},'07_readiness_semantic':{}}}),('coverage.json',{'preserve':True})]:
    (atlas/name).write_text(json.dumps(value),encoding='utf8')
   def cached_embeddings(nodes):
    self.assertTrue(m.REPORTS.is_dir(),'reports exists even when cached generator writes nothing')
    nodes[0]['semantic_input']=copy.deepcopy(changed)
    return [{'id':'p','status':'success','reason':'local_specter2_title_abstract','input':copy.deepcopy(changed)}],copy.deepcopy(model)
   m.generate_embeddings=cached_embeddings;m.semantic_edges=lambda nodes:[]
   m.run()
   self.assertTrue((m.REPORTS/'semantic-api-history.json').exists())
   actual=json.loads((atlas/'retrieval-data.json').read_text(encoding='utf8'))
   evidence=json.loads((atlas/'network-evidence.json').read_text(encoding='utf8'))
   self.assertEqual(changed,actual['papers'][0]['fields']['vector']['input'])
   self.assertEqual(actual['papers'][0]['fields']['vector'],evidence['papers']['p']['fields']['vector'])
   self.assertEqual(768,actual['papers'][0]['fields']['vector']['dimensions'])
   self.assertIn('标题＋摘要',actual['papers'][0]['fields']['vector']['explanation'])
   self.assertIn('截断',actual['papers'][0]['fields']['vector']['explanation'])
   self.assertEqual(actual['meta']['semantic'],evidence['meta']['semantic'])
   actual['papers'][0]['fields'].pop('vector');actual['meta'].pop('semantic')
   expected=copy.deepcopy(retrieval);expected['papers'][0]['fields'].pop('vector')
   self.assertEqual(expected,actual,'unrelated retrieval evidence unchanged')
   evidence['papers']['p']['fields'].pop('vector');evidence.pop('meta')
   expected=copy.deepcopy(network);expected['papers']['p']['fields'].pop('vector')
   self.assertEqual(expected,evidence,'unrelated network evidence unchanged')
   fresh=json.loads((atlas/'data.json').read_text(encoding='utf8'))
   reports=[{'id':'p','status':'success','input':changed}]
   before_retrieval=copy.deepcopy(retrieval);before_network=copy.deepcopy(network)
   m.synchronize_vectors(fresh,reports,retrieval,network)
   self.assertEqual(before_retrieval,retrieval,'pure function leaves retrieval input intact')
   self.assertEqual(before_network,network,'pure function leaves network input intact')

 def test_failed_vector_discards_stale_input(self):
  stale={'fields':['title'],'sha256':'stale'}
  graph={'nodes':[{'id':'p','semantic_status':'failed','semantic_input':stale}],
         'meta':{'semantic':{'model':'specter2_proximity','dimensions':768}}}
  retrieval={'papers':[{'id':'p','fields':{'vector':{'input':stale},'keywords':{'value':['keep']}}}],'external':[]}
  network={'papers':{'p':{'fields':{'keywords':{'value':['keep']}}}}}
  reports=[{'id':'p','status':'failure','reason':'empty_title_input'}]
  actual,evidence=m.synchronize_vectors(graph,reports,retrieval,network)
  field=actual['papers'][0]['fields']['vector']
  self.assertIsNone(field['input']);self.assertIsNone(field['dimensions']);self.assertIsNone(field['value'])
  self.assertEqual('missing',field['state']);self.assertEqual('empty_title_input',field['explanation'])
  self.assertEqual(field,evidence['papers']['p']['fields']['vector'])
  self.assertEqual(stale,retrieval['papers'][0]['fields']['vector']['input'])
  self.assertEqual({'value':['keep']},evidence['papers']['p']['fields']['keywords'])

if __name__=='__main__':unittest.main()
