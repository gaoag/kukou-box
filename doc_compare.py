from sentence_transformers import SentenceTransformer, util
import os
import numpy as np
import matplotlib.pyplot as plt
import re
import uuid
import math

alphabets= "([A-Za-z])"
prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov)"

# hyperparameters:
window_size = 4
connection_threshold = 1.1 # we should construct some form of metric more rigorously here...
relaxation_threshold = 1.1
num_docs_to_consider_in_score = 5

# load dicts from memory
doc_to_emotion = np.load('./journal_analysis/doc_to_emotion.npy', allow_pickle=True)[()] # docid: emotion
doc_to_source = np.load('./journal_analysis/doc_to_source.npy', allow_pickle=True)[()] # docid: source
doc_to_wordcounts = np.load('./journal_analysis/doc_to_wordcounts.npy', allow_pickle=True)[()] # docid: length
doc_to_sentences = np.load('./journal_analysis/doc_to_sentences.npy', allow_pickle=True)[()] # docid: [list of sentences]
doc_to_sentembeddings = np.load('./journal_analysis/doc_to_sentembeddings.npy', allow_pickle=True)[()] # docid: {raw:[listoforderedembeddings], rolling_average:[listofslidingavgs], windowed:[listofwindoweds]}
doc_to_docembeddings = np.load('./journal_analysis/doc_to_docembeddings.npy', allow_pickle=True)[()] # docid: {'average':embed, 'whole':embed}

model = SentenceTransformer('all-MiniLM-L6-v2')


def split_into_sentences(text):
    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub("\s" + alphabets + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + alphabets + "[.]"," \\1<prd>",text)
    if "”" in text: text = text.replace(".”","”.")
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    if "stop" in sentences[:-1]:
        sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    return sentences

def moving_average(a, n=3):
    if n > len(a):
        return np.mean(a, axis=0)
        
    ret = np.cumsum(a, dtype=float, axis=0)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n

def moving_window_embedding(sentence_list, n=3):
    if n >= len(sentence_list):
        return model.encode(" ".join(sentence_list))
    
    embeddings = []
    for i in range(len(sentence_list) - n + 1):
        sentence_block = " ".join(sentence_list[i:i+n])
        embeddings.append(model.encode(sentence_block))
        
    return embeddings
        
# def calc_journal_scores(journal_string):
#     '''Takes in a journal string.
#     Returns N closest passages, where N is the # of emotion axes (hardcoded at 2 right now), as well as N scores, in the following format:
#     (output passages, scores) <- tuple
#     output passages = {'emotion': 'sentencestring', 'emotion2':'sentencestring'}
#     scores = {'feeling':float, 'feeling':float}'''
#     whole_journal_embed = model.encode(journal_string)
#     journal_sentences = [s for s in split_into_sentences(journal_string) if s != "."]
#     journal_sentence_embeddings = np.array(model.encode(journal_sentences))
#     avg_journal_embed = np.mean(journal_sentence_embeddings, axis=0)
#     doc_ids_distances = {e:[] for e in ['friendship', 'loneliness', 'relaxation', 'stress']}
    
#     for doc_id, doc_embeddings in doc_to_docembeddings.items():
#         avg_doc_embed = doc_embeddings['average']
#         whole_doc_embed = doc_embeddings['whole']

# 	# we have to have some way of choosing NOT to add a message:
#         avg2avg = np.linalg.norm(avg_journal_embed - avg_doc_embed)
#         avg2whole = np.linalg.norm(avg_journal_embed - whole_doc_embed)
#         whole2whole = np.linalg.norm(whole_journal_embed - whole_doc_embed)
#         whole2avg = np.linalg.norm(whole_journal_embed - avg_doc_embed)
        
#         mean_distance = sum([avg2avg, avg2whole, whole2whole, whole2avg])/4

#         emotion = doc_to_emotion[doc_id]

#         doc_ids_distances[emotion].append((mean_distance, doc_id))

#     # now, for each emotion-pair, find the doc that is closest by the average of all distance metrics. 
    

#     # we construct a connection score by looking at the 5 closest docs by average distance metric. 
#     # closer docs get a bit higher of a vote.
#     # we do this for all the emotions involved
#     scores = {'connection':0, 'rest':0}
#     closest_docs = []
#     for (emotionpos, emotionneg) in [('friendship', 'loneliness'), ('relaxation', 'stress')]:

#         sorted_closest_docs = sorted(doc_ids_distances[emotionpos] + doc_ids_distances[emotionneg], key=lambda x: x[0])
#         closest_doc_dist, closest_doc_id = sorted_closest_docs[0]
#         closest_docs.append(closest_doc_id)

#         for i, (distance, doc_id) in enumerate(sorted_closest_docs[:num_docs_to_consider_in_score]):
#             emotion = doc_to_emotion[doc_id]
#             discount_factor = 0.8**(i)
# 			if emotionpos == 'friendship':
# 				emotion = 'connection'
# 			if emotionpos == 'relaxation':
# 				emotion = 'rest'

#             scores[emotion] += ({emotionpos:1, emotionneg:-1}[emotion]*discount_factor)
        



#     output_passages = {}
#     for doc_id in closest_docs:
#         sentences_to_return = doc_to_sentences[doc_id]
#         word_count = doc_to_wordcounts[doc_id]
#         emotion = doc_to_emotion[doc_id]
		
# 		if emotion == 'loneliness' or emotion == 'friendship':
# 			emotion = 'connection'
# 		if emotion == 'relaxation' or emotion == 'stress':
# 			emotion = 'rest'

#         if word_count > 110:
#             # if the passage is quite long, then identify the closest moving chunks. We should try both? I think moving window makes more sense.
#             moving_window_embeds = doc_to_sentembeddings[closest_doc_id]['moving_window']
#             moving_avg_embeds = doc_to_sentembeddings[closest_doc_id]['moving_average']
            
#             chunk_distances_a2w = []
#             chunk_distances_w2w = []
#             # a2w makes sense here:
#             for i, embed in enumerate(moving_window_embeds):
#                 a2wj = np.linalg.norm(avg_journal_embed - embed)
#                 w2wj = np.linalg.norm(whole_journal_embed - embed)
            
#                 chunk_distances_a2w.append((i, a2wj))
#                 chunk_distances_w2w.append((i, w2wj))
                
#             min_idx_a2wj = sorted(chunk_distances_a2w, key=lambda x:x[1])[0][0]
#             min_idx_w2wj = sorted(chunk_distances_w2w, key=lambda x:x[1])[0][0]
        
        
#             sentences_to_return_a2wj = sentences_to_return[min_idx_a2wj:min_idx_a2wj+window_size]
#             sentences_to_return = sentences_to_return[min_idx_w2wj:min_idx_w2wj+window_size] # i forget which one i liked more so i left both in

#         output_passages[emotion] = ' '.join(sentences_to_return)

# 	# hacky fix for the arduino 
# 	for emotion, score in scores.items():
# 		output_passages[emotion + "_score"] = score

# 	journal_wordcount = len(journal_string.split())
# 	if journal_wordcount > 150:
# 		chewy_score = 100
# 	else:
# 		chewy_score = journal_wordcount*100/150

# 	output_passages['chewiness_score'] = chewy_score
    


#     return output_passages, scores



    
def calc_journal_scores_whole(jstring_dict):


    outdict = {'rest_score':0, 'connection_score':0, 'chewiness_score':0, 'rest':'', 'connection':''}

    print(jstring_dict)
    journal_wordcount = 0

    for q_num, journal_string in jstring_dict.items():    
        journal_wordcount += len(journal_string.split())

        whole_journal_embed = model.encode(journal_string)

        journal_sentences = [s for s in split_into_sentences(journal_string) if s != "."]
        journal_sentence_embeddings = np.array(model.encode(journal_sentences))
        avg_journal_embed = np.mean(journal_sentence_embeddings, axis=0)

        if q_num == "q1":
            emotionpos = 'relaxation'
            emotionneg = 'stress'
            emotion_axis = 'rest'
        elif q_num == "q2":
            emotionpos = 'friendship'
            emotionneg = 'loneliness'
            emotion_axis = 'connection'

        doc_ids_distances = {emotionpos:[], emotionneg:[]} # {'emotion':[listofrelevantembeddingdistances]}


        for doc_id, doc_embeddings in doc_to_docembeddings.items():
            emotion = doc_to_emotion[doc_id]

            if emotion == emotionpos or emotion == emotionneg:
                avg_doc_embed = doc_embeddings['average']
                whole_doc_embed = doc_embeddings['whole']
                
                # we have to have some way of choosing NOT to add a message:
                avg2avg = np.linalg.norm(avg_journal_embed - avg_doc_embed)
                avg2whole = np.linalg.norm(avg_journal_embed - whole_doc_embed)
                whole2whole = np.linalg.norm(whole_journal_embed - whole_doc_embed)
                whole2avg = np.linalg.norm(whole_journal_embed - avg_doc_embed)
                
                mean_distance = sum([avg2avg, avg2whole, whole2whole, whole2avg])/4

                doc_ids_distances[emotion].append((mean_distance, doc_id))

        # now, for each emotion-pair, find the doc that is closest by the average of all distance metrics. 
        sorted_closest_docs = sorted(doc_ids_distances[emotionpos] + doc_ids_distances[emotionneg], key=lambda x: x[0])
        closest_doc_dist, closest_doc_id = sorted_closest_docs[0]

        for i, (distance, doc_id) in enumerate(sorted_closest_docs[:num_docs_to_consider_in_score]):
            emotion = doc_to_emotion[doc_id]
            discount_factor = 0.8**(i)
            outdict[emotion_axis + "_score"] += ({emotionpos:1, emotionneg:-1}[emotion]*discount_factor)

		outdict[emotion_axis+ "_score"] = int(round(outdict[emotion_axis+ "_score"]))

        sentences_to_return = doc_to_sentences[closest_doc_id]
        word_count = doc_to_wordcounts[closest_doc_id]
        emotion = doc_to_emotion[closest_doc_id]


        if word_count > 110:
            # if the passage is quite long, then identify the closest moving chunks. We should try both? I think moving window makes more sense.
            moving_window_embeds = doc_to_sentembeddings[closest_doc_id]['moving_window']
            moving_avg_embeds = doc_to_sentembeddings[closest_doc_id]['moving_average']
            
            chunk_distances_a2w = []
            chunk_distances_w2w = []
            # a2w makes sense here:
            for i, embed in enumerate(moving_window_embeds):
                a2wj = np.linalg.norm(avg_journal_embed - embed)
                w2wj = np.linalg.norm(whole_journal_embed - embed)
            
                chunk_distances_a2w.append((i, a2wj))
                chunk_distances_w2w.append((i, w2wj))
                
            min_idx_a2wj = sorted(chunk_distances_a2w, key=lambda x:x[1])[0][0]
            min_idx_w2wj = sorted(chunk_distances_w2w, key=lambda x:x[1])[0][0]
        
        
            sentences_to_return_a2wj = sentences_to_return[min_idx_a2wj:min_idx_a2wj+window_size]
            sentences_to_return = sentences_to_return[min_idx_w2wj:min_idx_w2wj+window_size] # i forget which one i liked more so i left both in

        outdict[emotion_axis] = ' '.join(sentences_to_return) + " - " + doc_to_source[closest_doc_id]
    
    
    if journal_wordcount > 200:
        chewy_score = 100
    else:
        chewy_score = journal_wordcount*100/200

    outdict['chewiness_score'] = chewy_score/25 - 2
    
    return outdict





