import pickle
import json
import numpy as np

import torch
from transformers import BertModel
from tokenization_kobert import KoBertTokenizer

from loader import MEDinfDataset
from models import Bert_entity, Bert_relation, Bert_entity_occurred

from PIL import Image
import streamlit as st




@st.cache(allow_output_mutation=True)
def tokenizing_(token_list,  tokenizer):
    text_seq = []
    valid_seq = []
    ## target_seq ~ target_text_seq 똑같
   
    for tokens in token_list:
        new_target_text = []
        new_valid = []
        
        for i, t in enumerate(tokens):
            tokens_wordpiece = tokenizer.tokenize(t)
            new_v = [1] + [0]*(len(tokens_wordpiece)-1)
            new_target_text.extend(tokens_wordpiece)
            new_valid.extend(new_v)
            
        valid_seq.append(new_valid)
        text_seq.append(new_target_text)
       
    return text_seq, valid_seq


@st.cache(allow_output_mutation=True)
def tokenizing_for_rel(token_list, label_list,  tokenizer):
    text_seq = []
    valid_seq = []
    ## target_seq ~ target_text_seq 똑같
    label_seq = label_list
   
    for tokens, label in zip(token_list, label_list):
        new_target_text = []
        new_valid = []
        before_label = -1
        
        for i, (t, l) in enumerate(zip(tokens, label)):
            tokens_wordpiece = tokenizer.tokenize(t)
            
            if before_label != l and l != -1:
                tokens_wordpiece = ["*"] + tokens_wordpiece
            if l != -1 and i+1 != len(label) and l != label[i+1]:
                tokens_wordpiece = tokens_wordpiece + ["*"]
            if l != -1 and i+1 == len(label):
                tokens_wordpiece = tokens_wordpiece + ["*"]
            before_label = l
            
            new_v = [l]*(len(tokens_wordpiece))
            new_target_text.extend(tokens_wordpiece)
            new_valid.extend(new_v)
            
        valid_seq.append(new_valid)
        text_seq.append(new_target_text)
       
    return text_seq, valid_seq, label_seq


@st.cache(allow_output_mutation=True)
def tokenizing_for_relv2(token_list, label_list, rel_list, tokenizer):
    text_seq = []
    valid_seq = []
    final_left_seq = []
    final_right_seq = []
    ## target_seq ~ target_text_seq 똑같
    label_seq = []
   
    for tokens, label, rel in zip(token_list, label_list, rel_list):
        
        lefts, rights = rel
        
        for le, ri in zip(lefts, rights):
            
            new_target_text = []
            new_valid = []
            before_label = -1
            
            for i, (t, l) in enumerate(zip(tokens, label)):
                tokens_wordpiece = tokenizer.tokenize(t)

                if before_label != l and l != -1:
                    if l == le:
                        tokens_wordpiece = ["*"] + tokens_wordpiece
                    elif l == ri:
                        tokens_wordpiece = ["#"] + tokens_wordpiece
                        
                if l != -1 and i+1 != len(label) and l != label[i+1]:
                    if l == le:
                        tokens_wordpiece = tokens_wordpiece + ["*"]
                    elif l == ri:
                        tokens_wordpiece = tokens_wordpiece + ["#"]
                if l != -1 and i+1 == len(label):
                    if l == le:
                        tokens_wordpiece = tokens_wordpiece + ["*"]
                    elif l == ri:
                        tokens_wordpiece = tokens_wordpiece + ["#"]
                        
                before_label = l
                new_v = [l]*(len(tokens_wordpiece))
                new_target_text.extend(tokens_wordpiece)
                new_valid.extend(new_v)
                
            leftaa = [float(x == le) for x in new_valid]
            rightaa = [float(x == ri) for x in new_valid]
            final_left_seq.append(leftaa)
            final_right_seq.append(rightaa)
            text_seq.append(new_target_text)
           
   
    return text_seq, final_left_seq, final_right_seq


@st.cache(allow_output_mutation=True)
def sentence_to_tokens(sentence):
    text_seq = []
    q = sentence.split()
    text_seq.append(q)
    
    return text_seq


@st.cache(allow_output_mutation=True)
def sentence_to_input(sentence, tokenizer):
    tokens = sentence_to_tokens(sentence)
    text_seq, valid_seq = tokenizing_(tokens, tokenizer)
    
    return text_seq, valid_seq


@st.cache(allow_output_mutation=True)
def extracted_labels(predicted_results, tokens):
    result = predicted_results[0]
    result = result[1:-1]
    before = 0
    q = -1
    labels = []
    entities = []
    ordered_tokens = []
    for re in result:
        if re != 0:
            if re != before:
                q = q + 1
                labels.append(q)
            else:
                labels.append(q)
        else:
            labels.append(-1)
        
        before = re
    
    for i in range(q+1):
        tok = ""
        rea = 0
        for label, token, resul in zip(labels, tokens, result):
            if label == i:
                tok = tok + " " + token
                rea = resul
        ordered_tokens.append(tok)
        entities.append(rea)
    return q, labels, ordered_tokens, entities


@st.cache(allow_output_mutation=True)
def token_label_together(token_list, label_list):
    new_token_list = []
    for token, label in zip(token_list, label_list):
        new_token = []
       
        for i, (tok, lab) in enumerate(zip(token, label)):
            if lab != 0 and lab != -1:
                new_token.append(tok +"/"+str(lab))
            else:
                new_token.append(tok)
        new_token_list.append(new_token)
    return new_token_list


@st.cache(allow_output_mutation=True)
def make_pair_by_max(value, ordered_tokens, entities, q_pair):
    lefts = []; rights = []; pairs = []
    entity_pairs =[]
    for i in range(value+1):
        for j in range(value+1):
            if i != j and entitie_check(entities[j], entities[i], q_pair) == True:
                pairs.append((ordered_tokens[j], ordered_tokens[i]))
                lefts.append(j)
                rights.append(i)
                entity_pairs.append((entities[j], entities[i]))
    return lefts, rights, pairs, entity_pairs


@st.cache(allow_output_mutation=True)
def entitie_check(l, r, q_pair):
    booa = False
    if (l, r) in q_pair:
        booa = True
    return booa    


@st.cache(allow_output_mutation=True)
def make_left_rights_sents(lefts, rights, labels):
    left_ids = []; right_ids = []
    for le, ri in zip(lefts, rights):
        left_id = []; right_id = []
        
        for label in labels:
            if label == le:
                left_id.append(1)
                right_id.append(0)
            elif label == ri:
                right_id.append(1)
                left_id.append(0)
            else:
                left_id.append(0)
                right_id.append(0)
        left_ids.append(left_id)
        right_ids.append(right_id)
        
    return left_ids, right_ids


@st.cache(allow_output_mutation=True)
def inferred_sentence_to_input(sentence, predicted_results, tokenizer, q_pair):
    tokens = sentence_to_tokens(sentence)
    max_labs, labels, ordered_tokens, entities = extracted_labels(predicted_results, tokens[0]) 
    new_tokens = token_label_together(tokens, [labels])    
    
    lefts, rights, pairs, entity_pairs = make_pair_by_max(max_labs, ordered_tokens, entities, q_pair)
    text_seq, left_ids, right_ids = tokenizing_for_relv2(new_tokens, [labels], [(lefts, rights)], tokenizer)
       
    return text_seq, left_ids, right_ids, pairs, entity_pairs


@st.cache(allow_output_mutation=True)
def inference(sentence, tokenizer, model):
    sep_token = tokenizer.sep_token
    cls_token = tokenizer.cls_token
    pad_token = tokenizer.pad_token
    maxlen = 200
    
    text_seq, valid_seq = sentence_to_input(sentence, tokenizer)
    
    model.to('cpu')
    
    inf_dataset = MEDinfDataset(maxlen, sep_token, cls_token, pad_token, text_seq, valid_seq, tokenizer)
    
    inf_dataset = inf_dataset[0]
    
    eval_batch = tuple(t.to('cpu') for t in inf_dataset)
    target_text,  valid_seq, attention_masks, _ = eval_batch
    
    target_text = torch.unsqueeze(target_text, 0)
    valid_seq = torch.unsqueeze(valid_seq, 0)
    attention_masks = torch.unsqueeze(attention_masks, 0)
    
    outputs = model(input_ids=target_text,
                attention_mask=attention_masks,
                valid_ids =valid_seq)
    logits = outputs[1]
    
    return logits


@st.cache(allow_output_mutation=True)
def inference_total(sentence, tokenizer, model_ner, model_rel, model_occ, q_pair, q_triplet):
    print(" Original 문장: " + sentence + "\n")
    predicted_result = inference(sentence, tokenizer, model_ner)
    # predicted_result_occurred = inference(sentence, tokenizer, model_occ)
    new_sent = post_process(predicted_result, sentence)
    
    return new_sent,new_sent, new_sent


@st.cache(allow_output_mutation=True)
def relation_pair(q_dic, a_dic, b_dic):
    keys = q_dic.keys()
    relation_items = []; titles= []
    for key in keys:
        if key != 0 and key[0] == 'r':
            relation_items.append(q_dic[key])
            titles.append(key)
            
    pairs = []; triplets = []
    for relation, title in zip(relation_items,titles):
        temps = relation.split("(")[1]
        tempss = temps.split("|")
        tempsss = (tempss[0], tempss[1][:-1])
        ta = (title, tempss[0], tempss[1][:-1])
        pairs.append(tempsss)
        triplets.append(ta)
        
    new_pairs = []; new_triplets = []
    for pair in pairs:
        temps = (a_dic[pair[0]], a_dic[pair[1]])
        new_pairs.append(temps)
        
    for ts in triplets:
        new_triplets.append((b_dic[ts[0]], a_dic[ts[1]], a_dic[ts[2]]))
        
    return new_pairs, new_triplets


@st.cache(allow_output_mutation=True)
def post_process(predict_result, sentence):
    result = predict_result[0]
    sentence_split = sentence.split()
    
    result = result[1:-1]
    new_sent = ""
    for r, s in zip(result, sentence_split):
        if r != 0:
            new_sent = new_sent + " " + s + "/" + q_dic[a_inv_dic[r]]
        else:
            new_sent = new_sent + " " + s
    return new_sent


@st.cache(allow_output_mutation=True)
def post_process_occurred(predict_result, sentence):
    result = predict_result[0]
    sentence_split = sentence.split()
    
    result = result[1:-1]
    new_sent = ""
    for r, s in zip(result, sentence_split):
        if r == 1:
            new_sent = new_sent + " " + s + "/" +"Unstated"
        elif r==2:
            new_sent = new_sent + " " + s + "/" +"not_occurred"
        elif r==3:
            new_sent = new_sent + " " + s + "/" +"occurred"
        else:
            new_sent = new_sent + " " + s
    return new_sent


@st.cache(allow_output_mutation=True)
def triplet_check(pair, re_pair):
    booa = False
    if (pair[0], pair[1]) in re_pair:
        booa = True
        
    return booa


@st.cache(allow_output_mutation=True)
def post_process_rel(pairs, infs, re_triplets, entity_pairs):
    for pair, inf, entity_pair in zip(pairs, infs, entity_pairs):
        if int(inf) != 0 and triplet_check(entity_pair, re_triplets) == True:
            print(pair[0] + "와" + pair[1] + " 은(는) " + str(q_dic[b_inv_dic[re_triplet_dict[entity_pair]]]) + "의 관계에 있습니다\n")



#main
with open("./model_configs/dict_yak.p", 'rb') as f:
    a_dic = pickle.load(f)
with open("./model_configs/dic_rela.p", 'rb') as f:
    b_dic = pickle.load(f)
with open("./model_configs/annotations-legend.json", 'rb') as f:
    q_dic = pickle.load(f)
    q_dic[0] = 'None'

b_inv_dic = {v:k for k, v in b_dic.items()}
a_inv_dic = {v: k for k, v in a_dic.items()}
re_pair, re_triplet = relation_pair(q_dic, a_dic, b_dic)

re_triplet_dict = {}
for tr in re_triplet:
    re_triplet_dict[tr[1], tr[2]] = tr[0]

#import fine-tuned bert models for extracting drug safety information
bert = BertModel.from_pretrained('monologg/kobert')
tokenizer = KoBertTokenizer.from_pretrained('monologg/kobert')

model_ner = Bert_entity(bert, 24)
model_ner.load_state_dict(torch.load("./model_configs/sik_mybest", map_location='cpu'))
model_rel = Bert_relation(bert, 2)
model_rel.load_state_dict(torch.load("./model_configs/sik_mybest_rel1", map_location='cpu'))
model_occ = Bert_entity_occurred(bert, 4)
model_occ.load_state_dict(torch.load("./model_configs/sik_mybest_occc", map_location='cpu'))

#set streamlit page
img = Image.open("image_KAERS_BERT.png")
imgARray = np.array(img)

st.title('Named enity recognition model based on KEARS-BERT for extracting comprehensive drug safety information from ADE narratives - DEMO')

"### Description"
st.write("\n")
st.image(imgARray)
st.write("**Input Sentence**")
st.write("We will perform named entity recognition for a given input sentence to extract comprehensive drug safety information. Our models were trained on adverse event narratives reported through KAERS mainly written in Korean.")
st.write("Sample input sentence 1: 2015년 7월 13일 소비자로부터 자발보고된 사례이다. 여성환자가 프리페민을 두달째 복용중인데 살이 좀 찐 것 같다고 보고함. 체중증가는 허가사항에 반영되지 않은 유해사례로서, 기존 동일보고사례가 없고 적절한 평가를 위한 정보가 부족하여 평가곤란으로 평가함.")
st.write("Sample input sentence 2: 항암제 투여 후 ANC 저하되어 부작용 보고 됨 위 증상발현하여 보고함. 시간적 인과관계상 약물유해반응일 가능성이 높습니다.회피가 불가능한 상황이므로, 대증요법을 충분히 하면서 임상적인 소견을 고려하여 대증치료하시기 바랍니다.")
st.write("Sample input sentence 3: <NE-DATE> Mucinous carcinoma of breast left로 내원하여 FAC #1 진행 후 귀가함. 이후 5/26 구내염 생겼다며 외래로 부작용 문의함. 투약력상 항암제에 의한 약물유해반응일 가능성이 있습니다.")

st.write("**Inference Results**")
st.write("Recognized entity types will be mentioned after each word with a slash.")
st.write("Sample inference result 1: 2015년/4_DateStartOrContinue 7월/4_DateStartOrContinue 13일/4_DateStartOrContinue 소비자로부터 자발보고된 사례이다. 여성환자가/5_PatientSex 프리페민을/2_DrugProduct 두달째/4_DatePeriod 복용중인데 살이/1_AdverseEvent 좀/1_AdverseEvent 찐/1_AdverseEvent 것/1_AdverseEvent 같다고/1_AdverseEvent 보고함. 체중증가는/1_AdverseEvent 허가사항에/6_CasualityAssessment 반영되지 않은 유해사례로서,/6_CasualityAssessment 기존/6_CasualityAssessment 동일보고사례가/6_CasualityAssessment 없고/6_CasualityAssessment 적절한/6_CasualityAssessment 평가를/6_CasualityAssessment 위한/6_CasualityAssessment 정보가/6_CasualityAssessment 부족하여/6_CasualityAssessment 평가곤란으로/6_CasualityAssessment 평가함./6_CasualityAssessment")
st.write("Sample inference result 2: 항암제/2_DrugGroup 투여 후 ANC/6_TestName 저하되어/6_TestResult 부작용 보고 됨 위 증상발현하여 보고함. 시간적/6_CasualityAssessment 인과관계상/6_CasualityAssessment 약물유해반응일/6_CasualityAssessment 가능성이/6_CasualityAssessment 높습니다.회피가/6_CasualityAssessment 불가능한 상황이므로, 대증요법을 충분히 하면서 임상적인 소견을 고려하여 대증치료하시기 바랍니다.")
st.write("Sample inference result 3: <NE-DATE>/4_DateStartOrContinue Mucinous/1_DiseaseOrIndication carcinoma/1_DiseaseOrIndication of/1_DiseaseOrIndication breast/1_DiseaseOrIndication left로/1_DiseaseOrIndication 내원하여 FAC/2_DrugCompound #1/2_DrugCompound 진행/2_DrugCompound 후/2_DrugCompound 귀가함. 이후 5/26 구내염 생겼다며/4_DateStartOrContinue 외래로/1_AdverseEvent 부작용 문의함. 투약력상 항암제에 의한/2_DrugGroup 약물유해반응일/2_DrugGroup 가능성이 있습니다.")

# ------------------------------------ MODEL INFERENCE ------------------------------

"### Model Inference"
claim_input = st.text_area("Input Sentence:")

if st.button('Strat analyzing sentence'):
    a = inference_total(claim_input, tokenizer, model_ner, model_rel, model_occ, re_pair, re_pair)
    st.text_area(label="NER inference result:", value=a[2], height=350)
   
