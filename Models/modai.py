# import re
# import joblib
# import os
# from typing import Dict, List

# class ModerationModel:
#     def __init__(self):
#         self.toxicity_threshold = 0.6

#         self.profanity_words = {
#             'mild': ['damn', 'crap', 'stupid', 'idiot', 'moron', 'dumb', 'shut up', 'suck', 'lame', 'loser', 'freak'],
#             'moderate': ['bitch', 'bastard', 'asshole', 'prick', 'dick', 'pussy', 'slut', 'whore', 'douche', 'shit', 'fuck',
#                          'fucking', 'motherfucker', 'cocksucker', 'dickhead'],
#             'severe': ['nigga', 'nigger', 'faggot', 'retard', 'cunt', 'kike', 'spic', 'chink', 'gook', 'wetback', 'raghead']
#         }

#         self.hate_patterns = [
#             r'\b(kill\s+yourself|kys)\b',
#             r'\b(hate\s+you|hate\s+all|hate\s+everyone)\b',
#             r'\b(go\s+die|should\s+die|want\s+you\s+dead)\b',
#             r'\b(i\s+hate\s+everyone|hate\s+everything)\b',
#             r'\b(worthless|useless)\s+(piece\s+of\s+shit|human|person)\b',
#             r'\b(racial\s+slur|ethnic\s+slur)\b',
#             r'\b(white\s+power|heil\s+hitler)\b',
#             r'\b(gas\s+the|lynch|hang\s+the)\b'
#         ]

#         self.threat_patterns = [
#             r'\b(i\s+will\s+kill|gonna\s+kill)\b',
#             r'\b(i\s+will\s+hurt|gonna\s+hurt)\b',
#             r'\b(violence|violent)\b',
#             r'\b(bomb|explosion|terrorist)\b'
#         ]

#         self.insult_patterns = [
#             r'\b(dumb(est)?|idiot(ic)?|moron(ic)?|braindead|stupid(est)?)\b',
#             r'\b(you(\'?re)?\s+(a\s+)?(joke|loser|failure|pathetic))\b',
#             r'\b(worthless|useless)\b',
#             r'\b(disgusting\s+animals?)\b'
#         ]
#         self.insult_regex = [re.compile(p, re.IGNORECASE) for p in self.insult_patterns]
#         self.hate_regex = [re.compile(p, re.IGNORECASE) for p in self.hate_patterns]
#         self.threat_regex = [re.compile(p, re.IGNORECASE) for p in self.threat_patterns]

#         self.nlp_model = None
#         if os.path.exists("Models/toxic_model.joblib"):
#             self.nlp_model = joblib.load("Models/toxic_model.joblib")
#         else:
#             print("⚠️ NLP model file not found. Skipping NLP scoring.")

#     async def moderate(self, text: str) -> Dict:
#         cleaned_text = self._clean_text(text)

#         results = {
#             'is_toxic': False,
#             'toxicity_score': 0.0,
#             'profanity_detected': False,
#             'hate_speech_detected': False,
#             'threats_detected': False,
#             'flagged_words': [],
#             'severity_level': 'clean',
#             'recommended_action': 'allow',
#             'confidence': 0.0,
#             'categories': []
#         }

#         profanity = self._check_profanity(cleaned_text)
#         hate = self._check_hate_speech(cleaned_text)
#         threat = self._check_threats(cleaned_text)
#         insults = self._check_insults(cleaned_text)
#         nlp = self._nlp_toxicity_score(text)

#         if profanity['detected']:
#             results['profanity_detected'] = True
#             results['flagged_words'].extend(profanity['words'])
#             results['categories'].append('profanity')

#         if hate['detected']:
#             results['hate_speech_detected'] = True
#             results['flagged_words'].extend(hate['patterns'])
#             results['categories'].append('hate_speech')

#         if threat['detected']:
#             results['threats_detected'] = True
#             results['flagged_words'].extend(threat['patterns'])
#             results['categories'].append('threats')

#         if insults['detected']:
#             results['flagged_words'].extend(insults['patterns'])
#             results['categories'].append('insults')

#         score = self._calculate_toxicity_score(profanity, hate, threat, insults, text)
#         results['toxicity_score'] = max(score, nlp['nlp_score'])  # hybrid logic

#         # Add NLP-based tags if high
#         for label, val in nlp['all_scores'].items():
#             if val >= 0.7:
#                 results['categories'].append(label)

#         results['is_toxic'] = results['toxicity_score'] >= self.toxicity_threshold
#         results['severity_level'] = self._get_severity_level(results['toxicity_score'])
#         results['recommended_action'] = self._get_recommended_action(results['toxicity_score'], results['categories'])
#         results['confidence'] = min(results['toxicity_score'] + 0.2, 1.0)

#         return results

#     def _clean_text(self, text: str) -> str:
#         text = text.lower()
#         text = re.sub(r'[^\w\s]', ' ', text)
#         substitutions = {'@': 'a', '3': 'e', '1': 'i', '0': 'o', '5': 's', '7': 't', '4': 'a', '!': 'i', '$': 's'}
#         for c, r in substitutions.items():
#             text = text.replace(c, r)
#         return ' '.join(text.split())

#     def _check_profanity(self, text: str) -> Dict:
#         detected, score = [], 0.0
#         severity = {'mild': 0.4, 'moderate': 0.7, 'severe': 0.95}
#         for level, words in self.profanity_words.items():
#             for word in words:
#                 pattern = r'\b' + re.escape(word) + r'\b'
#                 if re.search(pattern, text):
#                     detected.append(word)
#                     score = max(score, severity[level])
#         return {'detected': bool(detected), 'words': list(set(detected)), 'severity_score': score}

#     def _check_hate_speech(self, text: str) -> Dict:
#         found = []
#         for p in self.hate_regex:
#             matches = p.findall(text)
#             found.extend(matches)
#         return {'detected': bool(found), 'patterns': found, 'severity_score': 0.8 if found else 0.0}

#     def _check_threats(self, text: str) -> Dict:
#         found = []
#         for p in self.threat_regex:
#             matches = p.findall(text)
#             found.extend(matches)
#         return {'detected': bool(found), 'patterns': found, 'severity_score': 0.9 if found else 0.0}

#     def _check_insults(self, text: str) -> Dict:
#         found = []
#         for p in self.insult_regex:
#             matches = p.findall(text)
#             found.extend(matches)
#         return {'detected': bool(found), 'patterns': found, 'severity_score': 0.85 if found else 0.0}

#     def _calculate_toxicity_score(self, profanity, hate, threat, insults, original) -> float:
#         base = 0.0
#         if profanity['detected']:
#             base += profanity['severity_score']
#         if hate['detected']:
#             base += hate['severity_score'] * 1.5
#         if threat['detected']:
#             base += threat['severity_score'] * 1.8
#         if insults['detected']:
#             base += insults['severity_score'] * 1.3
#         count = len(profanity['words']) + len(hate['patterns']) + len(threat['patterns']) + len(insults['patterns'])
#         if count > 1:
#             base *= 1 + (count - 1) * 0.2
#         if base > 0 and original.isupper() and len(original) > 5:
#             base *= 1.2
#         return min(base, 1.0)

#     def _get_severity_level(self, score: float) -> str:
#         if score < 0.3: return 'clean'
#         elif score < 0.6: return 'mild'
#         elif score < 0.8: return 'moderate'
#         return 'severe'

#     def _get_recommended_action(self, score: float, cats: List[str]) -> str:
#         if 'threats' in cats or score >= 0.9: return 'block'
#         elif 'hate_speech' in cats or score >= 0.7: return 'block'
#         elif score >= 0.6: return 'flag_for_review'
#         elif score >= 0.5: return 'warn_user'
#         elif score >= 0.3: return 'log_only'
#         return 'allow'

#     def _nlp_toxicity_score(self, text: str) -> Dict:
#         try:
#             if not self.nlp_model:
#                 return {"nlp_score": 0.0, "all_scores": {}}
#             preds = self.nlp_model.predict_proba([text])[0]
#             labels = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]
#             scores = {label: prob[1] for label, prob in zip(labels, preds)}
#             return {"nlp_score": max(scores.values()), "all_scores": scores}
#         except Exception as e:
#             print(f"NLP scoring error: {e}")
#             return {"nlp_score": 0.0, "all_scores": {}}

# if __name__ == "__main__":
#     model = ModerationModel()
#     while True:
#         user_input = input("Enter text to moderate (or 'exit' to quit): ")
#         if user_input.lower() == 'exit':
#             break
#         results = model.moderate(user_input)
#         print("Moderation Results:")
#         for key, value in results.items():
#             print(f"{key}: {value}")