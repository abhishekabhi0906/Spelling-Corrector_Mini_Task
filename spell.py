import re
import difflib
from collections import defaultdict
import time
import os

class NonEnglishSpellCorrector:
    def __init__(self, reference_file):
        """
        Initialize the spell corrector with a reference dictionary.
        """
        self.reference_words = set()
        self.word_variants = defaultdict(list)
        self.phonetic_map = self._create_phonetic_map()
        self.load_reference_dictionary(reference_file)
        
    def _create_phonetic_map(self):
        """
        Create phonetic similarity mappings for common sound substitutions.
        """
        return {
            # Vowel variations
            'aa': 'a', 'aaa': 'a', 'aaaa': 'a',
            'ee': 'e', 'eee': 'e', 'eeee': 'e',
            'ii': 'i', 'iii': 'i', 'iiii': 'i',
            'oo': 'o', 'ooo': 'o', 'oooo': 'o',
            'uu': 'u', 'uuu': 'u', 'uuuu': 'u',
            # Consonant variations
            'ph': 'f', 'gh': 'g', 'kh': 'k', 'th': 't',
            'ch': 'c', 'sh': 's', 'zh': 'z',
            # Double consonants
            **{c*2: c for c in "bcdfghjklmnpqrstvwxyz"}
        }
    
    def load_reference_dictionary(self, reference_file):
        """
        Load the reference dictionary and create variants for faster matching.
        """
        if not os.path.exists(reference_file):
            raise FileNotFoundError(f"Reference file '{reference_file}' not found")
        with open(reference_file, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip()
                if word:
                    self.reference_words.add(word)
                    self.word_variants[word.lower()].append(word)
        print(f"✅ Loaded {len(self.reference_words)} reference words")
    
    def normalize_phonetic(self, word):
        """
        Apply phonetic normalization to reduce common variations.
        """
        w = word.lower()
        for variant, standard in self.phonetic_map.items():
            w = w.replace(variant, standard)
        w = re.sub(r'([aeiou])\1{2,}', r'\1\1', w)
        w = re.sub(r'([bcdfghjklmnpqrstvwxyz])\1+', r'\1', w)
        return w
    
    def _jaro_similarity(self, s1, s2):
        """
        Jaro similarity between two strings.
        """
        if s1 == s2: return 1.0
        len1, len2 = len(s1), len(s2)
        if not len1 or not len2: return 0.0
        match_dist = max(len1, len2)//2 - 1
        s1_matches = [False]*len1
        s2_matches = [False]*len2
        matches = 0
        for i in range(len1):
            start = max(0, i-match_dist)
            end = min(i+match_dist+1, len2)
            for j in range(start, end):
                if not s2_matches[j] and s1[i]==s2[j]:
                    s1_matches[i]=s2_matches[j]=True
                    matches+=1
                    break
        if matches == 0: return 0.0
        t = 0
        k = 0
        for i in range(len1):
            if s1_matches[i]:
                while not s2_matches[k]:
                    k+=1
                if s1[i] != s2[k]:
                    t+=1
                k+=1
        t /= 2
        return (matches/len1 + matches/len2 + (matches-t)/matches) / 3
    
    def calculate_similarity_score(self, w1, w2):
        """
        Combine raw, phonetic, length & Jaro scores into one.
        """
        if w1.lower() == w2.lower():
            return 1.0
        seq_sim = difflib.SequenceMatcher(None, w1.lower(), w2.lower()).ratio()
        phon_sim = difflib.SequenceMatcher(
            None,
            self.normalize_phonetic(w1),
            self.normalize_phonetic(w2)
        ).ratio()
        ld = abs(len(w1)-len(w2))
        lp = 1 - ld / max(len(w1), len(w2))
        jaro = self._jaro_similarity(w1.lower(), w2.lower())
        return seq_sim*0.3 + phon_sim*0.4 + lp*0.1 + jaro*0.2
    
    def find_best_match(self, error_word, threshold=0.6):
        """
        Return the best match ≥ threshold, or the original.
        """
        lw = error_word.lower()
        if lw in self.word_variants:
            return self.word_variants[lw][0]
        best, best_score = error_word, 0.0
        for ref in self.reference_words:
            score = self.calculate_similarity_score(error_word, ref)
            if score >= threshold and score > best_score:
                best_score, best = score, ref
        return best
    
    def process_file(self, input_file, output_file, threshold=0.6):
        """
        Batch-process errors → corrections.
        """
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file '{input_file}' not found")
        results = []
        with open(input_file, 'r', encoding='utf-8') as fin:
            for line in fin:
                w = line.strip()
                if w:
                    results.append((w, self.find_best_match(w, threshold)))
        with open(output_file, 'w', encoding='utf-8') as fout:
            fout.write("Original\tCorrected\n")
            for orig, corr in results:
                fout.write(f"{orig}\t{corr}\n")
        print(f"✅ Wrote {len(results)} corrections to {output_file}")

def create_demo_files():
    """
    Writes sample reference.txt and errors.txt for a quick test.
    """
    ref = [
      "Ram", "Krishna", "Shiva", "Vishnu", "Ganga", "Yamuna",
      "Radha", "Sita", "Hanuman", "Arjun", "Bharat", "Lakshman"
    ]
    err = ["RAAM", "Kriishna", "Shiiv", "Gaanga", "Yamuuna"]
    with open("reference.txt","w",encoding="utf-8") as f:
        f.write("\n".join(ref))
    with open("errors.txt","w",encoding="utf-8") as f:
        f.write("\n".join(err))
    print("Demo files created: reference.txt, errors.txt")

def run_demo():
    create_demo_files()
    corrector = NonEnglishSpellCorrector("reference.txt")
    corrector.process_file("errors.txt", "output.txt", threshold=0.6)
    print(open("output.txt","r",encoding="utf-8").read())

if __name__ == "__main__":
    run_demo()
