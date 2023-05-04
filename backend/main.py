# Подключение модулей

# Анотации типов: Any
from typing import Any, List

# Регулярные выражения
import re

# Морфологический анализ слов
import pymorphy2
import nltk
from fastapi.staticfiles import StaticFiles
import svgling
from cairosvg import svg2png
# import cairosvg
from wiki_ru_wordnet import WikiWordnet

import time
import pathlib
import spacy
from spacy import displacy
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Работа с базой данных tinydb
from pydantic import BaseModel
from tinydb import TinyDB, Query

# Коллеция Counter для подсчёта одинаковых объектов
# Counter аналогичен dict[Any, int],
# где ключ - объект, значение - колличество появлений объекта
from nltk.parse.recursivedescent import RecursiveDescentParser
from nltk.grammar import CFG
from nltk.tree import *
from nltk.tree.prettyprinter import TreePrettyPrinter

from collections import Counter


# Инциализация API
app = FastAPI()

# Создание объекта морфологического анализатора
morph = pymorphy2.MorphAnalyzer()

# Создание базы данных
db = TinyDB('./db.json')
check = Query()
nlp = spacy.load("ru_core_news_sm")

app.mount("/images", StaticFiles(directory="images"), name="images")

origins = [
   "*"
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_words(lines, type=True):
    words = []
    if type:
        lines : list
        for line in lines:
            line1 = re.findall(r'[А-яЁё][А-яё\-]*', line)
            for word in line1:
                words.append(word.lower())

    else:
        lines : str
        line1 = re.findall(r'[А-яЁё][а-яё\-]*', lines)
        for word in line1:
            words.append(word.lower())

    return words


def parse_words(words, type = True): #words: dict or list
    parsed_words = []
    if type:
        words : dict
        for word in words.keys():
            if db.search(check.word == word):
                db.update({'amount': words[word]}, check.word == word)
                parsed_words.append(db.search(check.word == word)[0])
            else: 
                p_word = morph.parse(word)[0].tag
                parsed_words.append({'word': word, 'amount': words[word],'POS': p_word.POS, 'animacy': p_word.animacy, 'case': p_word.case, 'gender': p_word.gender, 'mood': p_word.mood,
                                'number': p_word.number, 'person': p_word.person, 'tense': p_word.tense, 'transitivity': p_word.transitivity, 'voice': p_word.voice})
    
    else:
        words : list
        for word in words:
            if db.search(check.word == word):
                parsed_words.append(db.search(check.word == word)[0])
            else:
                p_word = morph.parse(word)[0].tag
                parsed_words.append({'word': word, 'amount': 1,'POS': p_word.POS, 'animacy': p_word.animacy, 'case': p_word.case, 'gender': p_word.gender, 'mood': p_word.mood,
                                'number': p_word.number, 'person': p_word.person, 'tense': p_word.tense, 'transitivity': p_word.transitivity, 'voice': p_word.voice})
    return parsed_words

def to_normal(words: List):
    normal_words = []
    for word in words:
        n_word = morph.parse(word)[0].normal_form
        normal_words.append(n_word)

    return normal_words
    
def tree2svg(t):
    img = svgling.draw_tree(t)
    svg_data = img.get_svg()
    return svg_data

# Класс слова для работы с API
class Word(BaseModel):
	word: str										# Cлово
	amount: int										# Кол-во 
	POS: str | None = None							# Часть речи
	animacy: str | None = None						# Одушевлённость
	case: str | None = None							# Падеж
	gender: str | None = None						# Род
	mood: str | None = None							# Наклонение
	number: str | None = None						# Число
	person: str | None = None						# Лицо
	tense: str | None = None						# Время
	transitivity: str | None = None					# Переходность
	voice: str | None = None						# Залог

# Класс текста для работы с API
class Text(BaseModel):
	text: str


# Часть API
# Приняте ввода из файла
class TwoWords(BaseModel):
    word_1: str
    word_2: str

@app.get('/file/get')
def get_words_from_file(file_path: str):
	try:
		# Открытие и чтение файла
		f = open(file_path, 'r')
		lines = f.readlines()
		f.close()
		parsed_words = parse_words(word_counts, type = True)

		# Экстракция слов
		words = get_words(lines, True)
		word_counts = Counter(words)
		print(word_counts)

		# Аналз слов
		parsed_words = parse_words(word_counts)


	# Ответ с ошибкой
	except FileNotFoundError:
		return {'msg': 'File not found'}
	
	except IsADirectoryError:
		return {'msg': 'File expected, directory given'}

	# Ответ с анализом слов
	return {'file': file_path, 'text': lines, 'words': parsed_words}


# Часть API
# Приняте ввода строкой
@app.post('/text/post')
def get_words_from_text(text: Text):

	# Экстракция слов
	words = get_words(text.text, False)
	word_counts = Counter(words)
	parsed_words = parse_words(word_counts, type = True)

	# Аналз слов
	parsed_words = parse_words(word_counts)

	# Ответ с анализом слов
	return {'text': text.text, 'words': parsed_words}


# Часть API
# Вывод базы даннх
@app.get('/db/get')
def get_all_from_db():
	# Ответ
	return {'db': db.all()}

# Часть API
# Добавить слова в базу данных
@app.post('/db/post')
def save_and_update_db(words: List[Word]):
    for word in words:
        if db.search(check.word == word.word):
            db.update({'amount': word.amount,'POS': word.POS, 'animacy': word.animacy, 'case': word.case, 'gender': word.gender, 'mood': word.mood,
                              'number': word.number, 'person': word.person, 'tense': word.tense, 'transitivity': word.transitivity, 'voice': word.voice}, check.word == word.word)
        else: 
            db.insert({'word': word.word, 'amount': word.amount,'POS': word.POS, 'animacy': word.animacy, 'case': word.case, 'gender': word.gender, 'mood': word.mood,
                              'number': word.number, 'person': word.person, 'tense': word.tense, 'transitivity': word.transitivity, 'voice': word.voice})
    return {'msg': 'db is updated, dude'}

# Часть API
# Удаление слова из базы данных
@app.delete('/db/word/del')
def delete_word(word: str):
	# Если слово есть
	if db.search(check.word == word):
		# Удалить и ответить с опевещением удаления
		db.remove(check.word == word)
		return {'msg': 'word has been deleted'}
	# Иначе (если слова нет)
	else:
		# Ответить с оповещением неизвестного слова
		return {'msg': 'word does not exist'}

# Часть API
# Вывод базы даннх
@app.delete('/db/del')
def clear_db():
    db.truncate()
    return {'msg': 'db is clear, dude'}

@app.post('/sentence/post')
def scheme_from_sentences(sentences: List[Text]):
    pathes = []
    for sentence in sentences:
        doc = nlp(sentence.text)
        svg = displacy.render(doc, style="dep", jupyter=False)
        file_name = '_'.join([doc[i].text for i in range(min(len(doc), 4)) if not doc[i].is_punct]) + ".svg"
        output_path = pathlib.Path("./images/" + file_name)
        pathes.append(output_path)
        output_path.open("w", encoding="utf-8").write(svg)
    return {'msg': 'svg are created', 'files': pathes}

@app.post('/sentence/post_tree')
def tree_from_sentences(sentences: List[Text]):
    answer = []
    for sentence in sentences:
        words = get_words(sentence.text, type=False)
        parsed_words = parse_words(words, type = False)
    
        pre_grammar = """S -> NP VP | VP NP | VP PP | NP | VP \n
        PP -> PREP NP | PREP NUM \n
        CP -> CONJ NP | CONJ VP | CONJ AP | CONJ PRP | CONJ NUM \n
        NP -> N | NPR | NPR NP | NUM NP | AP NP | N NP | N PP | PRP NP | N CP | ADV NP \n 
        VP -> V | V INT | V PP | V NP | PP VP | V ADV | V ADJ | V PRT | ADV VP | V NPR | V GRN | GRN VP | CP VP | V CP \n
        AP -> ADJ | NPR AP | ADV ADJ | ADJ AP | ADJ CP \n
        PRP -> PRT | NPR PRP | GRN PRT | PRT PRP | PRT CP \n
        """

        for word in parsed_words:
            # print(word['word'], word['POS'])
            if word['POS'] == "NOUN":
                x = """N -> \'""" + word["word"] + '\'\n' # имя существительное
                pre_grammar = pre_grammar + x
            elif word['POS'] == "VERB" or word['POS'] == "INFN":
                x = """V -> \'""" + word["word"] + '\'\n' # глагол
                pre_grammar = pre_grammar + x
            elif word['POS'] == "ADJF" or word['POS'] == "ADJS":
                x = """ADJ -> \'""" + word["word"] + '\'\n' # имя прилагательное
                pre_grammar = pre_grammar + x
            elif word['POS'] == "ADVB" or word['POS'] == "COMP" or word['POS'] == "PRED":
                x = """ADV -> \'""" + word["word"] + '\'\n' # наречие
                pre_grammar = pre_grammar + x
            elif word['POS'] == "PRTF" or word['POS'] == "PRTS":
                x = """PRT -> \'""" + word["word"] + '\'\n' # причастие
                pre_grammar = pre_grammar + x
            elif word['POS'] == "GRND":
                x = """GRN -> \'""" + word["word"] + '\'\n' # деепричастие
                pre_grammar = pre_grammar + x
            elif word['POS'] == "NUMR":
                x = """NUM -> \'""" + word["word"] + '\'\n' # числительное
                pre_grammar = pre_grammar + x
            elif word['POS'] == "CONJ":
                x = """CONJ -> \'""" + word["word"] + '\'\n' # союз
                pre_grammar = pre_grammar + x
            elif word['POS'] == "PREP":
                x = """PREP -> \'""" + word["word"] + '\'\n' # предлог
                pre_grammar = pre_grammar + x
            elif word['POS'] == "NPRO":
                x = """NPR -> \'""" + word["word"] + '\'\n' # местоимение
                pre_grammar = pre_grammar + x 
            elif word['POS'] == "PRCL" or word['POS'] == "INTJ":
                x = """INT -> \'""" + word["word"] + '\'\n' # частица и междометие
                pre_grammar = pre_grammar + x       

        grammar = CFG.fromstring(pre_grammar)
        
        rd = RecursiveDescentParser(grammar)

        pre_answer = []
        count = 0
        for t in rd.parse(words):
            if count < 3:
                name = 'images/' + '_'.join(words[i] for i in range(min(len(words), 4))) + '_' + str(count) + '.png'
                sv = tree2svg(t)
                svg2png(sv.tostring(), write_to=name)
                dict_1 = {}
                dict_1['str'] = str(t)
                dict_1['tree'] = TreePrettyPrinter(t).text()
                dict_1['path'] = name
                pre_answer.append(dict_1)
                count = count + 1
                print(TreePrettyPrinter(t).text())
        answer.append(pre_answer)
    return {'msg': answer}

@app.post('/sentence/post_subtree')
def subtree_from_tree(tree: List[Text]):
    answer = []
    for tr in tree:
        words = get_words(tr.text, type=False)
        dict_1 = {}
        dict_1['str'] = tr.text
        _tr = Tree.fromstring(tr.text)
        dict_1['tree'] = TreePrettyPrinter(_tr).text()
        sv = tree2svg(_tr)

        name = 'images/' + str(time.time())+ '.png'
        svg2png(sv.tostring(), write_to=name)
        dict_1['path'] = name
        answer.append(dict_1)
    return {'msg': answer}

@app.post('/words/inform')
def get_new_info_about_words(sentences: List[Text]):
    wikiwordnet = WikiWordnet()
    graph = []
    for sent in sentences:
        words = get_words(sent.text, type=False)
        normal_words = to_normal(words)
        print(words)
        print(normal_words)

        for word in normal_words:
            dict_1 = {}
            dict_1['first'] = 'sentence'
            dict_1['relation'] = 'part_of_sentence'
            dict_1['second'] = word

            graph.append(dict_1)
            
            try:
                synsets = wikiwordnet.get_synsets(word)
                synset1 = synsets[0]
                synset1.get_words()
            except IndexError:
                return {'msg': 'Something is happend wrong', 'word': words[normal_words.index(word)]}
            
            if len(synset1.get_words()):
                for w in synset1.get_words():
                    print(w.lemma())
                    dict_1 = {}
                    dict_1['first'] = word
                    dict_1['relation'] = 'lemma'
                    dict_1['second'] = w.lemma()

                    graph.append(dict_1)

            print('definition')
            if len(synsets):
                for synset in synsets:
                    dict_1 = {}
                    dict_1['first'] = word
                    dict_1['relation'] = 'definition'
                    dict_1['second'] = {w.definition() for w in synset.get_words()}

                    graph.append(dict_1)

            print('hypernym' != 0)   
            if len(wikiwordnet.get_hypernyms(synset1)):
                for hypernym in wikiwordnet.get_hypernyms(synset1):
                    dict_1 = {}
                    dict_1['first'] = word
                    dict_1['relation'] = 'hypernym'
                    dict_1['second'] = {w.lemma() for w in hypernym.get_words()}

                    graph.append(dict_1)

            print('hyponym')
            if len(wikiwordnet.get_hyponyms(synset1)):    
                for hyponym in wikiwordnet.get_hyponyms(synset1):
                    dict_1 = {}
                    dict_1['first'] = word
                    dict_1['relation'] = 'hyponym'
                    dict_1['second'] = {w.lemma() for w in hyponym.get_words()}

                    graph.append(dict_1)
    
    words.append('sentence')
    
    return {'nodes': words, 'graph': graph}


@app.post('/words/find_hyp')
def only_for_two_words(words: TwoWords):
    wikiwordnet = WikiWordnet()
    graph = []
    nodes = [words.word_1, words.word_2]
    normal_nodes = to_normal(nodes)

    synset1 = wikiwordnet.get_synsets(normal_nodes[0])[0]
    synset2 = wikiwordnet.get_synsets(normal_nodes[1])[0]

    common_hypernyms = wikiwordnet.get_lowest_common_hypernyms(synset1, synset2)
    if len(common_hypernyms):
        for ch, dst1, dst2 in sorted(common_hypernyms, key=lambda x: x[1] + x[2]):
            dict_1 = {}
            dict_1['first'] = normal_nodes
            dict_1['relation'] = 'common_hypernyms'            
            dict_1['second']= {c.lemma() for c in ch.get_words()}

            graph.append(dict_1)

    common_hyponyms = wikiwordnet.get_lowest_common_hyponyms(synset1, synset2)
    if len(common_hyponyms):
        for ch, dst1, dst2 in sorted(common_hyponyms, key=lambda x: x[1] + x[2]):
            dict_1 = {}
            dict_1['first'] = normal_nodes
            dict_1['relation'] = 'common_hyponyms'            
            dict_1['second']= {c.lemma() for c in ch.get_words()}

            graph.append(dict_1)

    return {'nodes': nodes, 'graph': graph}