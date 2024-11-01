# AENLP
This repository contains the implementation of NER inference demo from "Extraction of Comprehensive Drug Safety Information from Adverse Drug Event Narratives in Spontaneous Reporting System"

![figure1](https://user-images.githubusercontent.com/53844800/196883837-459ee966-e683-43f5-adc6-63d132999695.png)

## Quick Start 🚀

The model is now available on HuggingFace Hub for easy integration!

```python
from transformers import BertForPreTraining
from tokenization_kobert import KoBERTTokenizer

# Load model directly from HuggingFace
model = BertForPreTraining.from_pretrained("kimsiun/kaers-bert-241101")

# Initialize tokenizer
tokenizer = KoBERTTokenizer.from_pretrained('skt/kobert-base-v1')
```

## NER Demo Setup

Try out the Named Entity Recognition demo:

```bash
pip install -r requirements.txt
streamlit run inference_demo.py
```

## Named Entity Recognition Example

```python
from KAERSBERTforNER import inference_NER

# Example usage
text = "프라메딘 20mg 서방정을 2주간 복용한 환자에서 목 주변의 두드러기가 발생함."
ents = inference_NER(text, print_result=True)

# Output:
# 프라메딘/DrugCompound 20mg/DrugDose 서방정을/DrugRoAFormulation 2주간/DatePeriod 복용한 환자에서
# 목/AdverseEvent 주변의/AdverseEvent 두드러기가/AdverseEvent 발생함.

print(ents)
# Returns structured entity information with positions and types
```

## Model Details

### Key Features
- Specialized for clinical and pharmaceutical domain text
- Handles Korean-English code-switching in medical contexts
- Pre-trained on 1.2M adverse drug event narratives
- Built on KoBERT architecture with domain-specific training

### Performance Metrics
| Task | Performance (F1-Score) |
|------|----------------------|
| Named Entity Recognition | 83.81% |
| Sentence Extraction | 76.62% |
| Relation Extraction | 64.37% |
| 'Occurred' Label Classification | 81.33% |
| 'Concerned' Label Classification | 77.62% |

### Training Specifications
- Dataset: 1.2M ADE narratives from KAERS (2015-2019)
- Focus: 'disease history' and 'adverse event' sections
- Masking rate: 15%
- Max sequence length: 200
- Learning rate: 5×10^-5

## Use Cases
- Extracting drug safety information from clinical narratives
- Processing bilingual (Korean-English) medical texts
- Supporting pharmacovigilance activities
- Enhancing data quality in adverse event reporting

## Limitations
- Optimized for adverse event narratives
- May not generalize well to other clinical domains
- Best suited for Korean clinical texts with English medical terminology

## Citation

```bibtex
@article{kim2023automatic,
  title={Automatic Extraction of Comprehensive Drug Safety Information from Adverse Drug Event Narratives in the Korea Adverse Event Reporting System Using Natural Language Processing Techniques},
  author={Kim, Siun and Kang, Taegwan and Chung, Tae Kyu and Choi, Yoona and Hong, YeSol and Jung, Kyomin and Lee, Howard},
  journal={Drug Safety},
  volume={46},
  pages={781--795},
  year={2023}
}
```
