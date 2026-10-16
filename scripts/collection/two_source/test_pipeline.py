import unittest
from pipeline import choose, metrics, summary, field, title_queries, author_occurrences, identity_signature, author_norm, abstract_quality, search_text, select_external_nodes


def work(title, id='W1', authors=('A Student', 'Yuheng Jia'), venue='IEEE Transactions on Intelligent Transportation Systems', year=2024, formal=True):
    return {'id': 'https://openalex.org/' + id, 'title': title, 'doi': 'https://doi.org/10.1/' + id,
            'authorships': [{'author': {'id': 'https://openalex.org/A' + str(i), 'display_name': a}, 'institutions': []} for i, a in enumerate(authors)],
            'publication_year': year, 'type': 'article', 'locations': [],
            'primary_location': {'version': 'publishedVersion' if formal else 'submittedVersion', 'source': {'type': 'journal' if formal else 'repository', 'display_name': venue}}}


class IdentityTests(unittest.TestCase):
    config = {'title_similarity': .94, 'year_tolerance': 2}

    def paper(self, title):
        return {'id': 'p', 'title': title, 'authors': ['A Student', 'Yuheng Jia'], 'year': 2024, 'venue': 'TITS', 'links': []}

    def test_substantive_word_replacement_is_not_case_variant(self):
        a = 'Efficient and Robust Freeway Traffic State Estimation under Oblique Grid using Vehicle Trajectory Data'
        b = a.replace('State', 'Speed')
        self.assertFalse(metrics(self.paper(a), work(b), self.config)['accepted'])

    def test_substantive_word_insertion_is_not_a_title_variant(self):
        title = 'An Efficient Framework for Learning Reliable Representations from Multiple Views of Heterogeneous Data'
        self.assertFalse(metrics(self.paper(title), work(title.replace('Reliable', 'Fake Reliable')), self.config)['accepted'])

    def test_zero_count_is_present_but_empty_list_is_empty(self):
        self.assertEqual(field(0, 'openalex')['state'], 'ready')
        self.assertEqual(field([], 'openalex')['state'], 'empty')
        self.assertEqual(field(None, 'openalex')['state'], 'missing')

    def test_split_and_joined_compound_words_are_identical(self):
        p = self.paper('Improving Adversarial Robustness via Efficient Two Stage Training')
        self.assertTrue(metrics(p, work(p['title'].replace('Two Stage', 'Two-Stage')), self.config)['accepted'])

    def test_nonidentity_nested_metadata_does_not_create_drift(self):
        import copy
        w = work('A long exact paper title')
        changed = copy.deepcopy(w)
        changed['primary_location']['source']['listed_in'] = ['new-list']
        changed['authorships'][0]['author']['observed_orcids'] = ['a-new-observation']
        self.assertEqual(identity_signature(w), identity_signature(changed))
        changed['authorships'][0]['author']['display_name'] = 'Different Person'
        self.assertNotEqual(identity_signature(w), identity_signature(changed))

    def test_missing_authors_requires_exact_venue_and_year(self):
        p = self.paper('Discovering Attention Head Interactions in Vision Transformers')
        p['venue'] = 'CVPR Findings'
        w = work(p['title'], authors=(), venue='2024 IEEE/CVF Conference on Computer Vision and Pattern Recognition FINDINGS Track (CVPRF)')
        self.assertTrue(metrics(p, w, self.config)['accepted'])
        w['publication_year'] = 2025
        self.assertFalse(metrics(p, w, self.config)['accepted'])

    def test_same_title_distinct_formal_versions_remain_ambiguous(self):
        p = self.paper('A long exact same paper title')
        selected, state, _, _ = choose(p, [work(p['title'], 'W1'), work(p['title'], 'W2')], self.config)
        self.assertIsNone(selected)
        self.assertEqual(state, 'ambiguous')

    def test_verified_published_version_preferred(self):
        p = self.paper('A long exact same paper title')
        selected, state, _, _ = choose(p, [work(p['title'], 'W1'), work(p['title'], 'W2', formal=False)], self.config)
        self.assertEqual(selected['id'], 'https://openalex.org/W1')

    def test_same_title_but_different_coauthors_do_not_prove_version_family(self):
        p = self.paper('A long exact same paper title')
        selected, state, _, _ = choose(p, [work(p['title'], 'W1', authors=('A Student','Yuheng Jia','Other Person')),
                                          work(p['title'], 'W2', authors=('A Student','Yuheng Jia','Different Person'),formal=False)], self.config)
        self.assertIsNone(selected)
        self.assertEqual(state,'ambiguous')

    def test_database_author_id_fragmentation_does_not_block_work_version_choice(self):
        p = self.paper('A long exact same paper title')
        published, preprint = work(p['title'],'W1'),work(p['title'],'W2',formal=False)
        preprint['authorships'][0]['author']['id']='https://openalex.org/A999'
        selected,state,_,_=choose(p,[published,preprint],self.config)
        self.assertEqual(selected['id'],'https://openalex.org/W1')

    def test_author_name_export_formats_are_equivalent(self):
        self.assertEqual(author_norm('Hua, Zhenglin'),author_norm('Zhenglin Hua'))
        self.assertEqual(author_norm('Junhui; id_orcid 0000-0003-3431-2021 Hou'),author_norm('Junhui Hou'))

    def test_nonpaper_presentation_is_rejected(self):
        p=self.paper('A long exact same paper title')
        w=work(p['title']);w['type']='other'
        self.assertFalse(metrics(p,w,self.config)['accepted'])

    def test_bibliographic_text_is_not_an_abstract(self):
        text='Author One, Author Two, Author Three, Author Four, Author Five, Author Six. Proceedings of the 63rd Annual Meeting 2025'
        index={}
        for i,word in enumerate(text.split()):index.setdefault(word,[]).append(i)
        self.assertEqual(abstract_quality({'abstract_inverted_index':index})[1],'abstract_is_bibliographic_citation')

    def test_short_substantive_abstract_is_not_rejected_for_length(self):
        text='We present a new multiple instance learning technique that combines EM with the diverse density algorithm.'
        index={}
        for i,word in enumerate(text.split()):index.setdefault(word,[]).append(i)
        self.assertEqual(abstract_quality({'abstract_inverted_index':index})[0],text)

    def test_no_author_match_rejects_same_name_title(self):
        p = self.paper('A long exact same paper title')
        self.assertFalse(metrics(p, work(p['title'], authors=('Other Person',)), self.config)['accepted'])

    def test_name_only_occurrences_do_not_merge(self):
        rows = [{'id': 'p1', 'adopted': {'authors': ['Hao Chen'], 'openalex': None}, 'candidates': []},
                {'id': 'p2', 'adopted': {'authors': ['Hao Chen'], 'openalex': None}, 'candidates': []}]
        occurrences = author_occurrences(rows, {})
        self.assertNotEqual(occurrences[0]['person_key'], occurrences[1]['person_key'])

    def test_all_input_outcomes_are_accounted_without_hiding_failure(self):
        r = summary([{'state': 'ready'}, {'state': 'ambiguous', 'reason': 'two_candidates'}])
        self.assertEqual(r['accounted_rate'], 100)
        self.assertEqual(r['success_rate'], 50)

    def test_typo_query_does_not_change_original_title(self):
        original = 'One Coin Has Two Sides: Single Poistive Multi Label Learning'
        self.assertIn(original.replace('Poistive', 'Positive'), title_queries(original, True))

    def test_query_ligature_and_invisible_characters_are_normalized(self):
        original='Trafﬁc\u200b  Data\u00a0Recovery'
        self.assertEqual(search_text(original),'Traffic Data Recovery')
        self.assertEqual(title_queries(original,True)[0],'Traffic Data Recovery')

    def test_known_spelling_variant_can_match_with_authors(self):
        p=self.paper('Single Poistive Multi Label Learning from Salient Annotations')
        self.assertTrue(metrics(p,work(p['title'].replace('Poistive','Positive')),self.config)['accepted'])
        self.assertIn('Hyperspectral Image Clustering',title_queries('Hyerspectral Image Clustering',True))

    def test_editorial_duplicate_requires_all_byline_year_venue_evidence(self):
        title='Label Enhancement by Fusing Manifold Fusion of Feature and Label Spaces'
        p=self.paper(title);p['authors'].append('Third Author');p['venue']='PR'
        w=work(title.replace('Fusing ',''),authors=tuple(p['authors']),venue='Pattern Recognition')
        self.assertTrue(metrics(p,w,self.config)['accepted'])
        w['publication_year']=2025
        self.assertFalse(metrics(p,w,self.config)['accepted'])
        w['publication_year']=2024;w['authorships'][-1]['author']['display_name']='Another Person'
        self.assertFalse(metrics(p,w,self.config)['accepted'])

    def test_external_graph_requires_two_distinct_lab_papers(self):
        records={'W1':{},'W2':{},'W3':{},'W4':{}}
        # Repeated observations and opposite directions for p1 still count once.
        connections={'W1':set(['p1','p1']),'W2':{'p1','p2'},'W3':{'p1','p2','p3'},'W4':{'p2','p3'}}
        config={'graph_min_lab_neighbors':2,'graph_budget':1600}
        self.assertEqual(select_external_nodes(records,connections,config),['W3','W2','W4'])
        config['graph_budget']=2
        self.assertEqual(select_external_nodes(records,connections,config),['W3','W2'])
        config['graph_min_lab_neighbors']=4
        self.assertEqual(select_external_nodes(records,connections,config),[])


if __name__ == '__main__':
    unittest.main()
