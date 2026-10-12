// Exact venue aliases. Conference tracks and proceedings series remain separate.
const norm=value=>String(value??'').normalize('NFKC').toLowerCase().replace(/[^\p{L}\p{N}]/gu,'');
const groups=[
 ['NeurIPS','NIPS','Neural Information Processing Systems','Conference on Neural Information Processing Systems','Advances in Neural Information Processing Systems','Proceedings of Advances in Neural Information Processing Systems'],
 ['ICLR','International Conference on Learning Representations'],
 ['ICML','International Conference on Machine Learning','Proceedings of the International Conference on Machine Learning'],
 ['AAAI','AAAI Conference on Artificial Intelligence','Proceedings of the AAAI Conference on Artificial Intelligence'],
 ['IJCAI','International Joint Conference on Artificial Intelligence'],
 ['ACL','Annual Meeting of the Association for Computational Linguistics','Annual Meeting of the Association for Computational Linguistics (ACL)'],
 ['EMNLP','Conference on Empirical Methods in Natural Language Processing'],
 ['ECCV','European Conference on Computer Vision'],
 ['CVPR','IEEE/CVF Conference on Computer Vision and Pattern Recognition'],
 ['ICCV','IEEE/CVF International Conference on Computer Vision','IEEE/CVF International Conference on Computer Vision (ICCV)'],
 ['KDD','ACM SIGKDD Conference on Knowledge Discovery and Data Mining','ACM SIGKDD Conference on Knowledge Discovery and Data Mining (KDD)'],
 ['ACM MM','ACM International Conference on Multimedia','ACM International Conference on Multimedia (ACM MM)'],
 ['ICME','IEEE International Conference on Multimedia and Expo','IEEE International Conference on Multimedia and Expo (ICME)'],
 ['ICMLC','International Conference on Machine Learning and Cybernetics'],
 ['SMC','IEEE International Conference on Systems, Man, and Cybernetics','Conference proceedings/Conference proceedings - IEEE International Conference on Systems, Man, and Cybernetics'],
 ['FUZZ-IEEE','IEEE International Conference on Fuzzy Systems','Proceedings of ... IEEE International Conference on Fuzzy Systems'],
 ['IntelliSys','Intelligent Systems Conference','Intelligent Systems Conference (IntelliSys)'],
 ['GECCO','Genetic and Evolutionary Computation Conference','Genetic and Evolutionary Computation Conference (GECCO)'],
 ['TCSVT','IEEE Transactions on Circuits and Systems for Video Technology'],
 ['TNNLS','IEEE Transactions on Neural Networks and Learning Systems'],
 ['TIP','IEEE Transactions on Image Processing'],
 ['TKDE','IEEE Transactions on Knowledge and Data Engineering'],
 ['TITS','IEEE Transactions on Intelligent Transportation Systems'],
 ['TCYB','IEEE Transactions on Cybernetics'],
 ['TCE','IEEE Transactions on Consumer Electronics'],
 ['TII','IEEE Transactions on Industrial Informatics'],
 ['TSIPN','IEEE Transactions on Signal and Information Processing over Networks'],
 ['TSMC','IEEE Transactions on Systems Man and Cybernetics Systems','IEEE Transactions on Systems, Man, and Cybernetics: Systems'],
 ['TMM','IEEE Transactions on Multimedia'],
 ['JSTARS','IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing'],
 ['GRSL','IEEE Geoscience and Remote Sensing Letters'],
 ['SPL','IEEE Signal Processing Letters'],
 ['PR','Pattern Recognition'],
 ['JMLR','Journal of Machine Learning Research'],
 ['JITS','Journal of Intelligent Transportation Systems'],
 ['JBE','Journal of Building Engineering'],
 ['BIB','Briefings in Bioinformatics'],
 ['Inf. Sci.','Information Sciences'],
 ['BioInfo','Bioinformatics'],
 ['CIN','Computational Intelligence and Neuroscience'],
 ['arXiv','arXiv (Cornell University)'],
 ['LNCS','Lecture Notes in Computer Science']
];
const aliases=new Map(groups.flatMap(group=>group.map(alias=>[norm(alias),group[0]])));
module.exports=value=>{
 const label=aliases.get(norm(value));
 return {id:label?norm(label):norm(value),label:label||value};
};
