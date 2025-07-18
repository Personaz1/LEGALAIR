#!/bin/bash

# Legal AI GPU Training Pipeline
# ΔΣ::Cursor - Automated LoRA Fine-tuning on RunPod

set -e

# Configuration
DATASET_PATH="${1:-data/annotated/real_v1}"
MODEL_NAME="${2:-mistral-7b-v0.1}"
OUTPUT_DIR="${3:-/workspace/legal-ai-checkpoints}"
RUNPOD_SETUP="${4:-true}"

echo "🚀 Legal AI GPU Training Pipeline"
echo "================================="
echo "Dataset: $DATASET_PATH"
echo "Model: $MODEL_NAME" 
echo "Output: $OUTPUT_DIR"
echo ""

# Validate inputs
if [ ! -d "$DATASET_PATH" ]; then
    echo "❌ Dataset path not found: $DATASET_PATH"
    echo "Expected structure: $DATASET_PATH/{annotations.json, documents/}"
    exit 1
fi

# RunPod environment setup
if [ "$RUNPOD_SETUP" = "true" ]; then
    echo "🔧 Setting up RunPod environment..."
    
    # Install system dependencies
    apt-get update -qq
    apt-get install -y git curl wget unzip
    
    # Install Python dependencies
    pip install --upgrade pip
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    pip install transformers datasets peft bitsandbytes accelerate
    pip install huggingface_hub wandb tensorboard
    
    echo "✅ RunPod environment ready"
fi

# Setup directories
mkdir -p $OUTPUT_DIR
mkdir -p $OUTPUT_DIR/logs
mkdir -p $OUTPUT_DIR/tensorboard

# Dataset preparation
echo "📊 Preparing dataset..."
python3 -c "
import json
import os
from datasets import Dataset, DatasetDict
import pandas as pd

dataset_path = '$DATASET_PATH'
output_path = '$OUTPUT_DIR/processed_dataset'

# Load annotations
with open(os.path.join(dataset_path, 'annotations.json'), 'r', encoding='utf-8') as f:
    annotations = json.load(f)

# Convert to training format
training_data = []
for item in annotations:
    if 'text' in item and 'entities' in item:
        # Create instruction-following format
        entities_text = ', '.join([f'{e[\"label\"]}: {e[\"text\"]}' for e in item['entities']])
        
        prompt = f'''Проанализируй юридический документ и извлеки сущности:

Документ: {item['text']}

Извлеченные сущности: {entities_text}

Дай юридический анализ и рекомендации:'''

        training_data.append({
            'instruction': prompt,
            'input': item['text'],
            'output': item.get('analysis', 'Юридический анализ документа.')
        })

# Create HuggingFace dataset
df = pd.DataFrame(training_data)
dataset = Dataset.from_pandas(df)

# Split train/validation
train_size = int(0.9 * len(dataset))
train_dataset = dataset.select(range(train_size))
val_dataset = dataset.select(range(train_size, len(dataset)))

dataset_dict = DatasetDict({
    'train': train_dataset,
    'validation': val_dataset
})

# Save dataset
dataset_dict.save_to_disk(output_path)
print(f'✅ Dataset prepared: {len(train_dataset)} train, {len(val_dataset)} validation samples')
"

# Model training with LoRA
echo "🧠 Starting LoRA fine-tuning..."

python3 -c "
import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    TrainingArguments, 
    Trainer,
    DataCollatorForSeq2Seq
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import load_from_disk
import wandb

# Configuration
model_name = 'mistralai/Mistral-7B-v0.1'
output_dir = '$OUTPUT_DIR'
dataset_path = f'{output_dir}/processed_dataset'

# Initialize wandb
wandb.init(project='legal-ai-training', name='mistral-7b-lora')

# Load model and tokenizer
print('📥 Loading model and tokenizer...')
tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map='auto',
    trust_remote_code=True
)

# LoRA configuration
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    inference_mode=False,
    r=16,  # LoRA attention dimension
    lora_alpha=32,  # LoRA scaling parameter
    lora_dropout=0.1,
    target_modules=['q_proj', 'v_proj', 'k_proj', 'o_proj']
)

# Apply LoRA
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# Load dataset
dataset = load_from_disk(dataset_path)

# Tokenization function
def preprocess_function(examples):
    inputs = [f'Инструкция: {inst}\nВход: {inp}\nОтвет: ' 
              for inst, inp in zip(examples['instruction'], examples['input'])]
    targets = examples['output']
    
    model_inputs = tokenizer(inputs, max_length=512, truncation=True, padding=True)
    labels = tokenizer(targets, max_length=256, truncation=True, padding=True)
    
    model_inputs['labels'] = labels['input_ids']
    return model_inputs

# Preprocess dataset
tokenized_dataset = dataset.map(preprocess_function, batched=True)

# Training arguments
training_args = TrainingArguments(
    output_dir=f'{output_dir}/checkpoints',
    num_train_epochs=3,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    gradient_accumulation_steps=4,
    warmup_steps=100,
    learning_rate=5e-5,
    fp16=True,
    logging_steps=10,
    evaluation_strategy='steps',
    eval_steps=100,
    save_steps=200,
    save_total_limit=3,
    remove_unused_columns=False,
    report_to='wandb',
    load_best_model_at_end=True,
    metric_for_best_model='eval_loss',
    greater_is_better=False
)

# Data collator
data_collator = DataCollatorForSeq2Seq(
    tokenizer=tokenizer,
    model=model,
    label_pad_token_id=-100,
    pad_to_multiple_of=8
)

# Initialize trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset['train'],
    eval_dataset=tokenized_dataset['validation'],
    data_collator=data_collator,
    tokenizer=tokenizer
)

# Start training
print('🚀 Starting training...')
trainer.train()

# Save final model
model.save_pretrained(f'{output_dir}/final_model')
tokenizer.save_pretrained(f'{output_dir}/final_model')

print('✅ Training completed!')
"

# Export model for inference
echo "📦 Exporting model for deployment..."
python3 -c "
from peft import PeftModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

output_dir = '$OUTPUT_DIR'
base_model_name = 'mistralai/Mistral-7B-v0.1'

# Load base model
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_name,
    torch_dtype=torch.float16,
    device_map='auto'
)

# Load LoRA weights
model = PeftModel.from_pretrained(base_model, f'{output_dir}/final_model')

# Merge and unload
merged_model = model.merge_and_unload()

# Save merged model
merged_model.save_pretrained(f'{output_dir}/merged_model')

# Save tokenizer
tokenizer = AutoTokenizer.from_pretrained(base_model_name)
tokenizer.save_pretrained(f'{output_dir}/merged_model')

print('✅ Merged model exported to {output_dir}/merged_model')
"

# Generate model card
echo "📋 Generating model card..."
cat > $OUTPUT_DIR/MODEL_CARD.md << EOF
# Legal AI Mistral-7B Fine-tuned Model

## Model Description
Fine-tuned Mistral-7B model for Russian legal document analysis and advisory.

## Training Details
- **Base Model**: mistralai/Mistral-7B-v0.1
- **Fine-tuning Method**: LoRA (Low-Rank Adaptation)
- **Dataset**: Legal AI Annotated Dataset v1
- **Training Date**: $(date)
- **GPU**: RunPod A10 24GB

## Usage
\`\`\`python
from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained("$OUTPUT_DIR/merged_model")
model = AutoModelForCausalLM.from_pretrained("$OUTPUT_DIR/merged_model")

prompt = "Проанализируй юридический документ: ..."
inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=256)
response = tokenizer.decode(outputs[0], skip_special_tokens=True)
\`\`\`

## Performance
- Training Loss: See TensorBoard logs
- Validation Loss: See TensorBoard logs
- Fine-tuning Parameters: $(echo 'import torch; from peft import PeftModel; print("LoRA parameters trained")' | python3)

## License
This model inherits the license from Mistral-7B-v0.1.
EOF

echo ""
echo "🎯 Training Pipeline Summary"
echo "==========================="
echo "✅ Dataset processed and prepared"
echo "✅ LoRA fine-tuning completed"
echo "✅ Model merged and exported"
echo "✅ Model card generated"
echo ""
echo "📁 Output files:"
echo "   - Merged model: $OUTPUT_DIR/merged_model/"
echo "   - Checkpoints: $OUTPUT_DIR/checkpoints/"
echo "   - Logs: $OUTPUT_DIR/logs/"
echo "   - Model card: $OUTPUT_DIR/MODEL_CARD.md"
echo ""
echo "🚀 Ready for deployment with deploy_gpu_inference.sh" 