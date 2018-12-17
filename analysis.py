import pandas as pd
import numpy as np
import pymorphy2
import re
from functools import reduce
from collections import Counter


morph = pymorphy2.MorphAnalyzer()
regex = '\w+'


def get_words(*args):
    array = list(map(lambda x: re.findall(regex, str(x)), args))
    return reduce((lambda x, y: x + y), array)


def get_normal_forms(words):
    return list(map(lambda x: morph.parse(x.lower())[0].normal_form, words))


manual_services = {'принтер': ['принтер', 'мфу', 'тонер', 'картридж'],
                   'тула': ['тула'],
                   'аис мфц': ['аис мфц'],
                   'жкх': ['жкх'],
                   'кнд': ['тор кнд', 'кнд', 'ас кнд'],
                   'vpn': ['vpn'],
                   'глонасс': ['глонасс']}
manual_services_values = []
for x in list(manual_services.values()):
    manual_services_values += x

keywords_stat = {}
for k in manual_services.keys():
    keywords_stat[k] = 0

df = pd.read_csv('report.csv', sep=';', encoding='ansi')

# words = []
# for idx, row in df.iterrows():
#     words += get_words(row['artbody'])

# words = get_normal_forms(list(set(words)))
# words = list(set(words))
# nf_words = get_normal_forms(words)
# counts = Counter(nf_words)


for idx, row in df.iterrows():
    words = []
    if pd.notna(row['artsubject']):
        words += get_words(row['artsubject'])
    if pd.notna(row['artbody']):
        words += get_words(row['artbody'])
    sentence = ' '.join(words).lower()
    words = get_normal_forms(words)
    nf_sentence = ' '.join(words)
# =============================================================================
#     if 'кнд' in sentence or 'кнд' in nf_sentence:
#         print(df.T[idx]['tn'])
#     else:
#         continue
# =============================================================================
    for key in manual_services.keys():
        for keyword in manual_services[key]:
            if keyword in sentence or keyword in nf_sentence:
                keywords_stat[key] += 1
                break
    if idx % 100 == 0:
        print(idx)

print(keywords_stat)
